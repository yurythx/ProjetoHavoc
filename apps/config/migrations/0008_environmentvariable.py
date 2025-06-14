# Generated by Django 5.2.1 on 2025-05-25 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0007_appconfig_dependencies'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnvironmentVariable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(help_text='Nome da variável (ex: DEBUG)', max_length=100, unique=True)),
                ('value', models.TextField(blank=True, help_text='Valor da variável')),
                ('default_value', models.TextField(blank=True, help_text='Valor padrão')),
                ('description', models.TextField(help_text='Descrição da variável')),
                ('category', models.CharField(choices=[('core', 'Django Core'), ('database', 'Database'), ('email', 'Email'), ('security', 'Security'), ('site', 'Site'), ('static', 'Static & Media'), ('cache', 'Cache'), ('logging', 'Logging'), ('auth', 'Authentication'), ('ldap', 'LDAP'), ('social', 'Social Auth'), ('services', 'Third-party Services'), ('api', 'API Keys'), ('development', 'Development'), ('performance', 'Performance'), ('custom', 'Custom Application'), ('backup', 'Backup & Maintenance')], default='custom', max_length=20)),
                ('var_type', models.CharField(choices=[('string', 'String'), ('boolean', 'Boolean'), ('integer', 'Integer'), ('float', 'Float'), ('url', 'URL'), ('email', 'Email'), ('password', 'Password'), ('json', 'JSON'), ('csv', 'CSV (Comma Separated)')], default='string', max_length=20)),
                ('is_required', models.BooleanField(default=False, help_text='Variável obrigatória')),
                ('is_sensitive', models.BooleanField(default=False, help_text='Variável sensível (senha, chave, etc.)')),
                ('is_active', models.BooleanField(default=True, help_text='Variável ativa no sistema')),
                ('order', models.PositiveIntegerField(default=0, help_text='Ordem de exibição')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Variável de Ambiente',
                'verbose_name_plural': 'Variáveis de Ambiente',
                'ordering': ['category', 'order', 'key'],
            },
        ),
    ]
