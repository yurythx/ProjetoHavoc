from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django.apps import apps as django_apps
from django.db.models.signals import post_migrate
from allauth.socialaccount.models import SocialApp
from .models import SocialProviderConfig, AppConfig

@receiver(post_save, sender=SocialProviderConfig)
def sync_social_provider_to_social_app(sender, instance, created, **kwargs):
    """Sincroniza as configurações do provedor social com o SocialApp do django-allauth."""
    site = Site.objects.get_current()

    try:
        social_app = SocialApp.objects.get(provider=instance.provider)
    except SocialApp.DoesNotExist:
        social_app = SocialApp(provider=instance.provider)

    social_app.name = instance.provider
    social_app.client_id = instance.client_id
    social_app.secret = instance.secret_key
    social_app.save()

    social_app.sites.add(site)

@receiver(post_delete, sender=SocialProviderConfig)
def delete_social_app(sender, instance, **kwargs):
    """Remove o SocialApp correspondente quando um provedor social é excluído."""
    try:
        social_app = SocialApp.objects.get(provider=instance.provider)
        social_app.delete()
    except SocialApp.DoesNotExist:
        pass

def register_project_apps():
    """
    Função utilitária para registrar apps do projeto.
    Centraliza a lógica de registro para evitar duplicação.
    """
    from django.apps import apps as django_apps

    # Apps core que não podem ser desativados
    core_apps = ['accounts', 'config', 'pages']
    registered_count = 0

    # Registrar apps do projeto
    for app_config in django_apps.get_app_configs():
        if app_config.name.startswith('apps.'):
            app_label = app_config.name.split('.')[-1]

            # Verificar se o app já está registrado
            app, created = AppConfig.objects.get_or_create(
                label=app_label,
                defaults={
                    'name': getattr(app_config, 'verbose_name', app_label.capitalize()),
                    'is_core': app_label in core_apps,
                    'is_active': True,
                    'description': f'Módulo {app_label.capitalize()} do sistema',
                }
            )

            if created:
                registered_count += 1

    return registered_count


@receiver(post_migrate)
def register_apps_after_migrate(sender, **kwargs):
    """
    Registra automaticamente os apps instalados após a migração.
    Isso garante que novos apps sejam registrados automaticamente.
    """
    # Evitar execução durante migrações de outros apps
    if sender.name != 'apps.config':
        return

    try:
        register_project_apps()

        # Criar configuração de email padrão se não existir
        from .models import EmailConfig

        if not EmailConfig.objects.filter(is_default=True).exists():
            EmailConfig.objects.create(
                email_host='localhost',
                email_port=25,
                email_host_user='',
                email_host_password='',
                email_use_tls=False,
                default_from_email='no-reply@localhost',
                is_default=True,
                is_active=True,
                use_console_backend=True  # Usar console por padrão para desenvolvimento
            )
            print("✅ Configuração de email padrão criada")

    except Exception as e:
        # Ignorar erros durante migrações
        pass