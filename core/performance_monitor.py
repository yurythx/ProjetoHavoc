"""
Sistema de Monitoramento de Performance
Projeto Havoc - Monitoramento em tempo real
"""

import time
import psutil
import logging
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
import json

logger = logging.getLogger('performance')


class PerformanceMonitor:
    """Monitor de performance do sistema"""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()
        
    def start_request_monitoring(self, request):
        """Inicia monitoramento de uma requisição"""
        self.request_start = time.time()
        self.initial_queries = len(connection.queries)
        
        # Armazenar informações da requisição
        self.request_info = {
            'path': request.path,
            'method': request.method,
            'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
            'ip': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            'timestamp': timezone.now().isoformat()
        }
        
    def end_request_monitoring(self, response=None):
        """Finaliza monitoramento de uma requisição"""
        request_time = time.time() - self.request_start
        query_count = len(connection.queries) - self.initial_queries
        
        # Coletar métricas do sistema
        system_metrics = self.get_system_metrics()
        
        # Criar relatório de performance
        performance_data = {
            'request': self.request_info,
            'timing': {
                'request_time': round(request_time, 3),
                'query_count': query_count,
                'queries_time': self.calculate_queries_time(),
            },
            'system': system_metrics,
            'response': {
                'status_code': response.status_code if response else None,
                'content_length': len(response.content) if response and hasattr(response, 'content') else 0
            }
        }
        
        # Log se requisição for lenta
        slow_threshold = getattr(settings, 'PERFORMANCE_MONITORING', {}).get('SLOW_REQUEST_THRESHOLD', 2.0)
        if request_time > slow_threshold:
            logger.warning(f"Slow request detected: {json.dumps(performance_data)}")
        
        # Armazenar métricas no cache
        self.store_metrics(performance_data)
        
        return performance_data
    
    def get_client_ip(self, request):
        """Obtém IP real do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def calculate_queries_time(self):
        """Calcula tempo total das queries"""
        total_time = 0
        for query in connection.queries[self.initial_queries:]:
            total_time += float(query['time'])
        return round(total_time, 3)
    
    def get_system_metrics(self):
        """Coleta métricas do sistema"""
        try:
            # CPU e Memória
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # Disco
            disk = psutil.disk_usage('/')
            
            # Rede (se disponível)
            try:
                network = psutil.net_io_counters()
                network_data = {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            except:
                network_data = {}
            
            return {
                'cpu': {
                    'percent': round(cpu_percent, 1),
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'percent': round(memory.percent, 1),
                    'available': memory.available,
                    'total': memory.total,
                    'used': memory.used
                },
                'disk': {
                    'percent': round(disk.percent, 1),
                    'free': disk.free,
                    'total': disk.total,
                    'used': disk.used
                },
                'network': network_data,
                'load_average': list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else []
            }
        except Exception as e:
            logger.error(f"Erro ao coletar métricas do sistema: {e}")
            return {}
    
    def store_metrics(self, performance_data):
        """Armazena métricas no cache para análise posterior"""
        try:
            # Chave única para a métrica
            metric_key = f"performance_metric_{int(time.time())}"
            
            # Armazenar por 1 hora
            cache.set(metric_key, performance_data, 3600)
            
            # Manter lista das últimas 100 métricas
            metrics_list_key = "performance_metrics_list"
            metrics_list = cache.get(metrics_list_key, [])
            
            metrics_list.append(metric_key)
            
            # Manter apenas as últimas 100
            if len(metrics_list) > 100:
                # Remover métricas antigas
                old_keys = metrics_list[:-100]
                for old_key in old_keys:
                    cache.delete(old_key)
                metrics_list = metrics_list[-100:]
            
            cache.set(metrics_list_key, metrics_list, 3600)
            
        except Exception as e:
            logger.error(f"Erro ao armazenar métricas: {e}")
    
    def get_recent_metrics(self, limit=50):
        """Obtém métricas recentes"""
        try:
            metrics_list_key = "performance_metrics_list"
            metrics_list = cache.get(metrics_list_key, [])
            
            recent_metrics = []
            for metric_key in metrics_list[-limit:]:
                metric_data = cache.get(metric_key)
                if metric_data:
                    recent_metrics.append(metric_data)
            
            return recent_metrics
        except Exception as e:
            logger.error(f"Erro ao obter métricas recentes: {e}")
            return []
    
    def get_performance_summary(self):
        """Gera resumo de performance"""
        try:
            recent_metrics = self.get_recent_metrics(100)
            
            if not recent_metrics:
                return {
                    'status': 'no_data',
                    'message': 'Nenhuma métrica disponível'
                }
            
            # Calcular estatísticas
            request_times = [m['timing']['request_time'] for m in recent_metrics]
            query_counts = [m['timing']['query_count'] for m in recent_metrics]
            
            # Métricas do sistema (última disponível)
            latest_system = recent_metrics[-1].get('system', {})
            
            summary = {
                'status': 'ok',
                'period': f"Últimas {len(recent_metrics)} requisições",
                'requests': {
                    'total': len(recent_metrics),
                    'avg_time': round(sum(request_times) / len(request_times), 3),
                    'max_time': round(max(request_times), 3),
                    'min_time': round(min(request_times), 3),
                    'slow_requests': len([t for t in request_times if t > 2.0])
                },
                'database': {
                    'avg_queries': round(sum(query_counts) / len(query_counts), 1),
                    'max_queries': max(query_counts),
                    'total_queries': sum(query_counts)
                },
                'system': latest_system,
                'timestamp': timezone.now().isoformat()
            }
            
            # Determinar status geral
            if summary['requests']['avg_time'] > 2.0:
                summary['status'] = 'slow'
            elif latest_system.get('cpu', {}).get('percent', 0) > 80:
                summary['status'] = 'high_cpu'
            elif latest_system.get('memory', {}).get('percent', 0) > 80:
                summary['status'] = 'high_memory'
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo de performance: {e}")
            return {
                'status': 'error',
                'message': f'Erro ao gerar resumo: {str(e)}'
            }
    
    def clear_metrics(self):
        """Limpa todas as métricas armazenadas"""
        try:
            metrics_list_key = "performance_metrics_list"
            metrics_list = cache.get(metrics_list_key, [])
            
            # Remover todas as métricas
            for metric_key in metrics_list:
                cache.delete(metric_key)
            
            # Limpar lista
            cache.delete(metrics_list_key)
            
            logger.info("Métricas de performance limpas")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao limpar métricas: {e}")
            return False


class PerformanceMiddleware:
    """Middleware para monitoramento automático de performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.monitor = PerformanceMonitor()
    
    def __call__(self, request):
        # Iniciar monitoramento
        self.monitor.start_request_monitoring(request)
        
        # Processar requisição
        response = self.get_response(request)
        
        # Finalizar monitoramento
        performance_data = self.monitor.end_request_monitoring(response)
        
        # Adicionar header com tempo de resposta (apenas em debug)
        if settings.DEBUG:
            response['X-Response-Time'] = f"{performance_data['timing']['request_time']}s"
            response['X-Query-Count'] = str(performance_data['timing']['query_count'])
        
        return response


# Instância global do monitor
performance_monitor = PerformanceMonitor()
