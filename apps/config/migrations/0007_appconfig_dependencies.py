# Generated by Django 5.2.1 on 2025-05-23 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0006_appconfig_systemconfig_enable_app_management'),
    ]

    operations = [
        migrations.AddField(
            model_name='appconfig',
            name='dependencies',
            field=models.ManyToManyField(blank=True, help_text='Módulos que este app depende para funcionar', related_name='dependents', to='config.appconfig'),
        ),
    ]
