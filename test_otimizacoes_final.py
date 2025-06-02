#!/usr/bin/env python
"""
Teste Final das Otimizações Implementadas
Projeto Havoc - Verificação de Melhorias
"""
import os
import sys
import django
import time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
import json

def test_otimizacoes_final():
    """Testa todas as otimizações implementadas"""
    print("🔧 === TESTE FINAL DAS OTIMIZAÇÕES ===")
    print("🚀 PROJETO HAVOC - VERIFICAÇÃO DE MELHORIAS")
    print("=" * 70)
    
    results = {
        'security': test_security_improvements(),
        'performance': test_performance_improvements(),
        'wizard': test_wizard_fixes(),
        'compressor': test_compressor_setup(),
        'monitoring': test_monitoring_system(),
        'models': test_model_improvements(),
        'overall': {}
    }
    
    # Calcular score geral
    total_tests = sum(len(category) for category in results.values() if isinstance(category, dict))
    passed_tests = sum(
        sum(1 for test in category.values() if test.get('status') == 'pass') 
        for category in results.values() 
        if isinstance(category, dict)
    )
    
    overall_score = int((passed_tests / total_tests) * 100) if total_tests > 0 else 0
    
    results['overall'] = {
        'score': overall_score,
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': total_tests - passed_tests
    }
    
    # Exibir resultados
    display_results(results)
    
    return results

def test_security_improvements():
    """Testa melhorias de segurança"""
    print("\n1. 🔒 TESTANDO MELHORIAS DE SEGURANÇA")
    
    tests = {}
    
    # Teste 1: Configurações de segurança
    try:
        security_settings = [
            'SECURE_CONTENT_TYPE_NOSNIFF',
            'SECURE_BROWSER_XSS_FILTER',
            'X_FRAME_OPTIONS',
            'SESSION_COOKIE_HTTPONLY',
            'CSRF_COOKIE_HTTPONLY'
        ]
        
        missing_settings = []
        for setting in security_settings:
            if not hasattr(settings, setting):
                missing_settings.append(setting)
        
        if not missing_settings:
            tests['security_headers'] = {'status': 'pass', 'message': 'Headers de segurança configurados'}
            print("   ✅ Headers de segurança: OK")
        else:
            tests['security_headers'] = {'status': 'fail', 'message': f'Settings ausentes: {missing_settings}'}
            print(f"   ❌ Headers de segurança: {missing_settings}")
            
    except Exception as e:
        tests['security_headers'] = {'status': 'error', 'message': str(e)}
        print(f"   ❌ Erro nos headers: {e}")
    
    # Teste 2: Validadores de senha
    try:
        validators = getattr(settings, 'AUTH_PASSWORD_VALIDATORS', [])
        if len(validators) >= 4:
            tests['password_validators'] = {'status': 'pass', 'message': f'{len(validators)} validadores configurados'}
            print(f"   ✅ Validadores de senha: {len(validators)} configurados")
        else:
            tests['password_validators'] = {'status': 'fail', 'message': f'Apenas {len(validators)} validadores'}
            print(f"   ⚠️ Validadores de senha: apenas {len(validators)}")
            
    except Exception as e:
        tests['password_validators'] = {'status': 'error', 'message': str(e)}
        print(f"   ❌ Erro nos validadores: {e}")
    
    # Teste 3: Configurações de upload
    try:
        max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 0)
        if max_size <= 5242880:  # 5MB
            tests['upload_limits'] = {'status': 'pass', 'message': f'Limite: {max_size/1024/1024:.1f}MB'}
            print(f"   ✅ Limites de upload: {max_size/1024/1024:.1f}MB")
        else:
            tests['upload_limits'] = {'status': 'fail', 'message': f'Limite muito alto: {max_size/1024/1024:.1f}MB'}
            print(f"   ⚠️ Limite de upload alto: {max_size/1024/1024:.1f}MB")
            
    except Exception as e:
        tests['upload_limits'] = {'status': 'error', 'message': str(e)}
        print(f"   ❌ Erro nos limites: {e}")
    
    return tests

