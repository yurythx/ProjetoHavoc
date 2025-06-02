from django.core.management.base import BaseCommand
from apps.config.models import EmailConfig
from apps.config.email_utils import apply_email_settings_to_django


class Command(BaseCommand):
    help = 'Aplica as configurações de email ativas ao Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config-id',
            type=int,
            help='ID da configuração específica para aplicar',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Lista todas as configurações de email disponíveis',
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_email_configs()
            return

        config_id = options.get('config_id')
        
        if config_id:
            try:
                config = EmailConfig.objects.get(id=config_id)
                self.stdout.write(f'📧 Aplicando configuração específica: {config.name}')
            except EmailConfig.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Configuração com ID {config_id} não encontrada!')
                )
                return
        else:
            # Buscar configuração padrão
            config = EmailConfig.objects.filter(is_default=True, is_active=True).first()
            
            if not config:
                # Se não houver padrão, buscar qualquer ativa
                config = EmailConfig.objects.filter(is_active=True).first()
            
            if not config:
                self.stdout.write(
                    self.style.ERROR('❌ Nenhuma configuração de email ativa encontrada!')
                )
                return
            
            self.stdout.write(f'📧 Aplicando configuração padrão: {config.name}')

        # Aplicar configuração
        success = apply_email_settings_to_django(config)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('✅ Configurações de email aplicadas com sucesso!')
            )
            self.show_config_details(config)
        else:
            self.stdout.write(
                self.style.ERROR('❌ Erro ao aplicar configurações de email!')
            )

    def list_email_configs(self):
        """Lista todas as configurações de email"""
        configs = EmailConfig.objects.all().order_by('-is_default', '-is_active', 'name')
        
        if not configs:
            self.stdout.write('📧 Nenhuma configuração de email encontrada.')
            return
        
        self.stdout.write('📧 Configurações de Email Disponíveis:')
        self.stdout.write('')
        
        for config in configs:
            status_icons = []
            if config.is_default:
                status_icons.append('🌟 PADRÃO')
            if config.is_active:
                status_icons.append('✅ ATIVA')
            else:
                status_icons.append('❌ INATIVA')
            
            backend = '🖥️  CONSOLE' if config.use_console_backend else '📨 SMTP'
            status = ' | '.join(status_icons)
            
            self.stdout.write(f'   ID: {config.id} | Email Config')
            self.stdout.write(f'      Status: {status}')
            self.stdout.write(f'      Backend: {backend}')
            self.stdout.write(f'      Host: {config.email_host}:{config.email_port}')
            self.stdout.write(f'      From: {config.default_from_email}')
            self.stdout.write('')

    def show_config_details(self, config):
        """Mostra detalhes da configuração aplicada"""
        self.stdout.write('')
        self.stdout.write('📋 Detalhes da Configuração Aplicada:')
        self.stdout.write(f'   • ID: {config.id}')
        self.stdout.write(f'   • Backend: {"Console" if config.use_console_backend else "SMTP"}')
        self.stdout.write(f'   • Host: {config.email_host}')
        self.stdout.write(f'   • Porta: {config.email_port}')
        self.stdout.write(f'   • TLS: {"Sim" if config.email_use_tls else "Não"}')
        self.stdout.write(f'   • Usuário: {config.email_host_user or "Não configurado"}')
        self.stdout.write(f'   • Email padrão: {config.default_from_email}')
        self.stdout.write(f'   • Padrão: {"Sim" if config.is_default else "Não"}')
        self.stdout.write(f'   • Ativa: {"Sim" if config.is_active else "Não"}')
