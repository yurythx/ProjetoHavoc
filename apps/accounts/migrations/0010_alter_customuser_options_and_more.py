# Generated by Django 5.2.1 on 2025-05-23 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_remove_customuser_data_nascimento_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customuser',
            options={'verbose_name': 'Usuário', 'verbose_name_plural': 'Usuários'},
        ),
        migrations.AlterModelOptions(
            name='socialauthsettings',
            options={'verbose_name': 'Configuração de Autenticação Social', 'verbose_name_plural': 'Configurações de Autenticação Social'},
        ),
        migrations.AddField(
            model_name='customuser',
            name='data_nascimento',
            field=models.DateField(blank=True, null=True),
        ),
    ]
