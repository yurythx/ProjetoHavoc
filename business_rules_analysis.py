#!/usr/bin/env python
"""
Análise completa das regras de negócio do sistema
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from apps.config.models import (
    SystemConfig, EmailConfig, LDAPConfig, SocialProviderConfig,
    DatabaseConfig, Widget, MenuConfig, Plugin, AppConfig,
    EnvironmentVariable
)
from apps.accounts.models import CustomUser, Cargo, Departamento, UserAuditLog

def analyze_business_rules():
    """Análise completa das regras de negócio"""
    print("🔍 === ANÁLISE COMPLETA DAS REGRAS DE NEGÓCIO ===")
    
    errors_found = []
    warnings_found = []
    
    # 1. Análise de SystemConfig
    print("\n1. 📊 ANALISANDO SYSTEMCONFIG...")
    
    try:
        # Verificar se permite múltiplas instâncias (deveria ser singleton)
        system_configs = SystemConfig.objects.all()
        if system_configs.count() > 1:
            errors_found.append("❌ ERRO: Múltiplas instâncias de SystemConfig encontradas (deveria ser singleton)")
        elif system_configs.count() == 0:
            warnings_found.append("⚠️ AVISO: Nenhuma configuração do sistema encontrada")
        else:
            print("   ✅ SystemConfig: Instância única encontrada")
    except Exception as e:
        errors_found.append(f"❌ ERRO: Falha ao verificar SystemConfig: {e}")
    
    # 2. Análise de EmailConfig
    print("\n2. 📧 ANALISANDO EMAILCONFIG...")
    
    try:
        email_configs = EmailConfig.objects.all()
        default_configs = EmailConfig.objects.filter(is_default=True)
        
        if default_configs.count() > 1:
            errors_found.append("❌ ERRO: Múltiplas configurações de email marcadas como padrão")
        
        # Verificar configurações ativas sem padrão
        active_configs = EmailConfig.objects.filter(is_active=True)
        if active_configs.exists() and not default_configs.exists():
            warnings_found.append("⚠️ AVISO: Configurações de email ativas mas nenhuma marcada como padrão")
        
        print(f"   📊 Total: {email_configs.count()}, Ativas: {active_configs.count()}, Padrão: {default_configs.count()}")
        
    except Exception as e:
        errors_found.append(f"❌ ERRO: Falha ao verificar EmailConfig: {e}")
    
    # 3. Análise de AppConfig e Dependências
    print("\n3. 🔧 ANALISANDO APPCONFIG E DEPENDÊNCIAS...")
    
    try:
        app_configs = AppConfig.objects.all()
        core_apps = AppConfig.objects.filter(is_core=True)
        
        # Verificar se apps core estão ativos
        inactive_core_apps = core_apps.filter(is_active=False)
        if inactive_core_apps.exists():
            for app in inactive_core_apps:
                errors_found.append(f"❌ ERRO: App core '{app.name}' está inativo")
        
        # Verificar dependências circulares
        circular_deps = check_circular_dependencies()
        if circular_deps:
            for dep in circular_deps:
                errors_found.append(f"❌ ERRO: Dependência circular detectada: {dep}")
        
        # Verificar dependências órfãs
        orphan_deps = check_orphan_dependencies()
        if orphan_deps:
            for dep in orphan_deps:
                warnings_found.append(f"⚠️ AVISO: App '{dep}' tem dependências inativas")
        
        print(f"   📊 Total: {app_configs.count()}, Core: {core_apps.count()}, Ativos: {app_configs.filter(is_active=True).count()}")
        
    except Exception as e:
        errors_found.append(f"❌ ERRO: Falha ao verificar AppConfig: {e}")
    
    # 4. Análise de Usuários
    print("\n4. 👥 ANALISANDO USUÁRIOS...")
    
    try:
        User = get_user_model()
        users = User.objects.all()
        active_users = users.filter(is_active=True)
        staff_users = users.filter(is_staff=True, is_active=True)
        superusers = users.filter(is_superuser=True, is_active=True)
        
        if not superusers.exists():
            errors_found.append("❌ ERRO: Nenhum superusuário ativo encontrado")
        
        if not staff_users.exists():
            warnings_found.append("⚠️ AVISO: Nenhum usuário staff ativo encontrado")
        
        # Verificar usuários com emails duplicados
        from django.db.models import Count
        duplicate_emails = User.objects.values('email').annotate(
            count=Count('email')
        ).filter(count__gt=1)
        
        if duplicate_emails.exists():
            for dup in duplicate_emails:
                errors_found.append(f"❌ ERRO: Email duplicado encontrado: {dup['email']}")
        
        print(f"   📊 Total: {users.count()}, Ativos: {active_users.count()}, Staff: {staff_users.count()}, Super: {superusers.count()}")
        
    except Exception as e:
        errors_found.append(f"❌ ERRO: Falha ao verificar usuários: {e}")
    
    # 5. Análise de Integridade de Dados
    print("\n5. 🔗 ANALISANDO INTEGRIDADE DE DADOS...")
    
    try:
        # Verificar referências órfãs em UserAuditLog
        audit_logs = UserAuditLog.objects.all()
        orphan_logs = 0
        for log in audit_logs:
            if not log.user:
                orphan_logs += 1
        
        if orphan_logs > 0:
            warnings_found.append(f"⚠️ AVISO: {orphan_logs} logs de auditoria órfãos encontrados")
        
        print(f"   📊 Logs de auditoria: {audit_logs.count()}, Órfãos: {orphan_logs}")
        
    except Exception as e:
        errors_found.append(f"❌ ERRO: Falha ao verificar integridade: {e}")
    
    # 6. Análise de Validações
    print("\n6. ✅ ANALISANDO VALIDAÇÕES...")
    
    validation_issues = check_validation_issues()
    errors_found.extend(validation_issues['errors'])
    warnings_found.extend(validation_issues['warnings'])
    
    # 7. Resumo Final
    print("\n" + "="*60)
    print("📋 === RESUMO DA ANÁLISE ===")
    
    print(f"\n❌ ERROS CRÍTICOS ENCONTRADOS: {len(errors_found)}")
    for error in errors_found:
        print(f"   {error}")
    
    print(f"\n⚠️ AVISOS ENCONTRADOS: {len(warnings_found)}")
    for warning in warnings_found:
        print(f"   {warning}")
    
    if not errors_found and not warnings_found:
        print("\n🎉 NENHUM PROBLEMA ENCONTRADO!")
        print("✅ Todas as regras de negócio estão corretas!")
    else:
        print(f"\n🎯 TOTAL DE PROBLEMAS: {len(errors_found) + len(warnings_found)}")
        if errors_found:
            print("🚨 AÇÃO NECESSÁRIA: Corrigir erros críticos")
        if warnings_found:
            print("⚠️ RECOMENDAÇÃO: Revisar avisos")

def check_circular_dependencies():
    """Verifica dependências circulares em AppConfig"""
    circular_deps = []
    
    def has_circular_dependency(app, visited=None, path=None):
        if visited is None:
            visited = set()
        if path is None:
            path = []
        
        if app.id in visited:
            return path[path.index(app.id):] + [app.id]
        
        visited.add(app.id)
        path.append(app.id)
        
        for dependency in app.dependencies.all():
            result = has_circular_dependency(dependency, visited.copy(), path.copy())
            if result:
                return result
        
        return None
    
    for app in AppConfig.objects.all():
        circular = has_circular_dependency(app)
        if circular:
            app_names = [AppConfig.objects.get(id=app_id).name for app_id in circular]
            circular_deps.append(" -> ".join(app_names))
    
    return list(set(circular_deps))  # Remove duplicatas

def check_orphan_dependencies():
    """Verifica apps com dependências inativas"""
    orphan_deps = []
    
    for app in AppConfig.objects.filter(is_active=True):
        inactive_deps = app.dependencies.filter(is_active=False)
        if inactive_deps.exists():
            dep_names = [dep.name for dep in inactive_deps]
            orphan_deps.append(f"{app.name} depende de: {', '.join(dep_names)}")
    
    return orphan_deps

def check_validation_issues():
    """Verifica problemas de validação"""
    issues = {'errors': [], 'warnings': []}
    
    # Verificar se há dados inválidos que passaram pelas validações
    try:
        # Verificar usuários com datas de nascimento futuras
        User = get_user_model()
        from datetime import date
        future_birth_users = User.objects.filter(data_nascimento__gt=date.today())
        if future_birth_users.exists():
            issues['errors'].append(f"❌ ERRO: {future_birth_users.count()} usuários com data de nascimento futura")
        
        # Verificar emails inválidos
        invalid_emails = User.objects.exclude(email__contains='@')
        if invalid_emails.exists():
            issues['errors'].append(f"❌ ERRO: {invalid_emails.count()} usuários com emails inválidos")
        
    except Exception as e:
        issues['errors'].append(f"❌ ERRO: Falha na verificação de validações: {e}")
    
    return issues

if __name__ == '__main__':
    analyze_business_rules()
