# Generated by Django 5.2.1 on 2025-05-29 13:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_useractivity'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UserActivity',
        ),
    ]
