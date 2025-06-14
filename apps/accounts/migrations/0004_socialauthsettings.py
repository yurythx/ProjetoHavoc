# Generated by Django 5.2.1 on 2025-05-21 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_customuser_bio_customuser_cargo_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialAuthSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(max_length=30)),
                ('client_id', models.CharField(max_length=255)),
                ('secret', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'unique_together': {('provider',)},
            },
        ),
    ]
