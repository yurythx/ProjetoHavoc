#!/usr/bin/env python
"""
Auditoria Completa do Projeto Havoc
Análise de código, performance, segurança e otimizações
"""
import os
import sys
import django
import time
import psutil
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.db import connection
from django.conf import settings
from django.core.management import call_command
from django.urls import reverse
from django.core.exceptions import ValidationError
import json

def audit_projeto_havoc():
    """Auditoria completa do Projeto Havoc"""
    print("🔍 === AUDITORIA COMPLETA DO PROJETO HAVOC ===")
    print("🚀 ANÁLISE ABRANGENTE DE CÓDIGO, PERFORMANCE E SEGURANÇA")
    print("=" * 80)
    
    audit_results = {
        'errors': [],
        'warnings': [],
        'optimizations': [],
        'security_issues': [],
        'performance_issues': [],
        'recommendations': []
    }
    
    # 1. Análise de Estrutura do Projeto
    print("\n1. 📁 ANÁLISE DE ESTRUTURA DO PROJETO")
    audit_results.update(analyze_project_structure())
    
    # 2. Análise de Configurações
    print("\n2. ⚙️ ANÁLISE DE CONFIGURAÇÕES")
    audit_results.update(analyze_settings())
    
    # 3. Análise de Modelos
    print("\n3. 📊 ANÁLISE DE MODELOS")
    audit_results.update(analyze_models())
    
    # 4. Análise de Views
    print("\n4. 🌐 ANÁLISE DE VIEWS")
    audit_results.update(analyze_views())
    
    # 5. Análise de Templates
    print("\n5. 🎨 ANÁLISE DE TEMPLATES")
    audit_results.update(analyze_templates())
    
    # 6. Análise de URLs
    print("\n6. 🔗 ANÁLISE DE URLS")
    audit_results.update(analyze_urls())
    
    # 7. Análise de Banco de Dados
    print("\n7. 🗄️ ANÁLISE DE BANCO DE DADOS")
    audit_results.update(analyze_database())
    
    # 8. Análise de Performance
    print("\n8. ⚡ ANÁLISE DE PERFORMANCE")
    audit_results.update(analyze_performance())
    
    # 9. Análise de Segurança
    print("\n9. 🔒 ANÁLISE DE SEGURANÇA")
    audit_results.update(analyze_security())
    
    # 10. Testes de Funcionalidade
    print("\n10. 🧪 TESTES DE FUNCIONALIDADE")
    audit_results.update(test_functionality())
    
    # 11. Gerar Relatório Final
    print("\n11. 📋 RELATÓRIO FINAL")
    generate_final_report(audit_results)
    
    return audit_results

def analyze_project_structure():
    """Analisa a estrutura do projeto"""
    print("   📁 Verificando estrutura de arquivos...")
    
    results = {'structure_issues': []}
    
    # Verificar arquivos essenciais
    essential_files = [
        'manage.py',
        'requirements.txt',
        'core/settings.py',
        'core/urls.py',
        'core/wsgi.py',
    ]
    
    missing_files = []
    for file_path in essential_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        results['structure_issues'].append(f"Arquivos essenciais ausentes: {missing_files}")
        print(f"   ❌ Arquivos ausentes: {missing_files}")
    else:
        print("   ✅ Arquivos essenciais presentes")
    
    # Verificar estrutura de apps
    apps_dir = Path('apps')
    if apps_dir.exists():
        apps = [d for d in apps_dir.iterdir() if d.is_dir() and not d.name.startswith('__')]
        print(f"   📦 Apps encontrados: {len(apps)}")
        
        for app in apps:
            app_files = ['models.py', 'views.py', 'urls.py']
            missing_app_files = []
            for file_name in app_files:
                if not (app / file_name).exists():
                    missing_app_files.append(f"{app.name}/{file_name}")
            
            if missing_app_files:
                results['structure_issues'].append(f"Arquivos ausentes no app {app.name}: {missing_app_files}")
    
    # Verificar diretórios de mídia e estáticos
    static_dirs = ['static', 'media', 'templates']
    for dir_name in static_dirs:
        if not Path(dir_name).exists():
            results['structure_issues'].append(f"Diretório {dir_name} não encontrado")
    
    return results

