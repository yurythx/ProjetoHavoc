"""
Context processors para disponibilizar configurações globalmente nos templates.
"""

from django.core.cache import cache
from django.db import connection
import logging

logger = logging.getLogger(__name__)

def _get_default_config():
    """Retorna configuração padrão do sistema"""
    return {
        'site_name': 'Projeto Havoc',
        'site_description': 'Sistema Modular',
        'maintenance_mode': False,
        'allow_registration': True,
        'require_email_verification': True,
        'enable_app_management': True,
        'logo_url': None,
        'favicon_url': None,
        'has_custom_branding': False,
        # Configurações de tema padrão
        'theme': 'default',
        'primary_color': '#4361ee',
        'secondary_color': '#6c757d',
        'accent_color': '#4cc9f0',
        'sidebar_style': 'fixed',
        'header_style': 'fixed',
        # Funcionalidades padrão
        'enable_dark_mode_toggle': True,
        'enable_breadcrumbs': True,
        'enable_search': True,
        'enable_notifications': True,
        'notification_position': 'top-right',
        # SEO padrão
        'meta_keywords': '',
        'meta_author': '',
        'google_analytics_id': '',
    }

def system_config(request):
    """
    Context processor que disponibiliza as configurações do sistema
    em todos os templates.
    """
    # Tentar obter do cache primeiro
    config = cache.get('system_config')

    if config is None:
        # Verificar se as tabelas existem antes de fazer consultas
        try:
            # Verificar se a conexão com o banco está disponível
            if not connection.ensure_connection():
                return {'system_config': _get_default_config()}

            # Verificar se a tabela existe
            table_names = connection.introspection.table_names()
            if 'config_systemconfig' not in table_names:
                logger.debug("Tabela config_systemconfig não existe ainda - usando configuração padrão")
                return {'system_config': _get_default_config()}

            # Importar modelo apenas quando necessário
            from .models import SystemConfig

            # Obter a primeira configuração do sistema
            config = SystemConfig.objects.first()

            if config:
                # Criar dicionário com as configurações
                config_data = {
                    'site_name': config.site_name,
                    'site_description': config.site_description,
                    'maintenance_mode': config.maintenance_mode,
                    'allow_registration': config.allow_registration,
                    'require_email_verification': config.require_email_verification,
                    'enable_app_management': config.enable_app_management,
                    'logo_url': config.get_logo_url(),
                    'favicon_url': config.get_favicon_url(),
                    'has_custom_branding': config.has_custom_branding(),
                    # Configurações de tema
                    'theme': config.theme,
                    'primary_color': config.primary_color,
                    'secondary_color': config.secondary_color,
                    'accent_color': config.accent_color,
                    'sidebar_style': config.sidebar_style,
                    'header_style': config.header_style,
                    # Funcionalidades
                    'enable_dark_mode_toggle': config.enable_dark_mode_toggle,
                    'enable_breadcrumbs': config.enable_breadcrumbs,
                    'enable_search': config.enable_search,
                    'enable_notifications': config.enable_notifications,
                    'notification_position': config.notification_position,
                    # SEO
                    'meta_keywords': config.meta_keywords,
                    'meta_author': config.meta_author,
                    'google_analytics_id': config.google_analytics_id,
                }

                # Cachear por 5 minutos
                cache.set('system_config', config_data, 300)
                config = config_data
            else:
                # Configuração padrão se não existir
                config = _get_default_config()
                # Cachear configuração padrão por 1 minuto
                cache.set('system_config', config, 60)

        except Exception as e:
            # Em caso de erro, usar configuração padrão
            logger.debug(f"Erro ao carregar configurações do sistema: {e}")
            config = _get_default_config()

    return {
        'system_config': config
    }

def clear_system_config_cache():
    """
    Função utilitária para limpar o cache das configurações do sistema.
    Deve ser chamada sempre que as configurações forem alteradas.
    """
    cache.delete('system_config')
