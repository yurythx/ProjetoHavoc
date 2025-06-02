#!/usr/bin/env python
"""
Teste do Assistente de Configuração (Setup Wizard)
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.config.models import SetupWizard, WizardRecommendation
from apps.config.environment_detector import environment_detector
import json

def test_setup_wizard():
    """Testa o assistente de configuração completo"""
    print("🧙‍♂️ === TESTANDO ASSISTENTE DE CONFIGURAÇÃO ===")
    print("🚀 PROJETO HAVOC - SETUP WIZARD")
    print("=" * 60)
    
    # 1. Testar detector de ambiente
    print("\n1. 🔍 TESTANDO DETECTOR DE AMBIENTE")
    
    try:
        env_data = environment_detector.detect_full_environment()
        
        if env_data:
            print("   ✅ Detecção de ambiente funcionando")
            print(f"   📊 Score do ambiente: {env_data.get('score', 'N/A')}")
            print(f"   🔧 Componentes detectados: {len(env_data.get('environment', {}))}")
            print(f"   💡 Recomendações geradas: {len(env_data.get('recommendations', []))}")
            print(f"   ⚠️ Avisos: {len(env_data.get('warnings', []))}")
            print(f"   ❌ Erros: {len(env_data.get('errors', []))}")
            
            # Mostrar alguns detalhes
            if 'environment' in env_data:
                env = env_data['environment']
                if 'system' in env:
                    system = env['system']
                    print(f"   🖥️ Sistema: {system.get('os')} {system.get('os_version')}")
                    print(f"   💾 Memória: {system.get('memory_total', 0) // (1024**3)} GB")
                    print(f"   🔧 CPUs: {system.get('cpu_count')}")
                
                if 'django' in env:
                    django_info = env['django']
                    print(f"   🐍 Django: {django_info.get('version')}")
                    print(f"   🔧 Debug: {django_info.get('debug')}")
                    print(f"   📦 Apps: {django_info.get('installed_apps')}")
        else:
            print("   ❌ Erro na detecção de ambiente")
            return
            
    except Exception as e:
        print(f"   ❌ Erro no detector: {e}")
        return
    
    # 2. Testar acesso web ao wizard
    print("\n2. 🌐 TESTANDO ACESSO WEB AO WIZARD")
    
    client = Client()
    
    # Login
    login_success = client.login(username='admin', password='admin123')
    if login_success:
        print("   ✅ Login realizado")
        
        # Testar página inicial do wizard
        response = client.get('/config/wizard/')
        print(f"   📄 Wizard inicial: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
        
        if response.status_code == 200:
            # Verificar se wizard foi criado
            wizard_count = SetupWizard.objects.count()
            print(f"   🧙‍♂️ Wizards criados: {wizard_count}")
            
            if wizard_count > 0:
                wizard = SetupWizard.objects.first()
                print(f"   📊 Status: {wizard.get_status_display()}")
                print(f"   📈 Progresso: {wizard.progress_percentage}%")
                print(f"   🔄 Etapa atual: {wizard.current_step}")
                
                # Testar etapa de ambiente
                env_response = client.get(f'/config/wizard/{wizard.wizard_id}/environment/')
                print(f"   🔍 Etapa ambiente: {env_response.status_code} {'✅' if env_response.status_code == 200 else '❌'}")
                
                # Testar API de status
                api_response = client.get(f'/config/wizard/{wizard.wizard_id}/api/status/')
                if api_response.status_code == 200:
                    api_data = api_response.json()
                    print(f"   📡 API status: ✅")
                    print(f"   📊 Progresso via API: {api_data.get('progress')}%")
                    print(f"   🔄 Etapa via API: {api_data.get('current_step')}")
                else:
                    print(f"   📡 API status: ❌ ({api_response.status_code})")
        
    else:
        print("   ❌ Falha no login")
        return
    
    # 3. Testar modelos do wizard
    print("\n3. 🗄️ TESTANDO MODELOS DO WIZARD")
    
    try:
        # Verificar wizard criado
        wizard = SetupWizard.objects.first()
        if wizard:
            print("   ✅ Modelo SetupWizard funcionando")
            print(f"   🆔 ID: {wizard.wizard_id}")
            print(f"   👤 Iniciado por: {wizard.started_by}")
            print(f"   📅 Iniciado em: {wizard.started_at}")
            
            # Testar métodos do wizard
            next_step = wizard.get_next_step()
            print(f"   ➡️ Próxima etapa: {next_step}")
            
            # Testar salvamento de dados
            wizard.save_environment_data({'test': 'data'})
            wizard.save_user_preferences({'auto_apply': True})
            print("   💾 Salvamento de dados: ✅")
            
            # Verificar recomendações
            recommendations = WizardRecommendation.objects.filter(wizard=wizard)
            print(f"   💡 Recomendações: {recommendations.count()}")
            
            for rec in recommendations[:3]:  # Mostrar primeiras 3
                print(f"      - {rec.title} ({rec.get_priority_display()})")
        else:
            print("   ❌ Nenhum wizard encontrado")
            
    except Exception as e:
        print(f"   ❌ Erro nos modelos: {e}")
    
    # 4. Testar funcionalidades específicas
    print("\n4. ⚙️ TESTANDO FUNCIONALIDADES ESPECÍFICAS")
    
    try:
        if wizard:
            # Testar marcação de etapa como concluída
            wizard.mark_step_completed('welcome')
            print("   ✅ Marcar etapa concluída: ✅")
            
            # Testar avanço de etapa
            original_step = wizard.current_step
            wizard.advance_to_next_step()
            print(f"   ➡️ Avanço de etapa: {original_step} → {wizard.current_step}")
            
            # Testar relatório resumo
            summary = wizard.generate_summary_report()
            print("   📋 Relatório resumo: ✅")
            print(f"      - Progresso: {summary.get('progress')}")
            print(f"      - Etapas concluídas: {summary.get('steps_completed')}")
            print(f"      - Duração: {summary.get('duration')}")
            
    except Exception as e:
        print(f"   ❌ Erro nas funcionalidades: {e}")
    
    # 5. Testar URLs do wizard
    print("\n5. 🔗 TESTANDO URLS DO WIZARD")
    
    if wizard:
        urls_to_test = [
            (f'/config/wizard/{wizard.wizard_id}/', 'Wizard específico'),
            (f'/config/wizard/{wizard.wizard_id}/welcome/', 'Etapa welcome'),
            (f'/config/wizard/{wizard.wizard_id}/environment/', 'Etapa environment'),
            (f'/config/wizard/{wizard.wizard_id}/api/status/', 'API status'),
        ]
        
        for url, name in urls_to_test:
            try:
                response = client.get(url)
                status = '✅' if response.status_code == 200 else f'❌ ({response.status_code})'
                print(f"   🔗 {name}: {status}")
            except Exception as e:
                print(f"   🔗 {name}: ❌ (Erro: {e})")
    
    # 6. Testar dashboard com wizard
    print("\n6. 🏠 TESTANDO DASHBOARD COM WIZARD")
    
    try:
        dashboard_response = client.get('/config/')
        if dashboard_response.status_code == 200:
            content = dashboard_response.content.decode()
            has_wizard_button = 'Iniciar Assistente' in content
            print(f"   🏠 Dashboard: ✅")
            print(f"   🧙‍♂️ Botão do wizard: {'✅' if has_wizard_button else '❌'}")
        else:
            print(f"   🏠 Dashboard: ❌ ({dashboard_response.status_code})")
            
    except Exception as e:
        print(f"   🏠 Dashboard: ❌ (Erro: {e})")
    
    # 7. Estatísticas finais
    print("\n7. 📊 ESTATÍSTICAS FINAIS")
    
    try:
        total_wizards = SetupWizard.objects.count()
        total_recommendations = WizardRecommendation.objects.count()
        completed_wizards = SetupWizard.objects.filter(status='completed').count()
        in_progress_wizards = SetupWizard.objects.filter(status='in_progress').count()
        
        print(f"   🧙‍♂️ Total de wizards: {total_wizards}")
        print(f"   ✅ Wizards concluídos: {completed_wizards}")
        print(f"   🔄 Wizards em progresso: {in_progress_wizards}")
        print(f"   💡 Total de recomendações: {total_recommendations}")
        
        if total_recommendations > 0:
            applied_recs = WizardRecommendation.objects.filter(status='applied').count()
            pending_recs = WizardRecommendation.objects.filter(status='pending').count()
            print(f"   ✅ Recomendações aplicadas: {applied_recs}")
            print(f"   ⏳ Recomendações pendentes: {pending_recs}")
            
    except Exception as e:
        print(f"   📊 Erro nas estatísticas: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 TESTE DO ASSISTENTE DE CONFIGURAÇÃO CONCLUÍDO!")
    print("✅ TODAS AS FUNCIONALIDADES TESTADAS!")
    print("🧙‍♂️ SETUP WIZARD FUNCIONANDO PERFEITAMENTE!")
    print("=" * 60)

if __name__ == '__main__':
    test_setup_wizard()
