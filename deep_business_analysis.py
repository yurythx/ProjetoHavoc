#!/usr/bin/env python
"""
Análise profunda e específica das regras de negócio
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from apps.config.models import *
from apps.accounts.models import *

def deep_business_analysis():
    """Análise profunda das regras de negócio"""
    print("🔬 === ANÁLISE PROFUNDA DAS REGRAS DE NEGÓCIO ===")
    
    issues = []
    
    # 1. Análise de Constraints e Validações
    print("\n1. 🔒 ANALISANDO CONSTRAINTS E VALIDAÇÕES...")
    
    # Testar se SystemConfig realmente é singleton
    try:
        with transaction.atomic():
            SystemConfig.objects.create(
                site_name="Teste Duplicado",
                site_description="Teste"
            )
            issues.append("❌ ERRO CRÍTICO: SystemConfig permite múltiplas instâncias (não é singleton)")
    except Exception:
        print("   ✅ SystemConfig: Singleton funcionando corretamente")
    
    # Testar se EmailConfig permite múltiplos padrões
    try:
        with transaction.atomic():
            EmailConfig.objects.create(
                email_host="teste1.com",
                email_port=587,
                email_host_user="test@test.com",
                email_host_password="test",
                default_from_email="test@test.com",
                is_default=True
            )
            EmailConfig.objects.create(
                email_host="teste2.com", 
                email_port=587,
                email_host_user="test2@test.com",
                email_host_password="test",
                default_from_email="test2@test.com",
                is_default=True
            )
            issues.append("❌ ERRO CRÍTICO: EmailConfig permite múltiplas configurações padrão")
    except Exception:
        print("   ✅ EmailConfig: Validação de padrão único funcionando")
    
    # 2. Análise de Dependências de Apps
    print("\n2. 🔗 ANALISANDO DEPENDÊNCIAS DE APPS...")
    
    # Verificar se apps core podem ser desativados
    core_apps = AppConfig.objects.filter(is_core=True)
    for app in core_apps:
        try:
            # Testar via save()
            original_state = app.is_active
            app.is_active = False
            app.save()
            app.refresh_from_db()

            # Se ainda está ativo após tentar desativar, a proteção funcionou
            if app.is_active:
                print(f"   ✅ App core '{app.name}': Proteção via save() funcionando (forçou ativação)")
            else:
                issues.append(f"❌ ERRO CRÍTICO: App core '{app.name}' pode ser desativado via save()")
                app.is_active = True
                app.save()
        except Exception as e:
            print(f"   ✅ App core '{app.name}': Proteção via save() funcionando (exceção)")

        try:
            # Testar via update() (bypass mais comum)
            AppConfig.objects.filter(pk=app.pk).update(is_active=False)
            app.refresh_from_db()
            if not app.is_active:
                issues.append(f"❌ ERRO CRÍTICO: App core '{app.name}' pode ser desativado via update()")
                # Reativar
                app.is_active = True
                app.save()
            else:
                print(f"   ✅ App core '{app.name}': Proteção via update() funcionando")
        except Exception as e:
            print(f"   ✅ App core '{app.name}': Proteção via update() funcionando (constraint)")
    
    # 3. Análise de Validações de Usuário
    print("\n3. 👤 ANALISANDO VALIDAÇÕES DE USUÁRIO...")
    
    User = get_user_model()
    
    # Testar validação de email duplicado
    try:
        with transaction.atomic():
            User.objects.create_user(
                username="teste_dup1",
                email="admin@projetohavoc.com",  # Email já existente
                password="test123"
            )
            issues.append("❌ ERRO CRÍTICO: Sistema permite emails duplicados")
    except Exception:
        print("   ✅ Validação de email único funcionando")
    
    # Testar validação de data de nascimento futura
    try:
        with transaction.atomic():
            from datetime import date, timedelta
            future_date = date.today() + timedelta(days=365)
            user = User.objects.create_user(
                username="teste_future",
                email="future@test.com",
                password="test123"
            )
            user.data_nascimento = future_date
            user.save()
            issues.append("❌ ERRO CRÍTICO: Sistema permite data de nascimento futura")
    except Exception:
        print("   ✅ Validação de data de nascimento funcionando")
    
    # 4. Análise de Criptografia
    print("\n4. 🔐 ANALISANDO CRIPTOGRAFIA...")
    
    # Testar criptografia de senhas LDAP
    try:
        ldap_config = LDAPConfig.objects.create(
            server="ldap.test.com",
            port=389,
            bind_dn="cn=admin,dc=test,dc=com",
            domain="test.com"
        )
        ldap_config.set_password("senha_teste")
        ldap_config.save()
        
        # Verificar se a senha foi criptografada
        if ldap_config.bind_password == "senha_teste":
            issues.append("❌ ERRO CRÍTICO: Senha LDAP não está sendo criptografada")
        else:
            print("   ✅ Criptografia de senha LDAP funcionando")
        
        # Testar descriptografia
        decrypted = ldap_config.get_password()
        if decrypted != "senha_teste":
            issues.append("❌ ERRO CRÍTICO: Descriptografia de senha LDAP falhando")
        else:
            print("   ✅ Descriptografia de senha LDAP funcionando")
            
        ldap_config.delete()
    except Exception as e:
        issues.append(f"❌ ERRO: Falha no teste de criptografia LDAP: {e}")
    
    # 5. Análise de Rate Limiting
    print("\n5. ⚡ ANALISANDO RATE LIMITING...")
    
    # Verificar se rate limiting diferenciado está funcionando
    from django.test import Client
    from django.core.cache import cache
    
    # Limpar cache primeiro
    cache.clear()
    
    client = Client()
    
    # Testar rate limiting para usuário anônimo
    anon_blocked = False
    for i in range(105):  # Mais que o limite de 100
        response = client.get('/')
        if response.status_code == 429:
            anon_blocked = True
            break
    
    if not anon_blocked:
        issues.append("❌ ERRO: Rate limiting para usuários anônimos não está funcionando")
    else:
        print("   ✅ Rate limiting para anônimos funcionando")
    
    # 6. Análise de Middleware
    print("\n6. 🛡️ ANALISANDO MIDDLEWARE...")
    
    # Verificar se middleware de segurança está ativo
    from django.conf import settings
    
    required_middleware = [
        'core.middleware.UnifiedSecurityMiddleware',
        'apps.accounts.middleware.UserAuditMiddleware',
        'apps.config.middleware.AppControlMiddleware'
    ]
    
    for middleware in required_middleware:
        if middleware not in settings.MIDDLEWARE:
            issues.append(f"❌ ERRO: Middleware obrigatório '{middleware}' não está ativo")
        else:
            print(f"   ✅ Middleware '{middleware}' ativo")
    
    # 7. Análise de Configurações Críticas
    print("\n7. ⚙️ ANALISANDO CONFIGURAÇÕES CRÍTICAS...")
    
    # Verificar configurações de segurança
    security_settings = {
        'DEBUG': False,  # Deve ser False em produção
        'ALLOWED_HOSTS': ['*'],  # Deve ser configurado adequadamente
        'SECRET_KEY': 'django-insecure-',  # Não deve usar chave insegura
    }
    
    if settings.DEBUG:
        issues.append("⚠️ AVISO: DEBUG está ativo (não recomendado para produção)")
    
    if '*' in settings.ALLOWED_HOSTS:
        issues.append("⚠️ AVISO: ALLOWED_HOSTS permite qualquer host (risco de segurança)")
    
    if settings.SECRET_KEY.startswith('django-insecure-'):
        issues.append("❌ ERRO CRÍTICO: SECRET_KEY usando valor inseguro padrão")
    
    # 8. Resumo Final
    print("\n" + "="*60)
    print("📋 === RESUMO DA ANÁLISE PROFUNDA ===")
    
    critical_errors = [issue for issue in issues if issue.startswith("❌ ERRO CRÍTICO")]
    errors = [issue for issue in issues if issue.startswith("❌ ERRO") and not issue.startswith("❌ ERRO CRÍTICO")]
    warnings = [issue for issue in issues if issue.startswith("⚠️")]
    
    print(f"\n🚨 ERROS CRÍTICOS: {len(critical_errors)}")
    for error in critical_errors:
        print(f"   {error}")
    
    print(f"\n❌ ERROS: {len(errors)}")
    for error in errors:
        print(f"   {error}")
    
    print(f"\n⚠️ AVISOS: {len(warnings)}")
    for warning in warnings:
        print(f"   {warning}")
    
    if not issues:
        print("\n🎉 SISTEMA PERFEITO!")
        print("✅ Todas as regras de negócio estão implementadas corretamente!")
    else:
        print(f"\n🎯 TOTAL DE PROBLEMAS: {len(issues)}")
        if critical_errors:
            print("🚨 AÇÃO URGENTE: Corrigir erros críticos imediatamente")
        if errors:
            print("❌ AÇÃO NECESSÁRIA: Corrigir erros")
        if warnings:
            print("⚠️ RECOMENDAÇÃO: Revisar avisos")

if __name__ == '__main__':
    deep_business_analysis()
