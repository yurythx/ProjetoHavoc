"""
Middleware para aplicar configurações de email automaticamente
"""

from django.core.cache import cache
from .email_utils import auto_apply_email_settings
import logging

logger = logging.getLogger(__name__)


class EmailConfigMiddleware:
    """
    Middleware que aplica configurações de email na primeira requisição
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar se as configurações já foram aplicadas
        if not cache.get('email_config_applied'):
            try:
                # Tentar aplicar configurações de email
                if auto_apply_email_settings():
                    # Marcar como aplicado por 1 hora
                    cache.set('email_config_applied', True, 3600)
                    logger.info("Configurações de email aplicadas via middleware")
            except Exception as e:
                logger.debug(f"Erro ao aplicar configurações de email via middleware: {e}")

        response = self.get_response(request)
        return response
