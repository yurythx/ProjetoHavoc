from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import resolve, Resolver404
from django.template.response import TemplateResponse
from django.core.cache import cache
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class AppControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Ignorar admin, accounts, config e pages (páginas essenciais)
            if (request.path.startswith('/admin/') or
                request.path.startswith('/accounts/') or
                request.path.startswith('/config/') or
                request.path.startswith('/') and request.path == '/'):  # Rota raiz (home)
                return self.get_response(request)

            # Resolver a URL para obter o app
            resolver_match = resolve(request.path)
            app_name = resolver_match.app_name

            # Extrair o nome do app se estiver no formato 'apps.nome'
            if app_name and '.' in app_name:
                app_name = app_name.split('.')[-1]

            # Se não conseguir extrair o nome do app, pular verificação
            if not app_name:
                return self.get_response(request)

            # Verificar se o app está ativo usando cache
            cache_key = f'app_active_{app_name}'
            app_is_active = cache.get(cache_key)

            if app_is_active is None:
                # Verificar se as tabelas existem antes de fazer consultas
                try:
                    if not connection.ensure_connection():
                        return self.get_response(request)

                    table_names = connection.introspection.table_names()
                    if 'config_appconfig' not in table_names:
                        # Tabela não existe ainda, permitir acesso
                        return self.get_response(request)

                    from .models import AppConfig

                    try:
                        app_config = AppConfig.objects.get(label=app_name)
                        app_is_active = app_config.is_active
                        app_name_display = app_config.name

                        # Cachear resultado por 5 minutos
                        cache.set(cache_key, app_is_active, 300)
                        cache.set(f'app_name_{app_name}', app_name_display, 300)

                        if not app_is_active:
                            # Em vez de redirecionar, mostrar um template informativo
                            context = {
                                'module_name': app_name_display,
                                'module_label': app_name,
                                'user': request.user
                            }
                            return render(
                                request,
                                'config/module_disabled.html',
                                context
                            )
                    except AppConfig.DoesNotExist:
                        # Se o app não estiver registrado, permitir o acesso (para compatibilidade)
                        app_is_active = True
                        cache.set(cache_key, app_is_active, 300)

                except Exception as e:
                    logger.debug(f"Erro ao verificar status do app {app_name}: {e}")
                    # Em caso de erro, permitir acesso
                    return self.get_response(request)
            else:
                # Usar valor do cache
                if not app_is_active:
                    app_name_display = cache.get(f'app_name_{app_name}', app_name.capitalize())
                    context = {
                        'module_name': app_name_display,
                        'module_label': app_name,
                        'user': request.user
                    }
                    return render(
                        request,
                        'config/module_disabled.html',
                        context
                    )

        except Resolver404:
            # Se não conseguir resolver a URL, continuar normalmente
            pass
        except Exception as e:
            logger.debug(f"Erro no AppControlMiddleware: {e}")
            # Em caso de erro, continuar normalmente
            pass

        return self.get_response(request)
