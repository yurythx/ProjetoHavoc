from django.core.management.base import BaseCommand
from django.core.cache import cache
from apps.config.models import EmailConfig, SystemConfig
from apps.config.signals import register_project_apps


class Command(BaseCommand):
    help = 'Configura as configurações padrão do sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a recriação das configurações mesmo se já existirem',
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Configurando sistema Projeto Havoc...')
        
        # Registrar apps
        self.stdout.write('📦 Registrando apps do projeto...')
        registered_count = register_project_apps()
        
        if registered_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✅ {registered_count} novos apps registrados!')
            )
        else:
            self.stdout.write('ℹ️  Todos os apps já estão registrados.')

        # Configurar email padrão
        self.stdout.write('📧 Configurando email padrão...')
        email_created = self.setup_default_email(options['force'])
        
        if email_created:
            self.stdout.write(
                self.style.SUCCESS('✅ Configuração de email padrão criada!')
            )
        else:
            self.stdout.write('ℹ️  Configuração de email já existe.')

        # Configurar sistema padrão
        self.stdout.write('⚙️  Configurando sistema padrão...')
        system_created = self.setup_default_system(options['force'])
        
        if system_created:
            self.stdout.write(
                self.style.SUCCESS('✅ Configuração de sistema padrão criada!')
            )
        else:
            self.stdout.write('ℹ️  Configuração de sistema já existe.')

        # Limpar cache
        self.stdout.write('🧹 Limpando cache...')
        cache.clear()
        self.stdout.write(self.style.SUCCESS('✅ Cache limpo!'))

        # Mostrar estatísticas finais
        self.show_statistics()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎉 Sistema configurado com sucesso!'))
        self.stdout.write('💡 Execute "python manage.py runserver" para iniciar o servidor.')

    def setup_default_email(self, force=False):
        """Configura email padrão"""
        if force:
            EmailConfig.objects.filter(is_default=True).delete()

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
                use_console_backend=True  # Console para desenvolvimento
            )
            return True
        return False

    def setup_default_system(self, force=False):
        """Configura sistema padrão"""
        if force:
            SystemConfig.objects.all().delete()
        
        if not SystemConfig.objects.exists():
            SystemConfig.objects.create(
                site_name='Projeto Havoc',
                site_description='Sistema de Gerenciamento Modular',
                maintenance_mode=False,
                allow_registration=True,
                require_email_verification=True,
                enable_app_management=True,
                theme='default',
                primary_color='#4361ee',
                secondary_color='#6c757d',
                accent_color='#4cc9f0',
                sidebar_style='fixed',
                header_style='fixed',
                enable_dark_mode_toggle=True,
                enable_breadcrumbs=True,
                enable_search=True,
                enable_notifications=True,
                notification_position='top-right'
            )
            return True
        return False

    def show_statistics(self):
        """Mostra estatísticas do sistema"""
        from apps.config.models import AppConfig
        
        total_apps = AppConfig.objects.count()
        active_apps = AppConfig.objects.filter(is_active=True).count()
        core_apps = AppConfig.objects.filter(is_core=True).count()
        
        email_configs = EmailConfig.objects.count()
        system_configs = SystemConfig.objects.count()

        self.stdout.write('')
        self.stdout.write('📊 Estatísticas do Sistema:')
        self.stdout.write(f'   • Apps registrados: {total_apps}')
        self.stdout.write(f'   • Apps ativos: {active_apps}')
        self.stdout.write(f'   • Apps core: {core_apps}')
        self.stdout.write(f'   • Configurações de email: {email_configs}')
        self.stdout.write(f'   • Configurações de sistema: {system_configs}')
