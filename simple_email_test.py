#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.config.models import EmailConfig

print("🔍 Verificando configurações existentes...")
configs = EmailConfig.objects.all()
print(f"Total: {configs.count()}")

for config in configs:
    print(f"- ID: {config.id}, Slug: {config.slug}, Host: {config.email_host}")

print("\n🧪 Testando criação...")
try:
    new_config = EmailConfig.objects.create(
        email_host='smtp.test.com',
        email_port=587,
        email_host_user='test@test.com',
        email_host_password='test123',
        email_use_tls=True,
        default_from_email='test@test.com',
        is_active=True
    )
    print(f"✅ Criado: {new_config.slug}")
    new_config.delete()
    print("🗑️ Removido")
except Exception as e:
    print(f"❌ Erro: {e}")
