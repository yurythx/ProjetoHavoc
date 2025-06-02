"""
Comando para executar testes de performance
"""

from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import connection
import time
import statistics

from apps.accounts.models import Cargo, Departamento, UserAuditLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Executa testes de performance do sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Número de usuários de teste a criar'
        )
        parser.add_argument(
            '--iterations',
            type=int,
            default=5,
            help='Número de iterações para cada teste'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Limpar dados de teste após execução'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando testes de performance...\n')
        )
        
        # Configurações
        num_users = options['users']
        iterations = options['iterations']
        cleanup = options['cleanup']
        
        try:
            # Setup
            admin_user = self.setup_test_data(num_users)
            
            # Executar testes
            self.test_user_list_performance(admin_user, iterations)
            self.test_database_optimization(admin_user)
            self.test_audit_log_performance()
            self.test_cache_performance(admin_user)
            
            self.stdout.write(
                self.style.SUCCESS('\n✅ Todos os testes concluídos!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro durante os testes: {e}')
            )
        
        finally:
            if cleanup:
                self.cleanup_test_data()
    
    def setup_test_data(self, num_users):
        """Criar dados de teste"""
        self.stdout.write('🔧 Configurando dados de teste...')
        
        # Criar cargo e departamento
        cargo, _ = Cargo.objects.get_or_create(
            nome='Desenvolvedor Performance',
            defaults={'nivel': 3}
        )
        departamento, _ = Departamento.objects.get_or_create(
            nome='TI Performance'
        )
        
        # Criar usuário admin
        admin_user, created = User.objects.get_or_create(
            username='admin_perf',
            defaults={
                'email': 'admin_perf@example.com',
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
        for i in range(num_users):
            username = f'perf_user_{i}'
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    email=f'perf_user_{i}@example.com',
                    password='test123',
                    cargo=cargo,
                    departamento=departamento
                )
                users_created += 1
        
        self.stdout.write(f'✅ {users_created} usuários de teste criados')
        return admin_user
    
    def test_user_list_performance(self, admin_user, iterations):
        """Testar performance da listagem de usuários"""
        self.stdout.write('\n📊 Testando performance da listagem de usuários...')
        
        client = Client()
        client.force_login(admin_user)
        
        times = []
        for i in range(iterations):
            # Limpar cache para teste real
            from django.core.cache import cache
            cache.clear()
            
            start_time = time.time()
            response = client.get(reverse('accounts:user_list'))
            end_time = time.time()
            
            response_time = end_time - start_time
            times.append(response_time)
            
            if response.status_code == 200:
                self.stdout.write(f'  ✅ Iteração {i+1}: {response_time:.3f}s')
            else:
                self.stdout.write(f'  ❌ Iteração {i+1}: Erro {response.status_code}')
        
        # Estatísticas
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            
            self.stdout.write(f'\n📈 Resultados:')
            self.stdout.write(f'   Tempo médio: {avg_time:.3f}s')
            self.stdout.write(f'   Tempo mínimo: {min_time:.3f}s')
            self.stdout.write(f'   Tempo máximo: {max_time:.3f}s')
            
            if avg_time < 1.0:
                self.stdout.write(self.style.SUCCESS('   ✅ Performance EXCELENTE'))
            elif avg_time < 2.0:
                self.stdout.write(self.style.WARNING('   ⚠️ Performance BOA'))
            else:
                self.stdout.write(self.style.ERROR('   ❌ Performance RUIM'))
    
    def test_database_optimization(self, admin_user):
        """Testar otimização de queries"""
        self.stdout.write('\n🗄️ Testando otimização de queries...')
        
        client = Client()
        client.force_login(admin_user)
        
        # Resetar log de queries
        connection.queries_log.clear()
        
        # Fazer requisição
        response = client.get(reverse('accounts:user_list'))
        
        # Analisar queries
        query_count = len(connection.queries)
        
        self.stdout.write(f'📈 Resultados:')
        self.stdout.write(f'   Número de queries: {query_count}')
        self.stdout.write(f'   Status da resposta: {response.status_code}')
        
        # Analisar queries lentas
        slow_queries = [q for q in connection.queries if float(q['time']) > 0.1]
        if slow_queries:
            self.stdout.write(f'   ⚠️ Queries lentas (>100ms): {len(slow_queries)}')
            for query in slow_queries[:3]:  # Mostrar apenas as 3 primeiras
                self.stdout.write(f'     {query["time"]}s: {query["sql"][:100]}...')
        
        # Avaliar performance
        if query_count <= 10:
            self.stdout.write(self.style.SUCCESS('   ✅ Otimização EXCELENTE'))
        elif query_count <= 20:
            self.stdout.write(self.style.WARNING('   ⚠️ Otimização BOA'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ Possível problema N+1'))
    
    def test_audit_log_performance(self):
        """Testar performance dos logs de auditoria"""
        self.stdout.write('\n📝 Testando performance dos logs de auditoria...')
        
        user = User.objects.filter(username__startswith='perf_user_').first()
        if not user:
            self.stdout.write(self.style.ERROR('   ❌ Nenhum usuário de teste encontrado'))
            return
        
        # Teste de criação de logs
        start_time = time.time()
        for i in range(50):
            UserAuditLog.log_action(
                user=user,
                action='performance_test',
                ip_address='192.168.1.1',
                details={'iteration': i}
            )
        creation_time = time.time() - start_time
        
        # Teste de consulta de logs
        start_time = time.time()
        logs = list(UserAuditLog.objects.filter(user=user)[:25])
        query_time = time.time() - start_time
        
        self.stdout.write(f'📈 Resultados:')
        self.stdout.write(f'   Criação de 50 logs: {creation_time:.3f}s')
        self.stdout.write(f'   Consulta de 25 logs: {query_time:.3f}s')
        self.stdout.write(f'   Logs encontrados: {len(logs)}')
        
        if creation_time < 0.5 and query_time < 0.1:
            self.stdout.write(self.style.SUCCESS('   ✅ Performance EXCELENTE'))
        elif creation_time < 1.0 and query_time < 0.2:
            self.stdout.write(self.style.WARNING('   ⚠️ Performance BOA'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ Performance RUIM'))
    
    def test_cache_performance(self, admin_user):
        """Testar performance do cache"""
        self.stdout.write('\n💾 Testando performance do cache...')
        
        from django.core.cache import cache
        client = Client()
        client.force_login(admin_user)
        
        # Primeira requisição (sem cache)
        cache.clear()
        start_time = time.time()
        response1 = client.get(reverse('accounts:user_list'))
        time_without_cache = time.time() - start_time
        
        # Segunda requisição (com cache)
        start_time = time.time()
        response2 = client.get(reverse('accounts:user_list'))
        time_with_cache = time.time() - start_time
        
        # Calcular melhoria
        if time_without_cache > 0:
            improvement = ((time_without_cache - time_with_cache) / time_without_cache) * 100
        else:
            improvement = 0
        
        self.stdout.write(f'📈 Resultados:')
        self.stdout.write(f'   Sem cache: {time_without_cache:.3f}s')
        self.stdout.write(f'   Com cache: {time_with_cache:.3f}s')
        self.stdout.write(f'   Melhoria: {improvement:.1f}%')
        
        # Verificar se cache está funcionando
        cached_groups = cache.get('user_list_groups')
        cached_stats = cache.get('user_list_stats')
        
        if cached_groups and cached_stats:
            self.stdout.write(self.style.SUCCESS('   ✅ Cache funcionando corretamente'))
        else:
            self.stdout.write(self.style.WARNING('   ⚠️ Cache pode não estar funcionando'))
    
    def cleanup_test_data(self):
        """Limpar dados de teste"""
        self.stdout.write('\n🧹 Limpando dados de teste...')
        
        # Remover usuários de teste
        deleted_users = User.objects.filter(username__startswith='perf_user_').delete()
        deleted_admin = User.objects.filter(username='admin_perf').delete()
        
        # Remover logs de teste
        deleted_logs = UserAuditLog.objects.filter(action='performance_test').delete()
        
        # Remover cargo e departamento se não tiverem outros usuários
        try:
            cargo = Cargo.objects.get(nome='Desenvolvedor Performance')
            if not cargo.usuarios.exists():
                cargo.delete()
        except Cargo.DoesNotExist:
            pass
        
        try:
            dept = Departamento.objects.get(nome='TI Performance')
            if not dept.usuarios.exists():
                dept.delete()
        except Departamento.DoesNotExist:
            pass
        
        self.stdout.write(f'✅ Limpeza concluída:')
        self.stdout.write(f'   Usuários removidos: {deleted_users[0] + deleted_admin[0]}')
        self.stdout.write(f'   Logs removidos: {deleted_logs[0]}')
