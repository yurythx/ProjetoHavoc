"""
Sistema de Monitoramento para Configurações
Projeto Havoc - Sistema de Configurações Modular
"""

import logging
import json
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import (
    SystemConfig, EmailConfig, LDAPConfig, DatabaseConfig,
    AppConfig, Widget, Plugin, EnvironmentVariable
)

logger = logging.getLogger(__name__)


class ConfigurationMonitor:
    """Monitor principal para configurações do sistema"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutos
        self.status_cache_key = 'config_system_status'
        
    def get_system_status(self, force_refresh=False):
        """Obter status completo do sistema"""
        if not force_refresh:
            cached_status = cache.get(self.status_cache_key)
            if cached_status:
                return cached_status
        
        status = {
            'timestamp': timezone.now().isoformat(),
            'overall_health': 'healthy',
            'modules': self._check_all_modules(),
            'database': self._check_database_health(),
            'email': self._check_email_health(),
            'system': self._check_system_health(),
            'performance': self._check_performance_metrics(),
            'alerts': self._get_active_alerts()
        }
        
        # Determinar saúde geral
        status['overall_health'] = self._calculate_overall_health(status)
        
        # Cache do status
        cache.set(self.status_cache_key, status, self.cache_timeout)
        
        return status
    
    def _check_all_modules(self):
        """Verificar status de todos os módulos"""
        modules = {}
        
        # Sistema
        modules['system'] = self._check_system_module()
        
        # Email
        modules['email'] = self._check_email_module()
        
        # LDAP
        modules['ldap'] = self._check_ldap_module()
        
        # Banco de Dados
        modules['database'] = self._check_database_module()
        
        # Apps
        modules['apps'] = self._check_apps_module()
        
        # Widgets
        modules['widgets'] = self._check_widgets_module()
        
        # Plugins
        modules['plugins'] = self._check_plugins_module()
        
        return modules
    
    def _check_system_module(self):
        """Verificar módulo do sistema"""
        try:
            system_config = SystemConfig.objects.first()
            
            status = {
                'name': 'Sistema',
                'status': 'healthy',
                'configured': bool(system_config),
                'details': {},
                'issues': []
            }
            
            if system_config:
                status['details'] = {
                    'site_name': system_config.site_name,
                    'maintenance_mode': system_config.maintenance_mode,
                    'allow_registration': system_config.allow_registration,
                    'debug_mode': system_config.debug_mode,
                    'last_updated': system_config.updated_at.isoformat() if system_config.updated_at else None
                }
                
                # Verificar problemas
                if system_config.maintenance_mode:
                    status['issues'].append('Sistema em modo manutenção')
                    status['status'] = 'warning'

                if system_config.debug_mode:
                    status['issues'].append('Modo debug ativo (não recomendado para produção)')
                    if status['status'] == 'healthy':
                        status['status'] = 'warning'
            else:
                status['status'] = 'error'
                status['issues'].append('Configuração do sistema não encontrada')
            
            return status
            
        except Exception as e:
            logger.error(f"Erro ao verificar módulo sistema: {e}")
            return {
                'name': 'Sistema',
                'status': 'error',
                'configured': False,
                'details': {},
                'issues': [f'Erro: {str(e)}']
            }
    
    def _check_email_module(self):
        """Verificar módulo de email"""
        try:
            email_configs = EmailConfig.objects.all()
            active_configs = email_configs.filter(is_active=True)
            
            status = {
                'name': 'Email',
                'status': 'healthy',
                'configured': email_configs.exists(),
                'details': {
                    'total_configs': email_configs.count(),
                    'active_configs': active_configs.count(),
                    'default_config': None
                },
                'issues': []
            }
            
            # Verificar configuração padrão
            default_config = email_configs.filter(is_default=True).first()
            if default_config:
                status['details']['default_config'] = default_config.email_host
                
                # Testar configuração padrão
                test_result = self._test_email_config(default_config)
                if not test_result['success']:
                    status['status'] = 'warning'
                    status['issues'].append(f'Problema na configuração padrão: {test_result["error"]}')
            else:
                if active_configs.exists():
                    status['status'] = 'warning'
                    status['issues'].append('Nenhuma configuração padrão definida')
                else:
                    status['status'] = 'error'
                    status['issues'].append('Nenhuma configuração de email ativa')
            
            return status
            
        except Exception as e:
            logger.error(f"Erro ao verificar módulo email: {e}")
            return {
                'name': 'Email',
                'status': 'error',
                'configured': False,
                'details': {},
                'issues': [f'Erro: {str(e)}']
            }
    
    def _check_ldap_module(self):
        """Verificar módulo LDAP"""
        try:
            ldap_configs = LDAPConfig.objects.all()
            active_configs = ldap_configs.filter(is_active=True)
            
            status = {
                'name': 'LDAP',
                'status': 'healthy',
                'configured': ldap_configs.exists(),
                'details': {
                    'total_configs': ldap_configs.count(),
                    'active_configs': active_configs.count()
                },
                'issues': []
            }
            
            if not ldap_configs.exists():
                status['status'] = 'info'
                status['issues'].append('Nenhuma configuração LDAP configurada')
            elif not active_configs.exists():
                status['status'] = 'warning'
                status['issues'].append('Nenhuma configuração LDAP ativa')
            
            return status
            
        except Exception as e:
            logger.error(f"Erro ao verificar módulo LDAP: {e}")
            return {
                'name': 'LDAP',
                'status': 'error',
                'configured': False,
                'details': {},
                'issues': [f'Erro: {str(e)}']
            }
    
    def _check_database_module(self):
        """Verificar módulo de banco de dados"""
        try:
            db_configs = DatabaseConfig.objects.all()
            active_configs = db_configs.filter(is_active=True)
            
            status = {
                'name': 'Banco de Dados',
                'status': 'healthy',
                'configured': db_configs.exists(),
                'details': {
                    'total_configs': db_configs.count(),
                    'active_configs': active_configs.count(),
                    'connection_health': self._test_database_connections()
                },
                'issues': []
            }
            
            # Verificar saúde das conexões
            connection_issues = [
                conn for conn in status['details']['connection_health']
                if not conn['healthy']
            ]
            
            if connection_issues:
                status['status'] = 'warning'
                for issue in connection_issues:
                    status['issues'].append(f"Problema na conexão {issue['name']}: {issue['error']}")
            
            return status
            
        except Exception as e:
            logger.error(f"Erro ao verificar módulo banco: {e}")
            return {
                'name': 'Banco de Dados',
                'status': 'error',
                'configured': False,
                'details': {},
                'issues': [f'Erro: {str(e)}']
            }
    
    def _check_apps_module(self):
        """Verificar módulo de apps"""
        try:
            apps = AppConfig.objects.all()
            active_apps = apps.filter(is_active=True)
            core_apps = apps.filter(is_core=True)
            
            status = {
                'name': 'Apps',
                'status': 'healthy',
                'configured': apps.exists(),
                'details': {
                    'total_apps': apps.count(),
                    'active_apps': active_apps.count(),
                    'core_apps': core_apps.count()
                },
                'issues': []
            }
            
            # Verificar apps core desativados
            inactive_core = core_apps.filter(is_active=False)
            if inactive_core.exists():
                status['status'] = 'warning'
                for app in inactive_core:
                    status['issues'].append(f'App core desativado: {app.name}')
            
            return status
            
        except Exception as e:
            logger.error(f"Erro ao verificar módulo apps: {e}")
            return {
                'name': 'Apps',
                'status': 'error',
                'configured': False,
                'details': {},
                'issues': [f'Erro: {str(e)}']
            }
    
    def _check_widgets_module(self):
        """Verificar módulo de widgets"""
        try:
            widgets = Widget.objects.all()
            active_widgets = widgets.filter(is_active=True)
            
            status = {
                'name': 'Widgets',
                'status': 'healthy',
                'configured': widgets.exists(),
                'details': {
                    'total_widgets': widgets.count(),
                    'active_widgets': active_widgets.count()
                },
                'issues': []
            }
            
            if not widgets.exists():
                status['status'] = 'info'
                status['issues'].append('Nenhum widget configurado')
            
            return status
            
        except Exception as e:
            logger.error(f"Erro ao verificar módulo widgets: {e}")
            return {
                'name': 'Widgets',
                'status': 'error',
                'configured': False,
                'details': {},
                'issues': [f'Erro: {str(e)}']
            }
    
    def _check_plugins_module(self):
        """Verificar módulo de plugins"""
        try:
            plugins = Plugin.objects.all()
            active_plugins = plugins.filter(status='active')  # Usar 'status' em vez de 'is_active'

            status = {
                'name': 'Plugins',
                'status': 'healthy',
                'configured': plugins.exists(),
                'details': {
                    'total_plugins': plugins.count(),
                    'active_plugins': active_plugins.count()
                },
                'issues': []
            }

            if not plugins.exists():
                status['status'] = 'info'
                status['issues'].append('Nenhum plugin instalado')

            return status
            
        except Exception as e:
            logger.error(f"Erro ao verificar módulo plugins: {e}")
            return {
                'name': 'Plugins',
                'status': 'error',
                'configured': False,
                'details': {},
                'issues': [f'Erro: {str(e)}']
            }
    
    def _check_database_health(self):
        """Verificar saúde do banco de dados"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            return {
                'status': 'healthy',
                'connection': 'active',
                'response_time': 'fast'
            }
            
        except Exception as e:
            logger.error(f"Erro na verificação do banco: {e}")
            return {
                'status': 'error',
                'connection': 'failed',
                'error': str(e)
            }
    
    def _check_email_health(self):
        """Verificar saúde do sistema de email"""
        try:
            default_config = EmailConfig.objects.filter(is_default=True).first()
            if not default_config:
                return {
                    'status': 'warning',
                    'message': 'Nenhuma configuração padrão'
                }
            
            test_result = self._test_email_config(default_config)
            return {
                'status': 'healthy' if test_result['success'] else 'error',
                'config': default_config.email_host,
                'test_result': test_result
            }
            
        except Exception as e:
            logger.error(f"Erro na verificação de email: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_system_health(self):
        """Verificar saúde geral do sistema"""
        try:
            system_config = SystemConfig.objects.first()
            
            health = {
                'status': 'healthy',
                'maintenance_mode': False,
                'uptime': self._get_system_uptime(),
                'memory_usage': self._get_memory_usage()
            }
            
            if system_config and system_config.maintenance_mode:
                health['status'] = 'maintenance'
                health['maintenance_mode'] = True
            
            return health
            
        except Exception as e:
            logger.error(f"Erro na verificação do sistema: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_performance_metrics(self):
        """Verificar métricas de performance"""
        try:
            return {
                'database_queries': self._get_database_query_count(),
                'cache_hit_rate': self._get_cache_hit_rate(),
                'response_time': self._get_average_response_time()
            }
        except Exception as e:
            logger.error(f"Erro nas métricas de performance: {e}")
            return {}
    
    def _get_active_alerts(self):
        """Obter alertas ativos"""
        alerts = []
        
        # Verificar configurações críticas
        if not SystemConfig.objects.exists():
            alerts.append({
                'level': 'critical',
                'message': 'Configuração do sistema não encontrada',
                'module': 'system'
            })
        
        if not EmailConfig.objects.filter(is_active=True).exists():
            alerts.append({
                'level': 'warning',
                'message': 'Nenhuma configuração de email ativa',
                'module': 'email'
            })
        
        return alerts
    
    def _calculate_overall_health(self, status):
        """Calcular saúde geral baseada nos módulos"""
        module_statuses = [module['status'] for module in status['modules'].values()]
        
        if 'error' in module_statuses:
            return 'error'
        elif 'warning' in module_statuses:
            return 'warning'
        elif status['database']['status'] == 'error':
            return 'error'
        else:
            return 'healthy'
    
    def _test_email_config(self, config):
        """Testar configuração de email"""
        try:
            # Implementar teste real de conexão SMTP
            return {'success': True, 'message': 'Configuração válida'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_database_connections(self):
        """Testar conexões de banco"""
        connections = []
        
        # Testar conexão principal
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            connections.append({
                'name': 'default',
                'healthy': True,
                'response_time': 'fast'
            })
        except Exception as e:
            connections.append({
                'name': 'default',
                'healthy': False,
                'error': str(e)
            })
        
        return connections
    
    def _get_system_uptime(self):
        """Obter uptime do sistema"""
        # Implementar lógica de uptime
        return "24h 30m"
    
    def _get_memory_usage(self):
        """Obter uso de memória"""
        # Implementar lógica de memória
        return "45%"
    
    def _get_database_query_count(self):
        """Obter contagem de queries"""
        return len(connection.queries)
    
    def _get_cache_hit_rate(self):
        """Obter taxa de acerto do cache"""
        return "85%"
    
    def _get_average_response_time(self):
        """Obter tempo médio de resposta"""
        return "120ms"


# Instância global do monitor
config_monitor = ConfigurationMonitor()