def analyze_settings():
    """Analisa as configurações do Django"""
    print("   ⚙️ Verificando configurações...")
    
    results = {'settings_issues': [], 'settings_warnings': []}
    
    # Verificar configurações de segurança
    security_checks = [
        ('DEBUG', False, 'DEBUG deve ser False em produção'),
        ('SECRET_KEY', lambda x: not x.startswith('django-insecure-'), 'SECRET_KEY deve ser segura'),
        ('ALLOWED_HOSTS', lambda x: len(x) > 0, 'ALLOWED_HOSTS deve estar configurado'),
    ]
    
    for setting_name, expected, message in security_checks:
        try:
            value = getattr(settings, setting_name)
            if callable(expected):
                if not expected(value):
                    results['settings_warnings'].append(f"{setting_name}: {message}")
            elif value != expected:
                results['settings_warnings'].append(f"{setting_name}: {message}")
        except AttributeError:
            results['settings_issues'].append(f"Configuração {setting_name} não encontrada")
    
    # Verificar configurações de banco
    try:
        db_config = settings.DATABASES['default']
        if db_config['ENGINE'] == 'django.db.backends.sqlite3':
            results['settings_warnings'].append("SQLite não é recomendado para produção")
        print(f"   🗄️ Banco: {db_config['ENGINE']}")
    except KeyError:
        results['settings_issues'].append("Configuração de banco não encontrada")
    
    # Verificar middleware de segurança
    security_middleware = [
        'django.middleware.security.SecurityMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
    ]
    
    missing_middleware = []
    for middleware in security_middleware:
        if middleware not in settings.MIDDLEWARE:
            missing_middleware.append(middleware)
    
    if missing_middleware:
        results['settings_issues'].append(f"Middleware de segurança ausente: {missing_middleware}")
    
    print(f"   ✅ Configurações analisadas")
    print(f"   ⚠️ Issues: {len(results['settings_issues'])}")
    print(f"   ⚠️ Warnings: {len(results['settings_warnings'])}")
    
    return results

def analyze_models():
    """Analisa os modelos do projeto"""
    print("   📊 Verificando modelos...")
    
    results = {'model_issues': [], 'model_optimizations': []}
    
    try:
        from django.apps import apps
        
        # Obter todos os modelos
        all_models = apps.get_models()
        print(f"   📊 Total de modelos: {len(all_models)}")
        
        for model in all_models:
            model_name = f"{model._meta.app_label}.{model._meta.model_name}"
            
            # Verificar se tem __str__ method
            if not hasattr(model, '__str__') or model.__str__ is object.__str__:
                results['model_optimizations'].append(f"{model_name}: Implementar método __str__")
            
            # Verificar Meta class
            if not hasattr(model._meta, 'verbose_name'):
                results['model_optimizations'].append(f"{model_name}: Adicionar verbose_name")
            
            # Verificar índices
            indexed_fields = []
            for field in model._meta.fields:
                if field.db_index or field.unique:
                    indexed_fields.append(field.name)
            
            # Verificar campos de data sem auto_now
            for field in model._meta.fields:
                if field.get_internal_type() in ['DateTimeField', 'DateField']:
                    if not getattr(field, 'auto_now', False) and not getattr(field, 'auto_now_add', False):
                        if field.name in ['created_at', 'updated_at', 'modified_at']:
                            results['model_optimizations'].append(f"{model_name}.{field.name}: Considerar auto_now/auto_now_add")
        
        print(f"   ✅ Modelos analisados")
        
    except Exception as e:
        results['model_issues'].append(f"Erro ao analisar modelos: {str(e)}")
        print(f"   ❌ Erro: {e}")
    
    return results

def analyze_views():
    """Analisa as views do projeto"""
    print("   🌐 Verificando views...")
    
    results = {'view_issues': [], 'view_optimizations': []}
    
    # Testar views principais
    client = Client()
    
    # Tentar login
    try:
        User = get_user_model()
        admin_user = User.objects.filter(username='admin').first()
        if admin_user:
            login_success = client.login(username='admin', password='admin123')
            if login_success:
                print("   ✅ Login de teste bem-sucedido")
            else:
                results['view_issues'].append("Falha no login de teste")
        else:
            results['view_issues'].append("Usuário admin não encontrado")
    except Exception as e:
        results['view_issues'].append(f"Erro no teste de login: {str(e)}")
    
    # Testar URLs principais
    test_urls = [
        '/',
        '/accounts/login/',
        '/config/',
        '/config/wizard/',
        '/articles/',
    ]
    
    for url in test_urls:
        try:
            response = client.get(url)
            if response.status_code >= 500:
                results['view_issues'].append(f"Erro 500 em {url}")
            elif response.status_code == 404:
                results['view_optimizations'].append(f"URL {url} retorna 404")
            else:
                print(f"   ✅ {url}: {response.status_code}")
        except Exception as e:
            results['view_issues'].append(f"Erro ao testar {url}: {str(e)}")
    
    return results