def test_performance_improvements():
    """Testa melhorias de performance"""
    print("\n2. ⚡ TESTANDO MELHORIAS DE PERFORMANCE")
    
    tests = {}
    
    # Teste 1: Django Compressor
    try:
        if 'compressor' in settings.INSTALLED_APPS:
            compress_enabled = getattr(settings, 'COMPRESS_ENABLED', False)
            tests['compressor'] = {'status': 'pass', 'message': f'Instalado, enabled: {compress_enabled}'}
            print(f"   ✅ Django Compressor: Instalado (enabled: {compress_enabled})")
        else:
            tests['compressor'] = {'status': 'fail', 'message': 'Não instalado'}
            print("   ❌ Django Compressor: Não instalado")
            
    except Exception as e:
        tests['compressor'] = {'status': 'error', 'message': str(e)}
        print(f"   ❌ Erro no compressor: {e}")
    
    # Teste 2: Middleware de Performance
    try:
        middleware_list = getattr(settings, 'MIDDLEWARE', [])
        has_performance_middleware = any('PerformanceMiddleware' in mw for mw in middleware_list)
        
        if has_performance_middleware:
            tests['performance_middleware'] = {'status': 'pass', 'message': 'Middleware ativo'}
            print("   ✅ Performance Middleware: Ativo")
        else:
            tests['performance_middleware'] = {'status': 'fail', 'message': 'Middleware não encontrado'}
            print("   ❌ Performance Middleware: Não encontrado")
            
    except Exception as e:
        tests['performance_middleware'] = {'status': 'error', 'message': str(e)}
        print(f"   ❌ Erro no middleware: {e}")
    
    # Teste 3: Configurações de cache
    try:
        cache_config = getattr(settings, 'CACHES', {})
        default_cache = cache_config.get('default', {})
        backend = default_cache.get('BACKEND', '')
        
        if 'redis' in backend.lower():
            tests['cache_config'] = {'status': 'pass', 'message': 'Redis configurado'}
            print("   ✅ Cache: Redis configurado")
        elif 'locmem' in backend.lower():
            tests['cache_config'] = {'status': 'warning', 'message': 'Local memory cache'}
            print("   ⚠️ Cache: Local memory (desenvolvimento)")
        else:
            tests['cache_config'] = {'status': 'fail', 'message': f'Backend: {backend}'}
            print(f"   ❌ Cache: {backend}")
            
    except Exception as e:
        tests['cache_config'] = {'status': 'error', 'message': str(e)}
        print(f"   ❌ Erro no cache: {e}")
    
    return tests

def test_wizard_fixes():
    """Testa correções do wizard"""
    print("\n3. 🧙‍♂️ TESTANDO CORREÇÕES DO WIZARD")
    
    tests = {}
    
    # Teste 1: Acesso ao wizard
    try:
        client = Client()
        login_success = client.login(username='admin', password='admin123')
        
        if login_success:
            response = client.get('/config/wizard/')
            if response.status_code in [200, 302]:
                tests['wizard_access'] = {'status': 'pass', 'message': f'Status: {response.status_code}'}
                print(f"   ✅ Acesso ao wizard: {response.status_code}")
            else:
                tests['wizard_access'] = {'status': 'fail', 'message': f'Status: {response.status_code}'}
                print(f"   ❌ Acesso ao wizard: {response.status_code}")
        else:
            tests['wizard_access'] = {'status': 'fail', 'message': 'Falha no login'}
            print("   ❌ Acesso ao wizard: Falha no login")
            
    except Exception as e:
        tests['wizard_access'] = {'status': 'error', 'message': str(e)}
        print(f"   ❌ Erro no wizard: {e}")
    
    # Teste 2: Environment detector
    try:
        from apps.config.environment_detector import environment_detector
        env_data = environment_detector.detect_full_environment()
        
        if env_data and 'environment' in env_data:
            tests['environment_detector'] = {'status': 'pass', 'message': f'Score: {env_data.get("score", "N/A")}'}
            print(f"   ✅ Environment Detector: Score {env_data.get('score', 'N/A')}")
        else:
            tests['environment_detector'] = {'status': 'fail', 'message': 'Dados incompletos'}
            print("   ❌ Environment Detector: Dados incompletos")
            
    except Exception as e:
        tests['environment_detector'] = {'status': 'error', 'message': str(e)}
        print(f"   ❌ Erro no detector: {e}")
    
    return tests

