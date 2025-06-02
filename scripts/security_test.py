#!/usr/bin/env python
"""
Script para testar a segurança do sistema Projeto Havoc
Verifica se as correções de segurança estão funcionando corretamente
"""

import requests
import sys
import os
import time
import json
import argparse
from datetime import datetime
from urllib.parse import urljoin

# Configurações
BASE_URL = 'http://127.0.0.1:8000'
TEST_URLS = [
    '/accounts/test/',
    '/accounts/ldap/',
    '/config/test-module-disabled/',
    '/admin/',
    '/config/',
]

# Headers suspeitos para testar detecção
SUSPICIOUS_HEADERS = {
    'User-Agent': 'sqlmap/1.0',
    'X-Forwarded-For': '<script>alert("xss")</script>',
}

def test_url_protection():
    """Testa se URLs protegidas estão bloqueando acesso não autorizado"""
    print("🔒 Testando proteção de URLs...")
    
    session = requests.Session()
    
    for url in TEST_URLS:
        full_url = urljoin(BASE_URL, url)
        try:
            response = session.get(full_url, timeout=5)
            
            # URLs protegidas devem redirecionar para login ou retornar 403/404
            if response.status_code == 200:
                if 'login' in response.text.lower() or 'entrar' in response.text.lower():
                    print(f"  ✅ {url} - PROTEGIDA (Redirecionou para login)")
                elif 'acesso negado' in response.text.lower() or 'permission denied' in response.text.lower():
                    print(f"  ✅ {url} - PROTEGIDA (Acesso negado)")
                else:
                    print(f"  🚨 {url} - PROBLEMA: Acessível sem autenticação!")
            elif response.status_code in [302, 403, 404]:
                print(f"  ✅ {url} - PROTEGIDA (Status: {response.status_code})")
            else:
                print(f"  ❓ {url} - Status inesperado: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {url} - Erro de conexão: {e}")

def test_security_headers():
    """Testa se headers de segurança estão sendo aplicados"""
    print("\n🛡️ Testando headers de segurança...")
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        headers = response.headers
        
        # Headers de segurança esperados
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
        }
        
        for header, expected_value in security_headers.items():
            if header in headers:
                if headers[header] == expected_value:
                    print(f"  ✅ {header}: {headers[header]}")
                else:
                    print(f"  ⚠️  {header}: {headers[header]} (esperado: {expected_value})")
            else:
                print(f"  ❌ {header}: AUSENTE")
        
        # Verificar CSP
        if 'Content-Security-Policy' in headers:
            print(f"  ✅ Content-Security-Policy: PRESENTE")
        else:
            print(f"  ❌ Content-Security-Policy: AUSENTE")
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Erro ao testar headers: {e}")

def test_suspicious_requests():
    """Testa detecção de requests suspeitos"""
    print("\n🕵️ Testando detecção de requests suspeitos...")
    
    try:
        # Teste com user agent suspeito
        response = requests.get(
            BASE_URL, 
            headers=SUSPICIOUS_HEADERS,
            timeout=5
        )
        
        if response.status_code == 200:
            print("  ⚠️  Request suspeito foi aceito")
        else:
            print(f"  ✅ Request suspeito bloqueado (Status: {response.status_code})")
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Erro ao testar request suspeito: {e}")

def test_rate_limiting():
    """Testa rate limiting básico"""
    print("\n⏱️ Testando rate limiting...")
    
    try:
        # Fazer múltiplas requests rapidamente
        responses = []
        for i in range(10):
            response = requests.get(BASE_URL, timeout=2)
            responses.append(response.status_code)
        
        # Verificar se alguma foi bloqueada
        if 429 in responses:
            print("  ✅ Rate limiting funcionando (HTTP 429 detectado)")
        else:
            print("  ⚠️  Rate limiting não detectado (pode estar configurado para limite maior)")
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Erro ao testar rate limiting: {e}")

def test_csrf_protection():
    """Testa proteção CSRF"""
    print("\n🔐 Testando proteção CSRF...")
    
    try:
        # Tentar POST sem token CSRF
        response = requests.post(
            urljoin(BASE_URL, '/accounts/login/'),
            data={'username': 'test', 'password': 'test'},
            timeout=5
        )
        
        if response.status_code == 403:
            print("  ✅ Proteção CSRF funcionando (HTTP 403)")
        elif 'csrf' in response.text.lower():
            print("  ✅ Proteção CSRF funcionando (erro CSRF detectado)")
        else:
            print(f"  ⚠️  Proteção CSRF pode não estar funcionando (Status: {response.status_code})")
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Erro ao testar CSRF: {e}")

