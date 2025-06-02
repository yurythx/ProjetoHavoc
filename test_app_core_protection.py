#!/usr/bin/env python
"""
Teste específico para proteção de apps core
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.exceptions import ValidationError
from django.db import transaction
from apps.config.models import AppConfig

def test_app_core_protection():
    """Testa proteção de apps core"""
    print("🔒 === TESTANDO PROTEÇÃO DE APPS CORE ===")
    
    # Buscar apps core
    core_apps = AppConfig.objects.filter(is_core=True)
    
    print(f"📊 Apps core encontrados: {core_apps.count()}")
    for app in core_apps:
        print(f"   - {app.name} ({app.label}) - Ativo: {app.is_active}")
    
    # Testar cada app core
    for app in core_apps:
        print(f"\n🧪 Testando proteção do app: {app.name}")
        
        # Salvar estado original
        original_active = app.is_active
        
        try:
            # Tentar desativar via save()
            print("   📝 Teste 1: Tentando desativar via save()...")
            app.is_active = False
            app.save()
            
            # Verificar se ainda está ativo
            app.refresh_from_db()
            if app.is_active:
                print("   ✅ Proteção via save() funcionando")
            else:
                print("   ❌ ERRO: App core foi desativado via save()")
            
            # Tentar desativar via clean() + save()
            print("   📝 Teste 2: Tentando desativar via clean()...")
            app.is_active = False
            try:
                app.clean()
                print("   ❌ ERRO: clean() não levantou ValidationError")
            except ValidationError as e:
                print(f"   ✅ clean() protegeu corretamente: {e}")
            
            # Tentar desativar via update()
            print("   📝 Teste 3: Tentando desativar via update()...")
            AppConfig.objects.filter(pk=app.pk).update(is_active=False)
            app.refresh_from_db()
            if not app.is_active:
                print("   ❌ ERRO CRÍTICO: App core foi desativado via update() - bypass de proteção!")
                # Reativar
                app.is_active = True
                app.save()
            else:
                print("   ✅ Proteção via update() funcionando")
                
        except Exception as e:
            print(f"   ❌ ERRO no teste: {e}")
        
        finally:
            # Restaurar estado original
            app.is_active = original_active
            app.save()
    
    print("\n" + "="*50)
    print("📋 RESUMO DOS TESTES DE PROTEÇÃO")
    
    # Verificar estado final
    final_core_apps = AppConfig.objects.filter(is_core=True)
    inactive_core = final_core_apps.filter(is_active=False)
    
    if inactive_core.exists():
        print("❌ ERRO CRÍTICO: Apps core inativos encontrados:")
        for app in inactive_core:
            print(f"   - {app.name}: INATIVO")
    else:
        print("✅ Todos os apps core estão ativos")
    
    print(f"\n📊 ESTATÍSTICAS FINAIS:")
    print(f"   🔧 Apps core: {final_core_apps.count()}")
    print(f"   ✅ Ativos: {final_core_apps.filter(is_active=True).count()}")
    print(f"   ❌ Inativos: {inactive_core.count()}")

if __name__ == '__main__':
    test_app_core_protection()