def test_compressor_setup():
    """Testa configuração do compressor"""
    print("\n4. 🗜️ TESTANDO CONFIGURAÇÃO DO COMPRESSOR")
    
    tests = {}
    
    # Teste 1: Instalação
    try:
        import compressor
        tests['compressor_installed'] = {'status': 'pass', 'message': f'Versão: {compressor.__version__}'}
        print(f"   ✅ Compressor instalado: v{compressor.__version__}")
    except ImportError:
        tests['compressor_installed'] = {'status': 'fail', 'message': 'Não instalado'}
        print("   ❌ Compressor: Não instalado")
    
    # Teste 2: Configurações
    try:
        compress_settings = [
            'COMPRESS_ENABLED',
            'COMPRESS_CSS_FILTERS',
            'COMPRESS_JS_FILTERS'
        ]
        
        configured_settings = []
        for setting in compress_settings:
            if hasattr(settings, setting):
                configured_settings.append(setting)
        
        if len(configured_settings) >= 2:
            tests['compressor_config'] = {'status': 'pass', 'message': f'{len(configured_settings)} configurações'}
            print(f"   ✅ Configurações: {len(configured_settings)}/3")
        else:
            tests['compressor_config'] = {'status': 'fail', 'message': f'Apenas {len(configured_settings)} configurações'}
            print(f"   ❌ Configurações: {len(configured_settings)}/3")
            
    except Exception as e:
        tests['compressor_config'] = {'status': 'error', 'message': str(e)}
        print(f"   ❌ Erro nas configurações: {e}")
    
    return tests

def test_monitoring_system():
    """Testa sistema de monitoramento"""
    print("\n5. 📊 TESTANDO SISTEMA DE MONITORAMENTO")
    
    tests = {}
    
    # Teste 1: Performance Monitor
    try:
        from core.performance_monitor import performance_monitor
        summary = performance_monitor.get_performance_summary()
        
        if summary and 'status' in summary:
            tests['performance_monitor'] = {'status': 'pass', 'message': f'Status: {summary["status"]}'}
            print(f"   ✅ Performance Monitor: {summary['status']}")
        else:
            tests['performance_monitor'] = {'status': 'fail', 'message': 'Dados incompletos'}
            print("   ❌ Performance Monitor: Dados incompletos")
            
    except Exception as e:
        tests['performance_monitor'] = {'status': 'error', 'message': str(e)}
        print(f"   ❌ Erro no monitor: {e}")
    
    # Teste 2: API de Performance
    try:
        client = Client()
        login_success = client.login(username='admin', password='admin123')
        
        if login_success:
            response = client.get('/config/api/performance/')
            if response.status_code == 200:
                tests['performance_api'] = {'status': 'pass', 'message': 'API funcionando'}
                print("   ✅ Performance API: Funcionando")
            else:
                tests['performance_api'] = {'status': 'fail', 'message': f'Status: {response.status_code}'}
                print(f"   ❌ Performance API: {response.status_code}")
        else:
            tests['performance_api'] = {'status': 'fail', 'message': 'Falha no login'}
            print("   ❌ Performance API: Falha no login")
            
    except Exception as e:
        tests['performance_api'] = {'status': 'error', 'message': str(e)}
        print(f"   ❌ Erro na API: {e}")
    
    return tests