def analyze_templates():
    """Analisa os templates do projeto"""
    print("   🎨 Verificando templates...")
    
    results = {'template_issues': [], 'template_optimizations': []}
    
    # Verificar diretório de templates
    template_dirs = [
        Path('templates'),
        Path('apps/accounts/templates'),
        Path('apps/config/templates'),
        Path('apps/articles/templates'),
    ]
    
    total_templates = 0
    for template_dir in template_dirs:
        if template_dir.exists():
            templates = list(template_dir.rglob('*.html'))
            total_templates += len(templates)
            
            # Verificar templates base
            for template in templates:
                if template.name == 'base.html':
                    print(f"   ✅ Template base encontrado: {template}")
    
    print(f"   📄 Total de templates: {total_templates}")
    
    # Verificar se há templates órfãos ou duplicados
    if total_templates == 0:
        results['template_issues'].append("Nenhum template encontrado")
    
    return results

def analyze_urls():
    """Analisa as configurações de URLs"""
    print("   🔗 Verificando URLs...")
    
    results = {'url_issues': [], 'url_optimizations': []}
    
    try:
        from django.urls import get_resolver
        
        resolver = get_resolver()
        url_patterns = resolver.url_patterns
        
        print(f"   🔗 Padrões de URL encontrados: {len(url_patterns)}")
        
        # Verificar se há URLs duplicadas ou conflitantes
        # Isso seria uma análise mais complexa, por agora apenas contamos
        
    except Exception as e:
        results['url_issues'].append(f"Erro ao analisar URLs: {str(e)}")
    
    return results

def analyze_database():
    """Analisa o banco de dados"""
    print("   🗄️ Verificando banco de dados...")
    
    results = {'db_issues': [], 'db_optimizations': []}
    
    try:
        # Testar conexão
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("   ✅ Conexão com banco funcionando")
        
        # Verificar migrações pendentes
        from django.core.management.commands.migrate import Command as MigrateCommand
        from django.db.migrations.executor import MigrationExecutor
        
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            results['db_issues'].append(f"Migrações pendentes: {len(plan)}")
            print(f"   ⚠️ Migrações pendentes: {len(plan)}")
        else:
            print("   ✅ Todas as migrações aplicadas")
        
        # Verificar tamanho das tabelas
        if 'sqlite' in settings.DATABASES['default']['ENGINE']:
            db_path = settings.DATABASES['default']['NAME']
            if Path(db_path).exists():
                db_size = Path(db_path).stat().st_size
                print(f"   💾 Tamanho do banco: {db_size / 1024 / 1024:.2f} MB")
                
                if db_size > 100 * 1024 * 1024:  # 100MB
                    results['db_optimizations'].append("Banco de dados grande, considerar PostgreSQL")
        
    except Exception as e:
        results['db_issues'].append(f"Erro ao analisar banco: {str(e)}")
        print(f"   ❌ Erro: {e}")
    
    return results

def analyze_performance():
    """Analisa performance do sistema"""
    print("   ⚡ Verificando performance...")
    
    results = {'performance_issues': [], 'performance_optimizations': []}
    
    # Verificar uso de recursos
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    print(f"   🔧 CPU: {cpu_percent}%")
    print(f"   💾 Memória: {memory.percent}%")
    
    if cpu_percent > 80:
        results['performance_issues'].append(f"Alto uso de CPU: {cpu_percent}%")
    
    if memory.percent > 80:
        results['performance_issues'].append(f"Alto uso de memória: {memory.percent}%")
    
    # Verificar configurações de cache
    cache_config = getattr(settings, 'CACHES', {})
    default_cache = cache_config.get('default', {})
    cache_backend = default_cache.get('BACKEND', '')
    
    if 'locmem' in cache_backend or 'dummy' in cache_backend:
        results['performance_optimizations'].append("Configurar Redis ou Memcached para cache")
    
    # Verificar debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        if not settings.DEBUG:
            results['performance_issues'].append("Debug Toolbar ativo em produção")
        else:
            print("   🔧 Debug Toolbar ativo (desenvolvimento)")
    
    # Verificar compressão de arquivos estáticos
    if 'compressor' not in settings.INSTALLED_APPS:
        results['performance_optimizations'].append("Instalar django-compressor para otimizar CSS/JS")
    
    return results

