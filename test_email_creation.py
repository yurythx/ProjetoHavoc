#!/usr/bin/env python
"""
Script para testar a criação de EmailConfig e identificar o problema
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.config.models import EmailConfig
from apps.config.forms import EmailConfigForm

def test_direct_creation():
    """Testa criação direta via modelo"""
    print("🧪 TESTE 1: Criação direta via modelo")
    print("=" * 40)
    
    try:
        # Criar configuração diretamente
        config = EmailConfig(
            email_host='smtp.outlook.com',
            email_port=587,
            email_host_user='teste@outlook.com',
            email_host_password='senha123',
            email_use_tls=True,
            default_from_email='teste@outlook.com',
            is_active=True
        )
        
        print(f"📧 Host: {config.email_host}")
        print(f"🏷️ Slug antes do save: {config.slug}")
        
        # Salvar
        config.save()
        
        print(f"✅ Criação bem-sucedida!")
        print(f"🏷️ Slug após save: {config.slug}")
        print(f"🔑 ID: {config.id}")
        
        # Limpar
        config.delete()
        print(f"🗑️ Configuração removida")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na criação direta: {e}")
        print(f"📝 Tipo: {type(e).__name__}")
        return False

def test_form_creation():
    """Testa criação via formulário"""
    print("\n🧪 TESTE 2: Criação via formulário")
    print("=" * 40)
    
    try:
        # Dados do formulário
        form_data = {
            'email_host': 'smtp.gmail.com',
            'email_port': 587,
            'email_host_user': 'teste@gmail.com',
            'email_host_password': 'senha456',
            'email_use_tls': True,
            'default_from_email': 'teste@gmail.com',
            'is_active': True,
            'is_default': False
        }
        
        print(f"📧 Dados do formulário: {form_data['email_host']}")
        
        # Criar formulário
        form = EmailConfigForm(data=form_data)
        
        print(f"✅ Formulário válido: {form.is_valid()}")
        
        if not form.is_valid():
            print(f"❌ Erros do formulário: {form.errors}")
            return False
        
        # Salvar via formulário
        config = form.save()
        
        print(f"✅ Criação via formulário bem-sucedida!")
        print(f"🏷️ Slug: {config.slug}")
        print(f"🔑 ID: {config.id}")
        
        # Limpar
        config.delete()
        print(f"🗑️ Configuração removida")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na criação via formulário: {e}")
        print(f"📝 Tipo: {type(e).__name__}")
        return False

def test_multiple_creation():
    """Testa criação de múltiplas configurações"""
    print("\n🧪 TESTE 3: Criação múltipla para testar slugs únicos")
    print("=" * 50)
    
    configs_created = []
    
    try:
        # Criar várias configurações com hosts similares
        hosts = [
            'smtp.test1.com',
            'smtp.test2.com', 
            'smtp.test1.com',  # Mesmo host para testar slug único
            'smtp-test1-com',  # Host que geraria slug similar
        ]
        
        for i, host in enumerate(hosts, 1):
            print(f"\n📧 Criando configuração {i}: {host}")
            
            config = EmailConfig(
                email_host=host,
                email_port=587,
                email_host_user=f'teste{i}@{host}',
                email_host_password=f'senha{i}',
                email_use_tls=True,
                default_from_email=f'teste{i}@{host}',
                is_active=True
            )
            
            config.save()
            configs_created.append(config)
            
            print(f"   ✅ Criado com slug: {config.slug}")
        
        print(f"\n✅ Todas as {len(configs_created)} configurações criadas com sucesso!")
        
        # Mostrar todos os slugs
        print("\n📋 Slugs gerados:")
        for config in configs_created:
            print(f"   🏷️ {config.slug} - {config.email_host}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na criação múltipla: {e}")
        print(f"📝 Tipo: {type(e).__name__}")
        return False
        
    finally:
        # Limpar todas as configurações criadas
        print(f"\n🗑️ Limpando {len(configs_created)} configurações...")
        for config in configs_created:
            try:
                config.delete()
                print(f"   ✅ Removido: {config.slug}")
            except:
                pass

def check_existing_configs():
    """Verifica configurações existentes"""
    print("\n📊 CONFIGURAÇÕES EXISTENTES:")
    print("=" * 30)
    
    configs = EmailConfig.objects.all()
    
    if configs.exists():
        for config in configs:
            print(f"🏷️ {config.slug}")
            print(f"   📧 Host: {config.email_host}")
            print(f"   🔑 ID: {config.id}")
            print(f"   ✅ Ativo: {config.is_active}")
            print()
    else:
        print("ℹ️ Nenhuma configuração encontrada")

def simulate_web_creation():
    """Simula o processo que acontece na web"""
    print("\n🌐 TESTE 4: Simulação do processo web")
    print("=" * 40)
    
    try:
        # Simular dados que viriam do POST
        post_data = {
            'email_host': 'smtp.hotmail.com',
            'email_port': '587',
            'email_host_user': 'yurymenezes@hotmail.com',
            'email_host_password': 'minhasenha',
            'email_use_tls': 'on',  # Como vem do checkbox
            'default_from_email': 'yurymenezes@hotmail.com',
            'is_active': 'on',  # Como vem do checkbox
            'is_default': 'on'  # Como vem do checkbox
        }
        
        print(f"📧 Simulando POST com: {post_data['email_host']}")
        
        # Criar formulário como na view
        form = EmailConfigForm(data=post_data)
        
        print(f"✅ Formulário válido: {form.is_valid()}")
        
        if not form.is_valid():
            print(f"❌ Erros: {form.errors}")
            return False
        
        # Salvar como na view
        email_config = form.save()
        
        print(f"✅ Configuração criada via simulação web!")
        print(f"🏷️ Slug: {email_config.slug}")
        print(f"🔑 ID: {email_config.id}")
        print(f"📧 Host: {email_config.email_host}")
        print(f"✅ Ativo: {email_config.is_active}")
        print(f"⭐ Padrão: {email_config.is_default}")
        
        # Limpar
        email_config.delete()
        print(f"🗑️ Configuração removida")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na simulação web: {e}")
        print(f"📝 Tipo: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔬 TESTE COMPLETO DE CRIAÇÃO DE EMAIL CONFIG")
    print("=" * 60)
    
    # Verificar estado inicial
    check_existing_configs()
    
    # Executar testes
    tests = [
        test_direct_creation,
        test_form_creation,
        test_multiple_creation,
        simulate_web_creation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erro no teste {test.__name__}: {e}")
            results.append(False)
    
    # Resumo
    print(f"\n📊 RESUMO DOS TESTES:")
    print("=" * 30)
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Testes passaram: {passed}/{total}")
    
    if passed == total:
        print("🎉 Todos os testes passaram! O problema pode estar na interface web.")
    else:
        print("❌ Alguns testes falharam. Há um problema no código.")
    
    # Estado final
    check_existing_configs()
