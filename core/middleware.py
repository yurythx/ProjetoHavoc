"""
Middleware unificado para o Projeto Havoc
Consolida funcionalidades de segurança, performance e auditoria
"""

import time
import logging
import re
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.http import Http404, HttpResponse
from django.core.cache import cache

logger = logging.getLogger(__name__)
security_logger = logging.getLogger('django.security')


class UnifiedSecurityMiddleware(MiddlewareMixin):
    """
    Middleware unificado para segurança, performance e auditoria
    """
    
    # URLs de desenvolvimento bloqueadas em produção
    DEVELOPMENT_URLS = [
        '/accounts/test/',
        '/config/module-disabled-test/',
        '/admin/doc/',
        '/debug/',
    ]
    
    # URLs que requerem autenticação especial
    RESTRICTED_URLS = [
        '/accounts/ldap/',
        '/config/',
    ]
    
    # User agents suspeitos
    SUSPICIOUS_AGENTS = [
        'sqlmap', 'nikto', 'nmap', 'masscan', 'burp', 'owasp',
        'dirbuster', 'gobuster', 'wfuzz', 'hydra'
    ]
    
    # Padrões de ameaças
    THREAT_PATTERNS = {
        'sql_injection': [
            r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
            r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%23)|(#))",
            r"union.*select",
            r"exec(\s|\+)+(s|x)p\w+"
        ],
        'xss': [
            r"<script[^>]*>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
        ],
        'directory_traversal': [
            r"\.\.[\\/]",
            r"\.\.%2f",
            r"%2e%2e%2f",
        ]
    }
    
    def process_request(self, request):
        """Processar requisição com todas as verificações de segurança"""
        
        # Armazenar informações para auditoria
        request._audit_ip = self.get_client_ip(request)
        request._audit_user_agent = request.META.get('HTTP_USER_AGENT', '')
        request._performance_start_time = time.time()
        
        # 1. Verificar rate limiting
        if self._check_rate_limit(request):
            return HttpResponse('Rate limit excedido. Tente novamente em alguns minutos.', status=429)
        
        # 2. Bloquear URLs de desenvolvimento em produção
        if not settings.DEBUG:
            for dev_url in self.DEVELOPMENT_URLS:
                if request.path.startswith(dev_url):
                    security_logger.warning(
                        f'Tentativa de acesso a URL de desenvolvimento: {request.path} por {request._audit_ip}'
                    )
                    raise Http404("Página não encontrada")
        
        # 3. Verificar URLs restritas (temporariamente desabilitado para teste)
        # for restricted_url in self.RESTRICTED_URLS:
        #     if request.path.startswith(restricted_url):
        #         if not self._is_authorized_for_restricted_url(request, restricted_url):
        #             security_logger.warning(
        #                 f'Acesso não autorizado: {request.path} por {request._audit_ip}'
        #             )
        #             messages.error(request, 'Acesso negado. Você precisa ser um usuário staff para acessar esta área.')
        #             return redirect('pages:home')
        
        # 4. Detectar ameaças
        self._detect_threats(request)
        
        # 5. Verificar headers suspeitos
        if self._has_suspicious_headers(request):
            security_logger.warning(
                f'Headers suspeitos de {request._audit_ip}: {request._audit_user_agent}'
            )
        
        # 6. Verificar sessão de segurança
        return self._check_session_security(request)
    
    def process_response(self, request, response):
        """Processar resposta com headers de segurança e métricas"""
        
        # Adicionar headers de segurança
        self._add_security_headers(response)
        
        # Adicionar headers anti-cache para páginas protegidas
        if hasattr(request, 'user') and request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        # Log de performance
        if hasattr(request, '_performance_start_time'):
            request_time = time.time() - request._performance_start_time
            if request_time > 2.0:  # Log requests lentos
                logger.warning(
                    f'Slow request: {request.path} took {request_time:.3f}s '
                    f'for {request._audit_ip}'
                )
        
        return response
    
    def get_client_ip(self, request):
        """Obtém o IP real do cliente (método unificado)"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _check_rate_limit(self, request):
        """Verificar rate limiting"""
        ip = request._audit_ip

        # Diferentes limites para diferentes tipos de usuário
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                # Staff/Admin: 1000 requests por minuto
                limit = 1000
                timeout = 60
            else:
                # Usuários normais: 300 requests por minuto
                limit = 300
                timeout = 60
        else:
            # Usuários anônimos: 100 requests por minuto
            limit = 100
            timeout = 60

        cache_key = f'rate_limit:{ip}'
        current_requests = cache.get(cache_key, 0)

        if current_requests >= limit:
            return True

        cache.set(cache_key, current_requests + 1, timeout)
        return False
    
    def _is_authorized_for_restricted_url(self, request, url):
        """Verificar autorização para URL restrita"""
        if url.startswith('/config/'):
            return request.user.is_authenticated and request.user.is_staff
        if url.startswith('/accounts/ldap/'):
            return True
        return False
    
    def _detect_threats(self, request):
        """Detectar padrões de ameaças na requisição"""
        query_string = request.META.get('QUERY_STRING', '')
        path = request.path
        user_agent = request._audit_user_agent.lower()
        
        # Verificar padrões de ameaças
        for threat_type, patterns in self.THREAT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_string, re.IGNORECASE) or re.search(pattern, path, re.IGNORECASE):
                    security_logger.critical(
                        f'THREAT DETECTED: {threat_type} from {request._audit_ip} '
                        f'Pattern: {pattern} URL: {request.get_full_path()}'
                    )
                    break
    
    def _has_suspicious_headers(self, request):
        """Detectar headers suspeitos"""
        user_agent = request._audit_user_agent.lower()
        
        # Verificar user agents suspeitos
        for agent in self.SUSPICIOUS_AGENTS:
            if agent in user_agent:
                return True
        
        # Verificar headers de injeção
        suspicious_headers = ['HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP', 'HTTP_CLIENT_IP']
        for header in suspicious_headers:
            value = request.META.get(header, '')
            if any(char in value for char in ['<', '>', '"', "'", 'script', 'javascript']):
                return True
        
        return False
    
    def _check_session_security(self, request):
        """Verificar segurança da sessão"""
        if not request.user.is_authenticated and request.COOKIES.get(settings.SESSION_COOKIE_NAME):
            protected_urls = [
                '/accounts/profile', '/accounts/admin', '/accounts/password_change',
                '/config/', '/articles/create', '/articles/edit', '/articles/delete'
            ]
            
            for protected_url in protected_urls:
                if request.path.startswith(protected_url):
                    messages.warning(
                        request,
                        '🔒 Sua sessão expirou por segurança. Faça login novamente.'
                    )
                    return redirect('accounts:login')
        
        return None
    
    def _add_security_headers(self, response):
        """Adicionar headers de segurança"""
        # Headers básicos sempre
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Headers avançados apenas em produção
        if not settings.DEBUG:
            response['X-Frame-Options'] = 'DENY'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            # CSP básico
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
            
            # Permissions Policy
            response['Permissions-Policy'] = (
                'geolocation=(), microphone=(), camera=(), payment=(), '
                'usb=(), magnetometer=(), gyroscope=(), speaker=()'
            )


def audit_user_action(user, action, request=None, **details):
    """
    Função utilitária unificada para registrar ações de auditoria
    """
    try:
        from apps.accounts.models import UserAuditLog
        
        ip_address = None
        user_agent = ''
        
        if request:
            ip_address = getattr(request, '_audit_ip', None)
            user_agent = getattr(request, '_audit_user_agent', '')
        
        UserAuditLog.log_action(
            user=user,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            **details
        )
        
    except Exception as e:
        logger.error(f'Erro ao registrar ação de auditoria: {e}')


def log_security_event(event_type, details, request=None):
    """
    Função utilitária unificada para registrar eventos de segurança
    """
    ip = 'unknown'
    user_agent = 'unknown'
    user = 'anonymous'
    
    if request:
        ip = getattr(request, '_audit_ip', 'unknown')
        user_agent = getattr(request, '_audit_user_agent', 'unknown')
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user.username
    
    security_logger.warning(
        f'SECURITY EVENT: {event_type} | User: {user} | IP: {ip} | '
        f'Details: {details} | User-Agent: {user_agent[:100]}'
    )
