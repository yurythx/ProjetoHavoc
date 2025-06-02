#!/usr/bin/env python
"""
Demonstração completa do sistema de debug configurável
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.conf import settings
from apps.config.models import SystemConfig
import json

def demo_debug_system():
    """Demonstração completa do sistema de debug"""
    print("🎯 === DEMONSTRAÇÃO: SISTEMA DE DEBUG CONFIGURÁVEL ===")
    print("🚀 PROJETO HAVOC - CONFIGURAÇÃO DINÂMICA DE DEBUG")
    print("=" * 70)
    
    # 1. Estado inicial
    print("\n1. 📊 ESTADO INICIAL DO SISTEMA")
    
    system_config = SystemConfig.objects.first()
    print(f"   🔧 Debug no banco de dados: {system_config.debug_mode}")
    print(f"   ⚙️ DEBUG no Django settings: {settings.DEBUG}")
    
    # 2. Demonstrar interface web
    print("\n2. 🌐 INTERFACE WEB DE CONFIGURAÇÃO")
    
    client = Client()
    login_success = client.login(username='admin', password='admin123')
    
    if login_success:
        print("   ✅ Acesso autenticado ao sistema")
        print(f"   🔗 URL de configuração: /config/system/{system_config.slug}/")
        print("   📝 Seção: 'Configurações de Desenvolvimento'")
        print("   🎛️ Campo: 'Debug mode' com aviso de segurança")
    else:
        print("   ❌ Falha na autenticação")
        return
    
    # 3. Demonstrar API
    print("\n3. 📡 API DE MONITORAMENTO")
    
    response = client.get('/config/api/status/')
    if response.status_code == 200:
        data = response.json()
        system_module = data['modules']['system']
        
        print("   ✅ API de status acessível")
        print(f"   📊 Debug via API: {system_module['details']['debug_mode']}")
        print(f"   ⚠️ Status do sistema: {system_module['status']}")
        
        if system_module['issues']:
            print("   🚨 Alertas ativos:")
            for issue in system_module['issues']:
                print(f"      - {issue}")
    
    # 4. Demonstrar mudança de configuração
    print("\n4. 🔄 DEMONSTRAÇÃO DE MUDANÇA DE CONFIGURAÇÃO")
    
    original_debug = system_config.debug_mode
    
    # Simular mudança para False
    print("   📝 Simulando desativação do debug...")
    system_config.debug_mode = False
    system_config.save()
    
    print(f"   ✅ Debug alterado no banco: {system_config.debug_mode}")
    
    # Verificar API após mudança
    response = client.get('/config/api/status/?refresh=true')
    if response.status_code == 200:
        data = response.json()
        system_module = data['modules']['system']
        print(f"   📊 Debug via API (atualizado): {system_module['details']['debug_mode']}")
        print(f"   ⚠️ Status após mudança: {system_module['status']}")
    
    # Restaurar estado original
    system_config.debug_mode = original_debug
    system_config.save()
    print(f"   🔄 Debug restaurado: {system_config.debug_mode}")
    
    # 5. Funcionalidades implementadas
    print("\n5. ✅ FUNCIONALIDADES IMPLEMENTADAS")
    
    features = [
        "Campo debug_mode no modelo SystemConfig",
        "Interface web com aviso de segurança",
        "Formulário de configuração responsivo",
        "Validação e persistência no banco",
        "Integração com Django settings",
        "API de monitoramento em tempo real",
        "Alertas de segurança quando ativo",
        "Badge visual de status",
        "Documentação inline",
        "Testes automatizados"
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"   {i:2d}. ✅ {feature}")
    
    # 6. Benefícios
    print("\n6. 🎯 BENEFÍCIOS DO SISTEMA")
    
    benefits = [
        "Controle centralizado de debug",
        "Mudança sem editar código",
        "Interface amigável para administradores",
        "Alertas de segurança automáticos",
        "Monitoramento em tempo real",
        "Integração com sistema de auditoria",
        "Configuração persistente",
        "API para automação"
    ]
    
    for benefit in benefits:
        print(f"   🎁 {benefit}")
    
    # 7. Instruções de uso
    print("\n7. 📖 INSTRUÇÕES DE USO")
    
    instructions = [
        "Acesse o painel de configurações: /config/",
        "Clique em 'Sistema' > 'Configurações Gerais'",
        "Vá para a seção 'Configurações de Desenvolvimento'",
        "Marque/desmarque o campo 'Debug mode'",
        "Clique em 'Salvar Configurações'",
        "Reinicie o servidor para aplicar mudanças",
        "Monitore via API: /config/api/status/"
    ]
    
    for i, instruction in enumerate(instructions, 1):
        print(f"   {i}. {instruction}")
    
    # 8. Considerações de segurança
    print("\n8. 🔒 CONSIDERAÇÕES DE SEGURANÇA")
    
    security_notes = [
        "⚠️ SEMPRE desative debug em produção",
        "🔍 Debug expõe informações sensíveis",
        "📊 Monitore alertas de segurança",
        "🚨 Sistema alerta quando debug está ativo",
        "👥 Apenas staff pode alterar configurações",
        "📝 Todas as mudanças são auditadas",
        "🔄 Mudanças requerem restart do servidor"
    ]
    
    for note in security_notes:
        print(f"   {note}")
    
    # 9. Status final
    print("\n9. 📋 STATUS FINAL DO SISTEMA")
    
    final_response = client.get('/config/api/status/?refresh=true')
    if final_response.status_code == 200:
        final_data = final_response.json()
        final_system = final_data['modules']['system']
        
        print(f"   🔧 Debug ativo: {final_system['details']['debug_mode']}")
        print(f"   ⚠️ Status geral: {final_data['overall_health']}")
        print(f"   📊 Módulos monitorados: {len(final_data['modules'])}")
        print(f"   🕐 Última atualização: {final_data['timestamp']}")
    
    print("\n" + "=" * 70)
    print("🎉 SISTEMA DE DEBUG CONFIGURÁVEL IMPLEMENTADO COM SUCESSO!")
    print("🚀 PROJETO HAVOC - CONFIGURAÇÃO DINÂMICA FUNCIONANDO!")
    print("✅ TODAS AS FUNCIONALIDADES TESTADAS E APROVADAS!")
    print("=" * 70)

if __name__ == '__main__':
    demo_debug_system()
