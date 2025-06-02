"""
Sistema de Detecção Automática de Ambiente
Projeto Havoc - Assistente de Configuração
"""

import os
import sys
import platform
import psutil
import socket
import subprocess
from pathlib import Path
from django.conf import settings
from django.core.management import execute_from_command_line
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class EnvironmentDetector:
    """Detector automático de ambiente e configurações"""
    
    def __init__(self):
        self.environment_info = {}
        self.recommendations = []
        self.warnings = []
        self.errors = []
    
    def detect_full_environment(self):
        """Detecta todas as informações do ambiente"""
        try:
            self.environment_info = {
                'system': self._detect_system_info(),
                'python': self._detect_python_info(),
                'django': self._detect_django_info(),
                'database': self._detect_database_info(),
                'web_server': self._detect_web_server(),
                'cache': self._detect_cache_info(),
                'security': self._detect_security_info(),
                'performance': self._detect_performance_info(),
                'deployment': self._detect_deployment_type(),
                'dependencies': self._detect_dependencies(),
            }
            
            # Gerar recomendações baseadas na detecção
            self._generate_recommendations()
            
            return {
                'environment': self.environment_info,
                'recommendations': self.recommendations,
                'warnings': self.warnings,
                'errors': self.errors,
                'score': self._calculate_environment_score()
            }
            
        except Exception as e:
            logger.error(f"Erro na detecção de ambiente: {e}")
            self.errors.append(f"Erro na detecção: {str(e)}")
            return None
    
    def _detect_system_info(self):
        """Detecta informações do sistema operacional"""
        try:
            return {
                'os': platform.system(),
                'os_version': platform.release(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'hostname': socket.gethostname(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
                'uptime': self._get_system_uptime(),
            }
        except Exception as e:
            logger.error(f"Erro ao detectar sistema: {e}")
            return {'error': str(e)}
    
    def _detect_python_info(self):
        """Detecta informações do Python"""
        try:
            return {
                'version': platform.python_version(),
                'implementation': platform.python_implementation(),
                'executable': sys.executable,
                'path': sys.path[:3],  # Primeiros 3 paths
                'virtual_env': os.environ.get('VIRTUAL_ENV'),
                'pip_version': self._get_pip_version(),
            }
        except Exception as e:
            logger.error(f"Erro ao detectar Python: {e}")
            return {'error': str(e)}
    
    def _detect_django_info(self):
        """Detecta informações do Django"""
        try:
            import django
            return {
                'version': django.get_version(),
                'debug': settings.DEBUG,
                'secret_key_secure': not settings.SECRET_KEY.startswith('django-insecure-'),
                'allowed_hosts': settings.ALLOWED_HOSTS,
                'installed_apps': len(settings.INSTALLED_APPS),
                'middleware': len(settings.MIDDLEWARE),
                'time_zone': settings.TIME_ZONE,
                'language_code': settings.LANGUAGE_CODE,
                'static_url': settings.STATIC_URL,
                'media_url': getattr(settings, 'MEDIA_URL', None),
            }
        except Exception as e:
            logger.error(f"Erro ao detectar Django: {e}")
            return {'error': str(e)}
    
    def _detect_database_info(self):
        """Detecta informações do banco de dados"""
        try:
            db_config = settings.DATABASES['default']
            
            # Testar conexão
            connection_status = 'connected'
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
            except Exception:
                connection_status = 'disconnected'
            
            return {
                'engine': db_config['ENGINE'],
                'name': db_config['NAME'],
                'host': db_config.get('HOST', 'localhost'),
                'port': db_config.get('PORT', 'default'),
                'connection_status': connection_status,
                'supports_transactions': connection.features.supports_transactions,
                'max_connections': self._get_db_max_connections(),
            }
        except Exception as e:
            logger.error(f"Erro ao detectar banco: {e}")
            return {'error': str(e)}
    
    def _detect_web_server(self):
        """Detecta servidor web em uso"""
        try:
            # Detectar se está rodando com servidor de desenvolvimento
            if 'runserver' in sys.argv:
                return {
                    'type': 'development',
                    'server': 'Django Development Server',
                    'port': self._get_server_port(),
                    'recommendation': 'Use Gunicorn/uWSGI para produção'
                }
            
            # Detectar outros servidores
            server_indicators = {
                'gunicorn': 'Gunicorn',
                'uwsgi': 'uWSGI',
                'apache': 'Apache',
                'nginx': 'Nginx'
            }
            
            for indicator, name in server_indicators.items():
                if self._check_process_running(indicator):
                    return {
                        'type': 'production',
                        'server': name,
                        'detected': True
                    }
            
            return {
                'type': 'unknown',
                'server': 'Not detected',
                'recommendation': 'Configure um servidor web para produção'
            }
            
        except Exception as e:
            logger.error(f"Erro ao detectar servidor web: {e}")
            return {'error': str(e)}
    
    def _detect_cache_info(self):
        """Detecta sistema de cache"""
        try:
            cache_config = getattr(settings, 'CACHES', {})
            default_cache = cache_config.get('default', {})
            
            backend = default_cache.get('BACKEND', 'unknown')
            
            cache_info = {
                'backend': backend,
                'configured': bool(cache_config),
                'redis_available': self._check_redis_available(),
                'memcached_available': self._check_memcached_available(),
            }
            
            if 'redis' in backend.lower():
                cache_info['type'] = 'Redis'
                cache_info['recommended'] = True
            elif 'memcached' in backend.lower():
                cache_info['type'] = 'Memcached'
                cache_info['recommended'] = True
            elif 'locmem' in backend.lower():
                cache_info['type'] = 'Local Memory'
                cache_info['recommended'] = False
            else:
                cache_info['type'] = 'Database/File'
                cache_info['recommended'] = False
            
            return cache_info
            
        except Exception as e:
            logger.error(f"Erro ao detectar cache: {e}")
            return {'error': str(e)}
    
    def _detect_security_info(self):
        """Detecta configurações de segurança"""
        try:
            return {
                'https_configured': self._check_https_configured(),
                'csrf_protection': 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE,
                'session_security': self._check_session_security(),
                'password_validators': len(getattr(settings, 'AUTH_PASSWORD_VALIDATORS', [])),
                'secure_headers': self._check_secure_headers(),
                'debug_in_production': settings.DEBUG and self._is_production_environment(),
            }
        except Exception as e:
            logger.error(f"Erro ao detectar segurança: {e}")
            return {'error': str(e)}
    
    def _detect_performance_info(self):
        """Detecta informações de performance"""
        try:
            return {
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
                'django_debug_toolbar': 'debug_toolbar' in settings.INSTALLED_APPS,
            }
        except Exception as e:
            logger.error(f"Erro ao detectar performance: {e}")
            return {'error': str(e)}
    
    def _detect_deployment_type(self):
        """Detecta tipo de deployment"""
        try:
            indicators = {
                'docker': bool(Path('/.dockerenv').exists() or os.environ.get('DOCKER_CONTAINER')),
                'heroku': bool(os.environ.get('DYNO')),
                'aws': bool(os.environ.get('AWS_EXECUTION_ENV')),
                'gcp': bool(os.environ.get('GOOGLE_CLOUD_PROJECT')),
                'azure': bool(os.environ.get('WEBSITE_SITE_NAME')),
                'local': not any([
                    Path('/.dockerenv').exists(),
                    os.environ.get('DYNO'),
                    os.environ.get('AWS_EXECUTION_ENV'),
                    os.environ.get('GOOGLE_CLOUD_PROJECT'),
                    os.environ.get('WEBSITE_SITE_NAME'),
                ])
            }
            
            detected_platforms = [platform for platform, detected in indicators.items() if detected]
            
            return {
                'platforms': detected_platforms,
                'primary': detected_platforms[0] if detected_platforms else 'unknown',
                'containerized': indicators['docker'],
                'cloud_provider': self._detect_cloud_provider(),
            }
            
        except Exception as e:
            logger.error(f"Erro ao detectar deployment: {e}")
            return {'error': str(e)}
    
    def _detect_dependencies(self):
        """Detecta dependências instaladas"""
        try:
            import pkg_resources
            
            installed_packages = {pkg.project_name: pkg.version for pkg in pkg_resources.working_set}
            
            critical_packages = [
                'django', 'psycopg2', 'redis', 'celery', 'gunicorn',
                'pillow', 'requests', 'python-decouple'
            ]
            
            package_status = {}
            for package in critical_packages:
                package_status[package] = {
                    'installed': package.lower() in [p.lower() for p in installed_packages.keys()],
                    'version': installed_packages.get(package, 'Not installed')
                }
            
            return {
                'total_packages': len(installed_packages),
                'critical_packages': package_status,
                'requirements_file': bool(Path('requirements.txt').exists()),
                'pipfile': bool(Path('Pipfile').exists()),
                'poetry': bool(Path('pyproject.toml').exists()),
            }
            
        except Exception as e:
            logger.error(f"Erro ao detectar dependências: {e}")
            return {'error': str(e)}
    
    # Métodos auxiliares
    def _get_system_uptime(self):
        """Obtém uptime do sistema"""
        try:
            return psutil.boot_time()
        except:
            return None
    
    def _get_pip_version(self):
        """Obtém versão do pip"""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.stdout.strip() if result.returncode == 0 else 'Unknown'
        except:
            return 'Unknown'
    
    def _get_server_port(self):
        """Obtém porta do servidor"""
        try:
            for arg in sys.argv:
                if ':' in arg and arg.replace(':', '').replace('.', '').isdigit():
                    return arg.split(':')[-1]
            return '8000'  # Padrão Django
        except:
            return 'Unknown'
    
    def _check_process_running(self, process_name):
        """Verifica se um processo está rodando"""
        try:
            for proc in psutil.process_iter(['name']):
                if process_name.lower() in proc.info['name'].lower():
                    return True
            return False
        except:
            return False
    
    def _check_redis_available(self):
        """Verifica se Redis está disponível"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            return True
        except:
            return False
    
    def _check_memcached_available(self):
        """Verifica se Memcached está disponível"""
        try:
            import memcache
            mc = memcache.Client(['127.0.0.1:11211'])
            mc.set('test', 'test')
            return mc.get('test') == 'test'
        except:
            return False
    
    def _check_https_configured(self):
        """Verifica se HTTPS está configurado"""
        return getattr(settings, 'SECURE_SSL_REDIRECT', False) or \
               getattr(settings, 'SECURE_PROXY_SSL_HEADER', None) is not None
    
    def _check_session_security(self):
        """Verifica segurança de sessão"""
        return {
            'secure_cookies': getattr(settings, 'SESSION_COOKIE_SECURE', False),
            'httponly_cookies': getattr(settings, 'SESSION_COOKIE_HTTPONLY', True),
            'csrf_cookie_secure': getattr(settings, 'CSRF_COOKIE_SECURE', False),
        }
    
    def _check_secure_headers(self):
        """Verifica headers de segurança"""
        return {
            'hsts': getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0,
            'content_type_nosniff': getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False),
            'browser_xss_filter': getattr(settings, 'SECURE_BROWSER_XSS_FILTER', False),
            'frame_deny': getattr(settings, 'X_FRAME_OPTIONS', '') == 'DENY',
        }
    
    def _is_production_environment(self):
        """Detecta se é ambiente de produção"""
        production_indicators = [
            os.environ.get('DJANGO_ENV') == 'production',
            os.environ.get('ENVIRONMENT') == 'production',
            not settings.DEBUG,
            'production' in os.environ.get('DATABASE_URL', '').lower(),
        ]
        return any(production_indicators)
    
    def _detect_cloud_provider(self):
        """Detecta provedor de nuvem"""
        if os.environ.get('AWS_EXECUTION_ENV'):
            return 'AWS'
        elif os.environ.get('GOOGLE_CLOUD_PROJECT'):
            return 'Google Cloud'
        elif os.environ.get('WEBSITE_SITE_NAME'):
            return 'Azure'
        elif os.environ.get('DYNO'):
            return 'Heroku'
        return None
    
    def _get_db_max_connections(self):
        """Obtém máximo de conexões do banco"""
        try:
            with connection.cursor() as cursor:
                if 'postgresql' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute("SHOW max_connections;")
                    return cursor.fetchone()[0]
                elif 'mysql' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute("SHOW VARIABLES LIKE 'max_connections';")
                    return cursor.fetchone()[1]
            return 'Unknown'
        except:
            return 'Unknown'
    
    def _generate_recommendations(self):
        """Gera recomendações baseadas na detecção"""
        env = self.environment_info
        
        # Recomendações de segurança
        if env.get('django', {}).get('debug') and self._is_production_environment():
            self.errors.append("DEBUG=True em ambiente de produção!")
            self.recommendations.append({
                'category': 'security',
                'priority': 'critical',
                'title': 'Desativar DEBUG em produção',
                'description': 'DEBUG=True expõe informações sensíveis',
                'action': 'Definir DEBUG=False no arquivo .env'
            })
        
        # Recomendações de performance
        if env.get('cache', {}).get('type') in ['Database/File', 'Local Memory']:
            self.recommendations.append({
                'category': 'performance',
                'priority': 'high',
                'title': 'Configurar Redis para cache',
                'description': 'Cache atual não é otimizado para produção',
                'action': 'Instalar e configurar Redis'
            })
        
        # Recomendações de servidor web
        if env.get('web_server', {}).get('type') == 'development':
            self.recommendations.append({
                'category': 'deployment',
                'priority': 'high',
                'title': 'Configurar servidor web para produção',
                'description': 'Servidor de desenvolvimento não é adequado para produção',
                'action': 'Configurar Gunicorn + Nginx'
            })
    
    def _calculate_environment_score(self):
        """Calcula score do ambiente (0-100)"""
        score = 100
        
        # Penalidades por problemas
        score -= len(self.errors) * 20
        score -= len(self.warnings) * 10
        
        # Bonificações por boas práticas
        env = self.environment_info
        
        if env.get('django', {}).get('secret_key_secure'):
            score += 5
        
        if env.get('security', {}).get('csrf_protection'):
            score += 5
        
        if env.get('cache', {}).get('recommended'):
            score += 10
        
        return max(0, min(100, score))


# Instância global do detector
environment_detector = EnvironmentDetector()