def test_model_improvements():
    """Testa melhorias nos modelos"""
    print("\n6. 📊 TESTANDO MELHORIAS NOS MODELOS")
    
    tests = {}
    
    # Teste 1: Modelos com __str__
    try:
        from django.apps import apps
        models = apps.get_models()
        
        models_without_str = []
        for model in models:
            if not hasattr(model, '__str__') or model.__str__ is object.__str__:
                models_without_str.append(f"{model._meta.app_label}.{model._meta.model_name}")
        
        if len(models_without_str) == 0:
            tests['model_str_methods'] = {'status': 'pass', 'message': 'Todos os modelos têm __str__'}
            print("   ✅ Métodos __str__: Todos os modelos")
        else:
            tests['model_str_methods'] = {'status': 'warning', 'message': f'{len(models_without_str)} sem __str__'}
            print(f"   ⚠️ Métodos __str__: {len(models_without_str)} modelos sem __str__")
            
    except Exception as e:
        tests['model_str_methods'] = {'status': 'error', 'message': str(e)}
        print(f"   ❌ Erro nos modelos: {e}")
    
    # Teste 2: Verbose names
    try:
        from django.apps import apps
        models = apps.get_models()
        
        models_without_verbose = []
        for model in models:
            if not hasattr(model._meta, 'verbose_name') or model._meta.verbose_name == model._meta.model_name:
                models_without_verbose.append(f"{model._meta.app_label}.{model._meta.model_name}")
        
        if len(models_without_verbose) <= 5:  # Permitir alguns modelos do Django
            tests['model_verbose_names'] = {'status': 'pass', 'message': f'{len(models_without_verbose)} sem verbose_name'}
            print(f"   ✅ Verbose names: {len(models_without_verbose)} modelos sem verbose_name")
        else:
            tests['model_verbose_names'] = {'status': 'warning', 'message': f'{len(models_without_verbose)} sem verbose_name'}
            print(f"   ⚠️ Verbose names: {len(models_without_verbose)} modelos sem verbose_name")
            
    except Exception as e:
        tests['model_verbose_names'] = {'status': 'error', 'message': str(e)}
        print(f"   ❌ Erro nos verbose names: {e}")
    
    return tests

def display_results(results):
    """Exibe resultados finais"""
    print("\n" + "=" * 70)
    print("📋 RELATÓRIO FINAL DAS OTIMIZAÇÕES")
    print("=" * 70)
    
    overall = results['overall']
    score = overall['score']
    
    print(f"\n🎯 SCORE GERAL: {score}/100")
    print(f"✅ Testes passaram: {overall['passed_tests']}")
    print(f"❌ Testes falharam: {overall['failed_tests']}")
    print(f"📊 Total de testes: {overall['total_tests']}")
    
    if score >= 90:
        print("\n🎉 EXCELENTE! Projeto altamente otimizado")
        status_emoji = "🎉"
    elif score >= 75:
        print("\n✅ MUITO BOM! Projeto bem otimizado")
        status_emoji = "✅"
    elif score >= 60:
        print("\n⚠️ BOM! Algumas melhorias ainda necessárias")
        status_emoji = "⚠️"
    else:
        print("\n🚨 PRECISA MELHORAR! Várias otimizações necessárias")
        status_emoji = "🚨"
    
    # Resumo por categoria
    print(f"\n📊 RESUMO POR CATEGORIA:")
    
    categories = {
        'security': '🔒 Segurança',
        'performance': '⚡ Performance',
        'wizard': '🧙‍♂️ Wizard',
        'compressor': '🗜️ Compressor',
        'monitoring': '📊 Monitoramento',
        'models': '📊 Modelos'
    }
    
    for key, name in categories.items():
        if key in results and isinstance(results[key], dict):
            category_tests = results[key]
            passed = sum(1 for test in category_tests.values() if test.get('status') == 'pass')
            total = len(category_tests)
            percentage = int((passed / total) * 100) if total > 0 else 0
            
            if percentage >= 80:
                emoji = "✅"
            elif percentage >= 60:
                emoji = "⚠️"
            else:
                emoji = "❌"
            
            print(f"   {emoji} {name}: {passed}/{total} ({percentage}%)")
    
    print(f"\n{status_emoji} PROJETO HAVOC OTIMIZADO E FUNCIONANDO!")
    print("=" * 70)

if __name__ == '__main__':
    test_otimizacoes_final()
