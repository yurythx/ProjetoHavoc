from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Middleware para garantir segurança de sessão e prevenir acesso a páginas protegidas
    após logout usando o botão voltar do navegador.
    """

    def process_response(self, request, response):
        # Adicionar cabeçalhos de segurança para todas as respostas
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'

        # Para páginas que requerem autenticação, adicionar cabeçalhos anti-cache
        if request.user.is_authenticated:
            # Adicionar cabeçalhos para prevenir cache em páginas protegidas
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response

    def process_request(self, request):
        # Verificar se a sessão expirou para usuários que têm cookie de sessão
        # mas a sessão foi invalidada no servidor
        if not request.user.is_authenticated and request.COOKIES.get(settings.SESSION_COOKIE_NAME):
            # Lista de prefixos de URLs protegidas
            protected_urls = [
                '/accounts/profile',
                '/accounts/admin',
                '/accounts/password_change',
                '/config/',
                '/articles/create',
                '/articles/edit',
                '/articles/delete',
            ]

            # Verificar se estamos tentando acessar uma página protegida
            for protected_url in protected_urls:
                if request.path.startswith(protected_url):
                    messages.warning(
                        request,
                        '🔒 Sua sessão expirou por segurança. Por favor, faça login novamente para acessar esta página.'
                    )
                    return redirect('accounts:login')

        return None


class UserAuditMiddleware(MiddlewareMixin):
    """
    Middleware para registrar ações de auditoria dos usuários
    """

    def process_request(self, request):
        # Armazenar informações da requisição para uso posterior
        request._audit_ip = self.get_client_ip(request)
        request._audit_user_agent = request.META.get('HTTP_USER_AGENT', '')
        return None

    def get_client_ip(self, request):
        """Obtém o IP real do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware para verificações de segurança
    """

    def process_request(self, request):
        # Verificar se o usuário está bloqueado
        if request.user.is_authenticated:
            if hasattr(request.user, 'esta_bloqueado') and request.user.esta_bloqueado():
                from django.contrib.auth import logout

                logout(request)
                messages.error(
                    request,
                    'Sua conta foi temporariamente bloqueada por questões de segurança. '
                    'Tente novamente mais tarde ou entre em contato com o administrador.'
                )
                return redirect('accounts:login')

        return None


# Signals para auditoria
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Registra login bem-sucedido"""
    try:
        from .models import UserAuditLog

        # Atualizar informações de segurança do usuário
        if hasattr(user, 'registrar_login_sucesso'):
            ip = getattr(request, '_audit_ip', None)
            user.registrar_login_sucesso(ip)

        # Registrar no log de auditoria
        UserAuditLog.log_action(
            user=user,
            action='login',
            ip_address=getattr(request, '_audit_ip', None),
            user_agent=getattr(request, '_audit_user_agent', ''),
            login_method='web'
        )

        logger.info(f'Login bem-sucedido: {user.username} de {getattr(request, "_audit_ip", "IP desconhecido")}')

    except Exception as e:
        logger.error(f'Erro ao registrar login: {e}')


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Registra logout"""
    try:
        from .models import UserAuditLog

        if user:
            UserAuditLog.log_action(
                user=user,
                action='logout',
                ip_address=getattr(request, '_audit_ip', None),
                user_agent=getattr(request, '_audit_user_agent', ''),
            )

            logger.info(f'Logout: {user.username} de {getattr(request, "_audit_ip", "IP desconhecido")}')

    except Exception as e:
        logger.error(f'Erro ao registrar logout: {e}')


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Registra tentativa de login falhada"""
    try:
        from .models import UserAuditLog
        from django.contrib.auth import get_user_model

        username = credentials.get('username', 'Desconhecido')
        ip = getattr(request, '_audit_ip', None)
        User = get_user_model()

        try:
            user = User.objects.get(username=username)

            # Registrar tentativa falhada no usuário
            if hasattr(user, 'registrar_tentativa_login_falhada'):
                user.registrar_tentativa_login_falhada(ip)

            # Registrar no log de auditoria
            UserAuditLog.log_action(
                user=user,
                action='login_failed',
                ip_address=ip,
                user_agent=getattr(request, '_audit_user_agent', ''),
                attempted_username=username
            )

        except User.DoesNotExist:
            # Usuário não existe, mas ainda registramos a tentativa
            logger.warning(f'Tentativa de login com usuário inexistente: {username} de {ip}')

        logger.warning(f'Login falhado: {username} de {ip}')

    except Exception as e:
        logger.error(f'Erro ao registrar login falhado: {e}')


def audit_user_action(user, action, request=None, **details):
    """
    Função utilitária para registrar ações de auditoria
    """
    try:
        from .models import UserAuditLog

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
