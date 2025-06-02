#!/usr/bin/env python
"""
Script para testar performance do sistema Projeto Havoc
"""

import os
import sys
import django
import time
import requests
from concurrent.futures import ThreadPoolExecutor
import statistics

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from apps.accounts.models import Cargo, Departamento, UserAuditLog

User = get_user_model()


class PerformanceTester:
    """Classe para testes de performance"""
    
    def __init__(self):
        self.client = Client()
        self.base_url = 'http://127.0.0.1:8000'
        self.results = {}
    
    def setup_test_data(self):
        """Criar dados de teste"""
        print("🔧 Configurando dados de teste...")
        
        # Criar cargo e departamento
        cargo, _ = Cargo.objects.get_or_create(
            nome='Desenvolvedor Test',
            defaults={'nivel': 3}
        )
        departamento, _ = Departamento.objects.get_or_create(
            nome='TI Test'
        )
        
        # Criar usuário admin
        admin_user, created = User.objects.get_or_create(
            username='admin_test',
            defaults={
                'email': 'admin_test@example.com',
                'is_staff': True,
                'is_active': True,
                'cargo': cargo,
                'departamento': departamento
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        
        # Criar usuários de teste
        users_created = 0
        for i in range(100):
            username = f'user_test_{i}'
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    email=f'user_test_{i}@example.com',
                    password='test123',
                    cargo=cargo,
                    departamento=departamento
                )
                users_created += 1
        
        print(f"✅ {users_created} usuários de teste criados")
        return admin_user
    
    def test_user_list_performance(self, admin_user):
        """Testar performance da listagem de usuários"""
        print("\n📊 Testando performance da listagem de usuários...")
        
        # Login como admin
        self.client.login(username='admin_test', password='admin123')
        
        # Medir tempo de resposta
        times = []
        for i in range(10):
            start_time = time.time()
            response = self.client.get(reverse('accounts:user_list'))
            end_time = time.time()
            
            response_time = end_time - start_time
            times.append(response_time)
            
            if response.status_code != 200:
                print(f"❌ Erro na requisição {i+1}: {response.status_code}")
            else:
                print(f"✅ Requisição {i+1}: {response_time:.3f}s")
        
        # Calcular estatísticas
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        
        self.results['user_list'] = {
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'times': times
        }
        
        print(f"\n📈 Resultados da listagem de usuários:")
        print(f"   Tempo médio: {avg_time:.3f}s")
        print(f"   Tempo mínimo: {min_time:.3f}s")
        print(f"   Tempo máximo: {max_time:.3f}s")
        
        return avg_time < 2.0  # Deve ser menor que 2 segundos
    
    def test_concurrent_requests(self):
        """Testar requisições concorrentes"""
        print("\n🚀 Testando requisições concorrentes...")
        
        def make_request():
            try:
                response = requests.get(f'{self.base_url}/accounts/login/')
                return response.elapsed.total_seconds()
            except Exception as e:
                print(f"❌ Erro na requisição: {e}")
                return None
        
        # Fazer 20 requisições concorrentes
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(20)]
            times = [future.result() for future in futures if future.result()]
            end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = statistics.mean(times) if times else 0
        
        self.results['concurrent'] = {
            'total_time': total_time,
            'avg_time': avg_time,
            'successful_requests': len(times)
        }
        
        print(f"📈 Resultados de requisições concorrentes:")
        print(f"   Tempo total: {total_time:.3f}s")
        print(f"   Tempo médio por requisição: {avg_time:.3f}s")
        print(f"   Requisições bem-sucedidas: {len(times)}/20")
        
        return len(times) >= 18  # Pelo menos 90% de sucesso
    
    def test_database_queries(self, admin_user):
        """Testar otimização de queries do banco"""
        print("\n🗄️ Testando otimização de queries...")
        
        from django.db import connection
        from django.test.utils import override_settings
        
        # Login como admin
        self.client.login(username='admin_test', password='admin123')
        
        # Resetar queries
        connection.queries_log.clear()
        
        # Fazer requisição para listagem
        response = self.client.get(reverse('accounts:user_list'))
        
        # Contar queries
        query_count = len(connection.queries)
        
        self.results['database'] = {
            'query_count': query_count,
            'response_status': response.status_code
        }
        
        print(f"📈 Resultados de queries do banco:")
        print(f"   Número de queries: {query_count}")
        print(f"   Status da resposta: {response.status_code}")
        
        # Mostrar queries se for poucas
        if query_count <= 15:
            print("   Queries executadas:")
            for i, query in enumerate(connection.queries, 1):
                print(f"     {i}. {query['sql'][:100]}...")
        
        return query_count <= 15  # Deve ter no máximo 15 queries
    
    def test_audit_log_performance(self):
        """Testar performance dos logs de auditoria"""
        print("\n📝 Testando performance dos logs de auditoria...")
        
        user = User.objects.filter(username__startswith='user_test_').first()
        if not user:
            print("❌ Nenhum usuário de teste encontrado")
            return False
        
        # Medir tempo para criar logs
        start_time = time.time()
        for i in range(100):
            UserAuditLog.log_action(
                user=user,
                action='test_action',
                ip_address='192.168.1.1',
                details={'test': f'log_{i}'}
            )
        end_time = time.time()
        
        creation_time = end_time - start_time
        
        # Medir tempo para consultar logs
        start_time = time.time()
        logs = list(UserAuditLog.objects.filter(user=user)[:50])
        end_time = time.time()
        
        query_time = end_time - start_time
        
        self.results['audit_log'] = {
            'creation_time': creation_time,
            'query_time': query_time,
            'logs_created': 100,
            'logs_queried': len(logs)
        }
        
        print(f"📈 Resultados dos logs de auditoria:")
        print(f"   Tempo para criar 100 logs: {creation_time:.3f}s")
        print(f"   Tempo para consultar 50 logs: {query_time:.3f}s")
        print(f"   Logs consultados: {len(logs)}")
        
        return creation_time < 1.0 and query_time < 0.5
    
    def cleanup_test_data(self):
        """Limpar dados de teste"""
        print("\n🧹 Limpando dados de teste...")
        
        # Remover usuários de teste
        deleted_users = User.objects.filter(username__startswith='user_test_').delete()
        deleted_admin = User.objects.filter(username='admin_test').delete()
        
        # Remover logs de teste
        deleted_logs = UserAuditLog.objects.filter(action='test_action').delete()
        
        print(f"✅ Limpeza concluída:")
        print(f"   Usuários removidos: {deleted_users[0] + deleted_admin[0]}")
        print(f"   Logs removidos: {deleted_logs[0]}")
    
    def run_all_tests(self):
        """Executar todos os testes"""
        print("🚀 Iniciando testes de performance do sistema Projeto Havoc\n")
        
        try:
            # Setup
            admin_user = self.setup_test_data()
            
            # Executar testes
            tests = [
                ('Listagem de usuários', lambda: self.test_user_list_performance(admin_user)),
                ('Requisições concorrentes', self.test_concurrent_requests),
                ('Otimização de queries', lambda: self.test_database_queries(admin_user)),
                ('Logs de auditoria', self.test_audit_log_performance),
            ]
            
            results = {}
            for test_name, test_func in tests:
                try:
                    result = test_func()
                    results[test_name] = '✅ PASSOU' if result else '❌ FALHOU'
                except Exception as e:
                    results[test_name] = f'❌ ERRO: {e}'
            
            # Relatório final
            print("\n" + "="*60)
            print("📊 RELATÓRIO FINAL DE PERFORMANCE")
            print("="*60)
            
            for test_name, result in results.items():
                print(f"{test_name}: {result}")
            
            # Estatísticas detalhadas
            if self.results:
                print("\n📈 ESTATÍSTICAS DETALHADAS:")
                for test, data in self.results.items():
                    print(f"\n{test.upper()}:")
                    for key, value in data.items():
                        if isinstance(value, float):
                            print(f"  {key}: {value:.3f}")
                        else:
                            print(f"  {key}: {value}")
            
            print("\n✅ Testes de performance concluídos!")
            
        except Exception as e:
            print(f"❌ Erro durante os testes: {e}")
        
        finally:
            # Cleanup
            self.cleanup_test_data()


if __name__ == '__main__':
    tester = PerformanceTester()
    tester.run_all_tests()
