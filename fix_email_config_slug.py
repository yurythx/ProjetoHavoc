#!/usr/bin/env python
"""
Script para diagnosticar e corrigir o problema de slug duplicado no EmailConfig
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.config.models import EmailConfig

def diagnose_and_fix_slug_issue():
    """Diagnostica e corrige problemas de slug duplicado"""
    print("🔍 DIAGNÓSTICO DO PROBLEMA DE SLUG")
    print("=" * 50)
    
    # Listar todas as configurações de email existentes
    email_configs = EmailConfig.objects.all()
    
    print(f"📊 Total de configurações encontradas: {email_configs.count()}")
    print()
    
    if email_configs.count() == 0:
        print("✅ Nenhuma configuração encontrada. O problema pode estar na criação.")
        print("💡 Tentando criar uma configuração de teste...")
        
        try:
            test_config = EmailConfig.objects.create(
                email_host='smtp.gmail.com',
                email_port=587,
                email_host_user='test@gmail.com',
                email_host_password='testpass',
                email_use_tls=True,
                default_from_email='test@gmail.com',
                is_active=False
            )
            print(f"✅ Configuração de teste criada com slug: {test_config.slug}")
            
            # Tentar criar outra para testar o sistema de slug único
            test_config2 = EmailConfig.objects.create(
                email_host='smtp.outlook.com',
                email_port=587,
                email_host_user='test2@outlook.com',
                email_host_password='testpass2',
                email_use_tls=True,
                default_from_email='test2@outlook.com',
                is_active=False
            )
            print(f"✅ Segunda configuração criada com slug: {test_config2.slug}")
            
        except Exception as e:
            print(f"❌ Erro ao criar configuração de teste: {e}")
            return
    
    else:
        print("📋 CONFIGURAÇÕES EXISTENTES:")
        for i, config in enumerate(email_configs, 1):
            print(f"   {i}. ID: {config.id}")
            print(f"      📧 Host: {config.email_host}")
            print(f"      🏷️ Slug: {config.slug}")
            print(f"      ✅ Ativo: {config.is_active}")
            print(f"      📅 Criado: {config.created_at if hasattr(config, 'created_at') else 'N/A'}")
            print()
        
        # Verificar slugs duplicados
        slugs = [config.slug for config in email_configs]
        duplicate_slugs = [slug for slug in set(slugs) if slugs.count(slug) > 1]
        
        if duplicate_slugs:
            print("❌ SLUGS DUPLICADOS ENCONTRADOS:")
            for slug in duplicate_slugs:
                configs_with_slug = email_configs.filter(slug=slug)
                print(f"   🏷️ Slug '{slug}' usado por {configs_with_slug.count()} configurações:")
                for config in configs_with_slug:
                    print(f"      - ID: {config.id}, Host: {config.email_host}")
            
            print("\n🔧 CORRIGINDO SLUGS DUPLICADOS...")
            fix_duplicate_slugs()
        else:
            print("✅ Nenhum slug duplicado encontrado.")
    
    print("\n🧪 TESTANDO CRIAÇÃO DE NOVA CONFIGURAÇÃO...")
    test_new_creation()

def fix_duplicate_slugs():
    """Corrige slugs duplicados"""
    email_configs = EmailConfig.objects.all()
    
    # Agrupar por slug
    slug_groups = {}
    for config in email_configs:
        if config.slug not in slug_groups:
            slug_groups[config.slug] = []
        slug_groups[config.slug].append(config)
    
    # Corrigir duplicados
    for slug, configs in slug_groups.items():
        if len(configs) > 1:
            print(f"   🔧 Corrigindo slug duplicado: {slug}")
            
            # Manter o primeiro, renomear os outros
            for i, config in enumerate(configs[1:], 1):
                import re
                clean_host = re.sub(r'[^a-zA-Z0-9\-]', '-', config.email_host.lower())
                new_slug = f"email-{clean_host}-{i}"
                
                # Garantir que o novo slug seja único
                counter = 1
                while EmailConfig.objects.filter(slug=new_slug).exists():
                    new_slug = f"email-{clean_host}-{i}-{counter}"
                    counter += 1
                
                old_slug = config.slug
                config.slug = new_slug
                config.save()
                print(f"      ✅ ID {config.id}: {old_slug} → {new_slug}")

def test_new_creation():
    """Testa criação de nova configuração"""
    try:
        # Tentar criar uma nova configuração
        new_config = EmailConfig(
            email_host='smtp.test.com',
            email_port=587,
            email_host_user='newtest@test.com',
            email_host_password='newpass',
            email_use_tls=True,
            default_from_email='newtest@test.com',
            is_active=False
        )
        
        # Não salvar ainda, apenas verificar o slug que seria gerado
        print(f"   🏷️ Slug que seria gerado: {new_config.slug or 'Será gerado no save()'}")
        
        # Agora salvar
        new_config.save()
        print(f"   ✅ Nova configuração criada com sucesso!")
        print(f"   🏷️ Slug final: {new_config.slug}")
        print(f"   🔑 ID: {new_config.id}")
        
        # Limpar a configuração de teste
        new_config.delete()
        print(f"   🗑️ Configuração de teste removida")
        
    except Exception as e:
        print(f"   ❌ Erro ao criar nova configuração: {e}")
        print(f"   📝 Tipo do erro: {type(e).__name__}")
        
        # Se for erro de slug duplicado, mostrar detalhes
        if "UNIQUE constraint failed" in str(e):
            print("   💡 Confirmado: Problema de slug duplicado")
            print("   🔧 Executando correção...")
            fix_duplicate_slugs()

def cleanup_test_configs():
    """Remove configurações de teste criadas"""
    print("\n🧹 LIMPANDO CONFIGURAÇÕES DE TESTE...")
    
    test_configs = EmailConfig.objects.filter(
        email_host__in=['smtp.gmail.com', 'smtp.outlook.com', 'smtp.test.com'],
        email_host_user__in=['test@gmail.com', 'test2@outlook.com', 'newtest@test.com']
    )
    
    if test_configs.exists():
        count = test_configs.count()
        test_configs.delete()
        print(f"   🗑️ {count} configuração(ões) de teste removida(s)")
    else:
        print("   ✅ Nenhuma configuração de teste encontrada")

def show_final_status():
    """Mostra status final"""
    print("\n📊 STATUS FINAL:")
    print("=" * 30)
    
    email_configs = EmailConfig.objects.all()
    print(f"📧 Total de configurações: {email_configs.count()}")
    
    if email_configs.exists():
        print("📋 Configurações existentes:")
        for config in email_configs:
            print(f"   🏷️ {config.slug} - {config.email_host} ({'✅ Ativo' if config.is_active else '❌ Inativo'})")
    
    print("\n🎉 Diagnóstico e correção concluídos!")
    print("💡 Agora você pode tentar criar uma nova configuração de email.")

if __name__ == "__main__":
    try:
        diagnose_and_fix_slug_issue()
        cleanup_test_configs()
        show_final_status()
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