def analyze_security():
    """Analisa segurança do sistema"""
    print("   🔒 Verificando segurança...")
    
    results = {'security_issues': [], 'security_optimizations': []}
    
    # Verificar configurações de segurança
    security_settings = [
        ('SECURE_SSL_REDIRECT', True, 'Forçar HTTPS'),
        ('SECURE_HSTS_SECONDS', lambda x: x > 0, 'Configurar HSTS'),
        ('SECURE_CONTENT_TYPE_NOSNIFF', True, 'Prevenir MIME sniffing'),
        ('SECURE_BROWSER_XSS_FILTER', True, 'Filtro XSS do browser'),
        ('X_FRAME_OPTIONS', 'DENY', 'Prevenir clickjacking'),
    ]
    
    for setting_name, expected, description in security_settings:
        try:
            value = getattr(settings, setting_name, None)
            if callable(expected):
                if not expected(value):
                    results['security_optimizations'].append(f"{description}: {setting_name}")
            elif value != expected:
                results['security_optimizations'].append(f"{description}: {setting_name}")
        except AttributeError:
            results['security_optimizations'].append(f"{description}: {setting_name} não configurado")
    
    # Verificar senhas fracas
    try:
        User = get_user_model()
        users_with_weak_passwords = []
        
        # Verificar alguns usuários (limitado para performance)
        for user in User.objects.all()[:10]:
            if user.check_password('123456') or user.check_password('password') or user.check_password('admin'):
                users_with_weak_passwords.append(user.username)
        
        if users_with_weak_passwords:
            results['security_issues'].append(f"Usuários com senhas fracas: {users_with_weak_passwords}")
    
    except Exception as e:
        results['security_issues'].append(f"Erro ao verificar senhas: {str(e)}")
    
    # Verificar permissões de arquivos
    sensitive_files = ['core/settings.py', 'manage.py']
    for file_path in sensitive_files:
        if Path(file_path).exists():
            file_stat = Path(file_path).stat()
            # Verificar se arquivo é legível por outros (simplificado)
            if oct(file_stat.st_mode)[-1] in ['4', '5', '6', '7']:
                results['security_optimizations'].append(f"Arquivo {file_path} pode ter permissões muito abertas")
    
    return results

def test_functionality():
    """Testa funcionalidades principais"""
    print("   🧪 Testando funcionalidades...")
    
    results = {'functionality_issues': [], 'functionality_optimizations': []}
    
    client = Client()
    
    # Teste de login
    try:
        response = client.post('/accounts/login/', {
            'username': 'admin',
            'password': 'admin123'
        })
        if response.status_code == 200 and 'error' in response.content.decode().lower():
            results['functionality_issues'].append("Problema no sistema de login")
        else:
            print("   ✅ Sistema de login funcionando")
    except Exception as e:
        results['functionality_issues'].append(f"Erro no teste de login: {str(e)}")
    
    # Teste do wizard
    try:
        login_success = client.login(username='admin', password='admin123')
        if login_success:
            response = client.get('/config/wizard/')
            if response.status_code >= 400:
                results['functionality_issues'].append(f"Erro no wizard: {response.status_code}")
            else:
                print("   ✅ Setup Wizard funcionando")
    except Exception as e:
        results['functionality_issues'].append(f"Erro no teste do wizard: {str(e)}")
    
    # Teste de criação de usuário
    try:
        User = get_user_model()
        test_user = User.objects.create_user(
            username='test_audit',
            email='test@audit.com',
            password='test123456'
        )
        test_user.delete()
        print("   ✅ Criação de usuário funcionando")
    except Exception as e:
        results['functionality_issues'].append(f"Erro na criação de usuário: {str(e)}")
    
    return results

def generate_final_report(audit_results):
    """Gera relatório final da auditoria"""
    print("   📋 Gerando relatório final...")
    
    # Contar issues
    total_errors = sum(len(audit_results.get(key, [])) for key in audit_results if 'issues' in key)
    total_warnings = sum(len(audit_results.get(key, [])) for key in audit_results if 'warnings' in key)
    total_optimizations = sum(len(audit_results.get(key, [])) for key in audit_results if 'optimizations' in key)
    
    print(f"\n📊 RESUMO DA AUDITORIA:")
    print(f"   ❌ Erros críticos: {total_errors}")
    print(f"   ⚠️ Avisos: {total_warnings}")
    print(f"   🚀 Otimizações sugeridas: {total_optimizations}")
    
    # Calcular score geral
    max_score = 100
    penalty_per_error = 10
    penalty_per_warning = 5
    penalty_per_optimization = 2
    
    score = max_score - (total_errors * penalty_per_error) - (total_warnings * penalty_per_warning) - (total_optimizations * penalty_per_optimization)
    score = max(0, score)
    
    print(f"\n🎯 SCORE GERAL DO PROJETO: {score}/100")
    
    if score >= 90:
        print("   🎉 EXCELENTE! Projeto em ótimo estado")
    elif score >= 70:
        print("   ✅ BOM! Algumas melhorias recomendadas")
    elif score >= 50:
        print("   ⚠️ REGULAR! Várias otimizações necessárias")
    else:
        print("   🚨 CRÍTICO! Ação imediata necessária")
    
    # Salvar relatório detalhado
    report_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'score': score,
        'summary': {
            'errors': total_errors,
            'warnings': total_warnings,
            'optimizations': total_optimizations
        },
        'details': audit_results
    }
    
    with open('audit_report.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Relatório detalhado salvo em: audit_report.json")

if __name__ == '__main__':
    audit_projeto_havoc()