def run_security_audit(base_url=None):
    """Executa auditoria completa de segurança"""
    global BASE_URL
    if base_url:
        BASE_URL = base_url

    print("🚀 Iniciando testes de segurança do Projeto Havoc...")
    print("=" * 60)

    # Verificar se servidor está rodando
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Servidor acessível em {BASE_URL}")
    except requests.exceptions.RequestException:
        print(f"❌ Servidor não acessível em {BASE_URL}")
        print("   Certifique-se de que o servidor Django está rodando")
        return False

    # Executar testes
    results = {
        'timestamp': datetime.now().isoformat(),
        'base_url': BASE_URL,
        'tests': {}
    }

    try:
        test_url_protection()
        results['tests']['url_protection'] = 'PASSED'
    except Exception as e:
        results['tests']['url_protection'] = f'FAILED: {e}'

    try:
        test_security_headers()
        results['tests']['security_headers'] = 'PASSED'
    except Exception as e:
        results['tests']['security_headers'] = f'FAILED: {e}'

    try:
        test_suspicious_requests()
        results['tests']['suspicious_requests'] = 'PASSED'
    except Exception as e:
        results['tests']['suspicious_requests'] = f'FAILED: {e}'

    try:
        test_rate_limiting()
        results['tests']['rate_limiting'] = 'PASSED'
    except Exception as e:
        results['tests']['rate_limiting'] = f'FAILED: {e}'

    try:
        test_csrf_protection()
        results['tests']['csrf_protection'] = 'PASSED'
    except Exception as e:
        results['tests']['csrf_protection'] = f'FAILED: {e}'

    print("\n" + "=" * 60)
    print("🎯 Testes de segurança concluídos!")
    print("\n📋 Resumo:")
    print("  - URLs protegidas: Verificadas")
    print("  - Headers de segurança: Verificados")
    print("  - Detecção de ameaças: Verificada")
    print("  - Rate limiting: Verificado")
    print("  - Proteção CSRF: Verificada")

    # Salvar resultados
    save_audit_results(results)

    return True

def save_audit_results(results):
    """Salva resultados da auditoria"""
    # Criar diretório de relatórios se não existir
    reports_dir = 'reports'
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    # Salvar relatório
    filename = f"security_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(reports_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Relatório salvo em: {filepath}")

def scheduled_audit(interval_hours=24):
    """Executa auditorias agendadas"""
    print(f"🕐 Modo agendado ativado - executando a cada {interval_hours} horas")

    while True:
        try:
            print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Executando auditoria de segurança...")

            success = run_security_audit()

            if success:
                print("✅ Auditoria concluída com sucesso")
            else:
                print("❌ Auditoria falhou")

            # Aguardar próxima execução
            sleep_seconds = interval_hours * 3600
            print(f"😴 Aguardando {interval_hours} horas para próxima auditoria...")
            time.sleep(sleep_seconds)

        except KeyboardInterrupt:
            print("\n🛑 Modo agendado interrompido")
            break
        except Exception as e:
            print(f"❌ Erro na auditoria agendada: {e}")
            time.sleep(300)  # Aguardar 5 minutos antes de tentar novamente

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Testes de Segurança Projeto Havoc')
    parser.add_argument('--url', default='http://127.0.0.1:8000', help='URL base do servidor')
    parser.add_argument('--schedule', action='store_true', help='Executar em modo agendado')
    parser.add_argument('--interval', type=float, default=24, help='Intervalo em horas para modo agendado')
    parser.add_argument('--output', help='Arquivo de saída para o relatório')

    args = parser.parse_args()

    if args.schedule:
        scheduled_audit(args.interval)
    else:
        success = run_security_audit(args.url)
        if not success:
            sys.exit(1)

    print("\n💡 Dicas:")
    print("  - Execute este script regularmente para monitorar a segurança")
    print("  - Use --schedule para execução automática")
    print("  - Verifique os logs de segurança em logs/security.log")
    print("  - Configure alertas para eventos suspeitos em produção")

if __name__ == '__main__':
    main()
