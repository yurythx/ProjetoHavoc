from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ConfigConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.config'
    verbose_name = 'Configurações'

    def ready(self):
        # Importar signals para registrá-los
        from . import signals

        # Não aplicar configurações de email aqui para evitar consultas ao banco
        # durante a inicialização. As configurações serão aplicadas quando necessário
        logger.info("App Config inicializado - configurações serão carregadas sob demanda")
