from django.core.management.base import BaseCommand
from apps.config.signals import register_project_apps

class Command(BaseCommand):
    help = 'Registra os apps instalados no sistema'

    def handle(self, *args, **options):
        self.stdout.write('Registrando apps do projeto...')

        registered_count = register_project_apps()

        if registered_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'{registered_count} novos apps registrados com sucesso!')
            )
        else:
            self.stdout.write('Todos os apps já estão registrados.')

        # Mostrar estatísticas
        from apps.config.models import AppConfig
        total_apps = AppConfig.objects.count()
        active_apps = AppConfig.objects.filter(is_active=True).count()
        core_apps = AppConfig.objects.filter(is_core=True).count()

        self.stdout.write('')
        self.stdout.write('📊 Estatísticas:')
        self.stdout.write(f'   • Total de apps: {total_apps}')
        self.stdout.write(f'   • Apps ativos: {active_apps}')
        self.stdout.write(f'   • Apps core: {core_apps}')
