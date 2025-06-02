#!/usr/bin/env python
"""
Sistema de Testes de Penetração Automatizados para Projeto Havoc
Executa testes de segurança abrangentes para identificar vulnerabilidades
"""

import requests
import json
import time
import random
import string
import sys
import os
from urllib.parse import urljoin, urlparse
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
import hashlib

class PenetrationTester:
    def __init__(self, base_url='http://127.0.0.1:8000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.vulnerabilities = []
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'vulnerabilities': 0,
            'warnings': 0
        }
        
    def log_vulnerability(self, severity, test_name, description, details=None):
        """Registra uma vulnerabilidade encontrada"""
        vuln = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'test': test_name,
            'description': description,
            'details': details or {}
        }
        self.vulnerabilities.append(vuln)
        
        if severity in ['CRITICAL', 'HIGH']:
            self.test_results['vulnerabilities'] += 1
        else:
            self.test_results['warnings'] += 1
    
    def test_sql_injection(self):
        """Testa vulnerabilidades de SQL Injection"""
        print("🔍 Testando SQL Injection...")
        
        # Payloads de SQL Injection
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "admin' #",
            "admin'/*",
            "' or 1=1#",
            "' or 1=1--",
            "' or 1=1/*",
            "') or '1'='1--",
            "') or ('1'='1--"
        ]
        
        # URLs para testar
        test_urls = [
            '/accounts/login/',
            '/accounts/register/',
            '/admin/login/',
            '/accounts/ldap/'
        ]
        
        for url in test_urls:
            for payload in sql_payloads:
                try:
                    # Teste via POST
                    data = {
                        'username': payload,
                        'password': payload,
                        'email': f'{payload}@test.com'
                    }
                    
                    response = self.session.post(
                        urljoin(self.base_url, url),
                        data=data,
                        timeout=5,
                        allow_redirects=False
                    )
                    
                    # Verificar sinais de SQL injection
                    if self._check_sql_injection_response(response, payload):
                        self.log_vulnerability(
                            'CRITICAL',
                            'SQL Injection',
                            f'Possível SQL Injection em {url}',
                            {'payload': payload, 'url': url}
                        )
                        
                except Exception as e:
                    continue
        
        print("  ✅ Teste de SQL Injection concluído")
    
    def _check_sql_injection_response(self, response, payload):
        """Verifica se a resposta indica SQL injection"""
        error_indicators = [
            'sql syntax',
            'mysql_fetch',
            'ora-01756',
            'microsoft ole db',
            'odbc sql server driver',
            'sqlite_master',
            'postgresql',
            'warning: mysql',
            'valid mysql result',
            'mysqlclient',
            'database error'
        ]
        
        response_text = response.text.lower()
        return any(indicator in response_text for indicator in error_indicators)
    
    def test_xss_vulnerabilities(self):
        """Testa vulnerabilidades de Cross-Site Scripting (XSS)"""
        print("🔍 Testando XSS...")
        
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            'javascript:alert("XSS")',
            '<iframe src="javascript:alert(\'XSS\')"></iframe>',
            '<body onload=alert("XSS")>',
            '<input onfocus=alert("XSS") autofocus>',
            '<select onfocus=alert("XSS") autofocus>',
            '<textarea onfocus=alert("XSS") autofocus>',
            '<keygen onfocus=alert("XSS") autofocus>',
            '<video><source onerror="alert(\'XSS\')">'
        ]
        
        # URLs para testar
        test_urls = [
            '/accounts/register/',
            '/accounts/profile/',
            '/config/'
        ]
        
        for url in test_urls:
            for payload in xss_payloads:
                try:
                    # Teste via GET
                    params = {'q': payload, 'search': payload}
                    response = self.session.get(
                        urljoin(self.base_url, url),
                        params=params,
                        timeout=5
                    )
                    
                    if payload in response.text and 'text/html' in response.headers.get('content-type', ''):
                        self.log_vulnerability(
                            'HIGH',
                            'XSS Vulnerability',
                            f'Possível XSS em {url}',
                            {'payload': payload, 'url': url}
                        )
                        
                except Exception as e:
                    continue
        
        print("  ✅ Teste de XSS concluído")
    
    def test_authentication_bypass(self):
        """Testa bypass de autenticação"""
        print("🔍 Testando bypass de autenticação...")
        
        # URLs protegidas para testar
        protected_urls = [
            '/accounts/users/',
            '/accounts/profile/',
            '/config/',
            '/admin/',
            '/accounts/test/'
        ]
        
        bypass_techniques = [
            # Headers de bypass
            {'X-Forwarded-For': '127.0.0.1'},
            {'X-Real-IP': '127.0.0.1'},
            {'X-Originating-IP': '127.0.0.1'},
            {'X-Remote-IP': '127.0.0.1'},
            {'X-Client-IP': '127.0.0.1'},
            # User-Agent spoofing
            {'User-Agent': 'GoogleBot/2.1'},
            {'User-Agent': 'Mozilla/5.0 (compatible; Bingbot/2.0)'},
        ]
        
        for url in protected_urls:
            # Teste sem autenticação
            try:
                response = self.session.get(urljoin(self.base_url, url), timeout=5)
                
                if response.status_code == 200 and 'login' not in response.text.lower():
                    self.log_vulnerability(
                        'CRITICAL',
                        'Authentication Bypass',
                        f'URL protegida acessível sem autenticação: {url}',
                        {'url': url, 'status_code': response.status_code}
                    )
                
                # Teste com headers de bypass
                for headers in bypass_techniques:
                    response = self.session.get(
                        urljoin(self.base_url, url),
                        headers=headers,
                        timeout=5
                    )
                    
                    if response.status_code == 200 and 'login' not in response.text.lower():
                        self.log_vulnerability(
                            'HIGH',
                            'Authentication Bypass via Headers',
                            f'Bypass de autenticação com headers em {url}',
                            {'url': url, 'headers': headers}
                        )
                        
            except Exception as e:
                continue
        
        print("  ✅ Teste de bypass de autenticação concluído")
    
    def test_directory_traversal(self):
        """Testa vulnerabilidades de Directory Traversal"""
        print("🔍 Testando Directory Traversal...")
        
        traversal_payloads = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '....//....//....//etc/passwd',
            '..%2F..%2F..%2Fetc%2Fpasswd',
            '..%252F..%252F..%252Fetc%252Fpasswd',
            '..%c0%af..%c0%af..%c0%afetc%c0%afpasswd',
            '../../../../../../../etc/passwd%00.jpg',
            '....\/....\/....\/etc\/passwd',
            'file:///etc/passwd',
            '/var/www/../../etc/passwd'
        ]
        
        # URLs que podem aceitar parâmetros de arquivo
        test_urls = [
            '/static/',
            '/media/',
            '/accounts/avatar/',
            '/config/backup/'
        ]
        
        for url in test_urls:
            for payload in traversal_payloads:
                try:
                    test_url = urljoin(self.base_url, url + payload)
                    response = self.session.get(test_url, timeout=5)
                    
                    # Verificar sinais de directory traversal
                    if self._check_directory_traversal_response(response):
                        self.log_vulnerability(
                            'HIGH',
                            'Directory Traversal',
                            f'Possível Directory Traversal em {url}',
                            {'payload': payload, 'url': url}
                        )
                        
                except Exception as e:
                    continue
        
        print("  ✅ Teste de Directory Traversal concluído")
    
    def _check_directory_traversal_response(self, response):
        """Verifica se a resposta indica directory traversal"""
        indicators = [
            'root:x:0:0:',
            '[boot loader]',
            'localhost',
            '# Copyright',
            'daemon:x:',
            'bin:x:',
            'sys:x:'
        ]
        
        return any(indicator in response.text for indicator in indicators)
    
    def test_csrf_protection(self):
        """Testa proteção CSRF"""
        print("🔍 Testando proteção CSRF...")
        
        # URLs que devem ter proteção CSRF
        csrf_urls = [
            '/accounts/login/',
            '/accounts/register/',
            '/accounts/profile/',
            '/config/',
            '/admin/login/'
        ]
        
        for url in csrf_urls:
            try:
                # Tentar POST sem token CSRF
                response = self.session.post(
                    urljoin(self.base_url, url),
                    data={'test': 'data'},
                    timeout=5
                )
                
                if response.status_code not in [403, 400]:
                    self.log_vulnerability(
                        'MEDIUM',
                        'CSRF Protection Missing',
                        f'Possível falta de proteção CSRF em {url}',
                        {'url': url, 'status_code': response.status_code}
                    )
                    
            except Exception as e:
                continue
        
        print("  ✅ Teste de proteção CSRF concluído")
    
    def test_rate_limiting(self):
        """Testa rate limiting"""
        print("🔍 Testando rate limiting...")
        
        test_url = urljoin(self.base_url, '/accounts/login/')
        
        # Fazer múltiplas requisições rapidamente
        responses = []
        start_time = time.time()
        
        for i in range(150):  # Mais que o limite de 100
            try:
                response = self.session.post(
                    test_url,
                    data={'username': f'test{i}', 'password': 'test'},
                    timeout=2
                )
                responses.append(response.status_code)
                
                if response.status_code == 429:
                    break
                    
            except Exception as e:
                continue
        
        end_time = time.time()
        
        # Verificar se rate limiting foi ativado
        if 429 not in responses:
            self.log_vulnerability(
                'MEDIUM',
                'Rate Limiting Missing',
                'Rate limiting não detectado ou configurado muito alto',
                {
                    'requests_made': len(responses),
                    'time_taken': end_time - start_time,
                    'status_codes': list(set(responses))
                }
            )
        
        print("  ✅ Teste de rate limiting concluído")
    
    def test_information_disclosure(self):
        """Testa vazamento de informações"""
        print("🔍 Testando vazamento de informações...")
        
        # URLs que podem vazar informações
        info_urls = [
            '/admin/',
            '/.env',
            '/settings.py',
            '/config.py',
            '/debug',
            '/phpinfo.php',
            '/server-status',
            '/server-info',
            '/.git/config',
            '/robots.txt',
            '/sitemap.xml',
            '/crossdomain.xml',
            '/clientaccesspolicy.xml'
        ]
        
        sensitive_patterns = [
            'SECRET_KEY',
            'DATABASE_URL',
            'password',
            'api_key',
            'private_key',
            'debug = true',
            'traceback',
            'exception',
            'mysql',
            'postgresql'
        ]
        
        for url in info_urls:
            try:
                response = self.session.get(urljoin(self.base_url, url), timeout=5)
                
                if response.status_code == 200:
                    response_text = response.text.lower()
                    
                    for pattern in sensitive_patterns:
                        if pattern in response_text:
                            self.log_vulnerability(
                                'MEDIUM',
                                'Information Disclosure',
                                f'Possível vazamento de informações em {url}',
                                {'url': url, 'pattern': pattern}
                            )
                            break
                            
            except Exception as e:
                continue
        
        print("  ✅ Teste de vazamento de informações concluído")
    
    def test_security_headers(self):
        """Testa headers de segurança"""
        print("🔍 Testando headers de segurança...")
        
        response = self.session.get(self.base_url, timeout=5)
        headers = response.headers
        
        # Headers de segurança obrigatórios
        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': None,  # Apenas em HTTPS
            'Content-Security-Policy': None
        }
        
        for header, expected in required_headers.items():
            if header not in headers:
                severity = 'HIGH' if header in ['X-Frame-Options', 'X-Content-Type-Options'] else 'MEDIUM'
                self.log_vulnerability(
                    severity,
                    'Missing Security Header',
                    f'Header de segurança ausente: {header}',
                    {'missing_header': header}
                )
            elif expected and isinstance(expected, list):
                if headers[header] not in expected:
                    self.log_vulnerability(
                        'MEDIUM',
                        'Incorrect Security Header',
                        f'Header de segurança incorreto: {header}',
                        {'header': header, 'value': headers[header], 'expected': expected}
                    )
        
        print("  ✅ Teste de headers de segurança concluído")
    
    def run_all_tests(self):
        """Executa todos os testes de penetração"""
        print("🚀 Iniciando Testes de Penetração Automatizados - Projeto Havoc...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Verificar se servidor está acessível
        try:
            response = self.session.get(self.base_url, timeout=5)
            print(f"✅ Servidor acessível em {self.base_url}")
        except Exception as e:
            print(f"❌ Servidor não acessível: {e}")
            return
        
        # Executar todos os testes
        tests = [
            self.test_sql_injection,
            self.test_xss_vulnerabilities,
            self.test_authentication_bypass,
            self.test_directory_traversal,
            self.test_csrf_protection,
            self.test_rate_limiting,
            self.test_information_disclosure,
            self.test_security_headers
        ]
        
        for test in tests:
            try:
                test()
                self.test_results['passed'] += 1
            except Exception as e:
                print(f"  ❌ Erro no teste {test.__name__}: {e}")
                self.test_results['failed'] += 1
            
            self.test_results['total_tests'] += 1
        
        end_time = time.time()
        
        # Gerar relatório
        self.generate_report(end_time - start_time)
    
    def generate_report(self, duration):
        """Gera relatório dos testes"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO DE TESTES DE PENETRAÇÃO")
        print("=" * 60)
        
        print(f"⏱️  Duração: {duration:.2f} segundos")
        print(f"🧪 Total de testes: {self.test_results['total_tests']}")
        print(f"✅ Testes passaram: {self.test_results['passed']}")
        print(f"❌ Testes falharam: {self.test_results['failed']}")
        print(f"🚨 Vulnerabilidades críticas: {self.test_results['vulnerabilities']}")
        print(f"⚠️  Avisos: {self.test_results['warnings']}")
        
        if self.vulnerabilities:
            print("\n🚨 VULNERABILIDADES ENCONTRADAS:")
            print("-" * 40)
            
            for vuln in self.vulnerabilities:
                severity_emoji = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }.get(vuln['severity'], '⚪')
                
                print(f"{severity_emoji} {vuln['severity']} - {vuln['test']}")
                print(f"   📝 {vuln['description']}")
                if vuln['details']:
                    print(f"   🔍 Detalhes: {vuln['details']}")
                print()
        else:
            print("\n🎉 NENHUMA VULNERABILIDADE CRÍTICA ENCONTRADA!")
        
        # Salvar relatório em arquivo
        self.save_report()
        
        print("\n💡 RECOMENDAÇÕES:")
        print("- Execute estes testes regularmente")
        print("- Corrija vulnerabilidades críticas imediatamente")
        print("- Monitore logs de segurança")
        print("- Mantenha sistema atualizado")
    
    def save_report(self):
        """Salva relatório em arquivo JSON"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results,
            'vulnerabilities': self.vulnerabilities,
            'target': self.base_url
        }
        
        # Criar diretório de relatórios se não existir
        reports_dir = 'reports'
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        # Salvar relatório
        filename = f"penetration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Relatório salvo em: {filepath}")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Testes de Penetração Automatizados')
    parser.add_argument('--url', default='http://127.0.0.1:8000', help='URL base do servidor')
    parser.add_argument('--output', help='Arquivo de saída para o relatório')
    
    args = parser.parse_args()
    
    tester = PenetrationTester(args.url)
    tester.run_all_tests()

if __name__ == '__main__':
    main()
