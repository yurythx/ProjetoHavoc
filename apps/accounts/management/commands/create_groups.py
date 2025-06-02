from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Cria os grupos básicos do sistema'

    def handle(self, *args, **options):
        # Grupos básicos do sistema
        groups = [
            {
                'name': 'Usuario',
                'description': 'Grupo padrão para usuários comuns do sistema'
            },
            {
                'name': 'Administrador',
                'description': 'Grupo para administradores do sistema'
            }
        ]

        created_count = 0
        
        for group_data in groups:
            group, created = Group.objects.get_or_create(
                name=group_data['name']
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Grupo "{group.name}" criado com sucesso!'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Grupo "{group.name}" já existe.'
                    )
                )

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n{created_count} grupo(s) criado(s) com sucesso!'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '\nTodos os grupos básicos já existem no sistema.'
                )
            )
