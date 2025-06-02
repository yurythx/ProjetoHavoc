"""
Configurações de Segurança para Projeto Havoc
Configurações específicas para produção e desenvolvimento
"""

import os
from decouple import config

def get_security_settings(debug_mode=False):
    """
    Retorna configurações de segurança baseadas no ambiente
    """
    
    # Configurações base de segurança
    security_settings = {
        # HTTPS e SSL
        'SECURE_SSL_REDIRECT': not debug_mode,
        'SECURE_PROXY_SSL_HEADER': ('HTTP_X_FORWARDED_PROTO', 'https') if not debug_mode else None,
        
        # HSTS (HTTP Strict Transport Security)
        'SECURE_HSTS_SECONDS': 31536000 if not debug_mode else 0,  # 1 ano
        'SECURE_HSTS_INCLUDE_SUBDOMAINS': not debug_mode,
        'SECURE_HSTS_PRELOAD': not debug_mode,
        
        # Cookies seguros
        'SESSION_COOKIE_SECURE': not debug_mode,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'SESSION_COOKIE_AGE': 3600,  # 1 hora
        
        'CSRF_COOKIE_SECURE': not debug_mode,
        'CSRF_COOKIE_HTTPONLY': True,
        'CSRF_COOKIE_SAMESITE': 'Lax',
        
        # Headers de segurança
        'SECURE_CONTENT_TYPE_NOSNIFF': True,
        'SECURE_BROWSER_XSS_FILTER': True,
        'X_FRAME_OPTIONS': 'DENY',
        'SECURE_REFERRER_POLICY': 'strict-origin-when-cross-origin',
        
        # Configurações de senha
        'AUTH_PASSWORD_VALIDATORS': [
            {
                'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
            },
            {
                'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
                'OPTIONS': {
                    'min_length': 8,
                }
            },
            {
                'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
            },
            {
                'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
            },
        ],
        
        # Configurações de login
        'LOGIN_ATTEMPTS_LIMIT': 5,
        'LOGIN_ATTEMPTS_TIMEOUT': 300,  # 5 minutos
        
        # Configurações de upload
        'FILE_UPLOAD_MAX_MEMORY_SIZE': 5242880,  # 5MB
        'DATA_UPLOAD_MAX_MEMORY_SIZE': 5242880,  # 5MB
        'DATA_UPLOAD_MAX_NUMBER_FIELDS': 1000,
        
        # Configurações de admin
        'ADMIN_URL': config('ADMIN_URL', default='admin/'),
        
        # Configurações de logging para segurança
        'SECURITY_LOGGING': {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'security': {
                    'format': '{levelname} {asctime} {name} {process:d} {thread:d} {message}',
                    'style': '{',
                },
            },
            'handlers': {
                'security_file': {
                    'level': 'WARNING',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': 'logs/security.log',
                    'maxBytes': 1024*1024*5,  # 5MB
                    'backupCount': 5,
                    'formatter': 'security',
                },
            },
            'loggers': {
                'security': {
                    'handlers': ['security_file'],
                    'level': 'WARNING',
                    'propagate': False,
                },
            },
        }
    }
    
    # Configurações específicas para desenvolvimento
    if debug_mode:
        security_settings.update({
            'INTERNAL_IPS': ['127.0.0.1', 'localhost'],
            'ALLOWED_HOSTS': ['*'],  # Apenas para desenvolvimento
        })
    else:
        # Configurações específicas para produção
        security_settings.update({
            'ALLOWED_HOSTS': config('ALLOWED_HOSTS', default='').split(','),
            'SECURE_CROSS_ORIGIN_OPENER_POLICY': 'same-origin',
        })
    
    return security_settings


def get_performance_settings(debug_mode=False):
    """
    Retorna configurações de performance
    """
    
    performance_settings = {
        # Cache
        'CACHES': {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache' if debug_mode else 'django.core.cache.backends.redis.RedisCache',
                'LOCATION': '127.0.0.1:6379' if not debug_mode else '',
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                } if not debug_mode else {},
                'KEY_PREFIX': 'havoc',
                'TIMEOUT': 300,  # 5 minutos
            }
        },
        
        # Sessões
        'SESSION_ENGINE': 'django.contrib.sessions.backends.cached_db',
        'SESSION_CACHE_ALIAS': 'default',
        
        # Arquivos estáticos
        'STATICFILES_STORAGE': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage' if not debug_mode else 'django.contrib.staticfiles.storage.StaticFilesStorage',
        
        # Compressão (se django-compressor estiver instalado)
        'COMPRESS_ENABLED': not debug_mode,
        'COMPRESS_OFFLINE': not debug_mode,
        'COMPRESS_CSS_FILTERS': [
            'compressor.filters.css_default.CssAbsoluteFilter',
            'compressor.filters.cssmin.rCSSMinFilter',
        ] if not debug_mode else [],
        'COMPRESS_JS_FILTERS': [
            'compressor.filters.jsmin.JSMinFilter',
        ] if not debug_mode else [],
        
        # Database
        'CONN_MAX_AGE': 60 if not debug_mode else 0,
        
        # Email (configuração básica)
        'EMAIL_BACKEND': 'django.core.mail.backends.console.EmailBackend' if debug_mode else 'django.core.mail.backends.smtp.EmailBackend',
        'EMAIL_TIMEOUT': 30,
    }
    
    return performance_settings


def get_monitoring_settings():
    """
    Retorna configurações de monitoramento e logging
    """
    
    # Criar diretório de logs se não existir
    import os
    os.makedirs('logs', exist_ok=True)
    
    monitoring_settings = {
        'LOGGING': {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                    'style': '{',
                },
                'simple': {
                    'format': '{levelname} {message}',
                    'style': '{',
                },
            },
            'handlers': {
                'file': {
                    'level': 'INFO',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': 'logs/django.log',
                    'maxBytes': 1024*1024*5,  # 5MB
                    'backupCount': 5,
                    'formatter': 'verbose',
                },
                'console': {
                    'level': 'INFO',
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple',
                },
                'error_file': {
                    'level': 'ERROR',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': 'logs/errors.log',
                    'maxBytes': 1024*1024*5,  # 5MB
                    'backupCount': 5,
                    'formatter': 'verbose',
                },
            },
            'root': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
            },
            'loggers': {
                'django': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False,
                },
                'django.request': {
                    'handlers': ['error_file'],
                    'level': 'ERROR',
                    'propagate': False,
                },
                'apps': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False,
                },
            },
        }
    }
    
    return monitoring_settings


def apply_security_middleware():
    """
    Retorna lista de middleware de segurança recomendado
    """
    
    security_middleware = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]
    
    return security_middleware


def get_database_optimization():
    """
    Retorna configurações otimizadas para banco de dados
    """
    
    db_optimization = {
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        } if 'mysql' in config('DATABASE_URL', default='') else {},
        
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
        
        # Pool de conexões (se usando PostgreSQL)
        'ENGINE_OPTIONS': {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_timeout': 30,
            'pool_recycle': 3600,
        } if 'postgresql' in config('DATABASE_URL', default='') else {},
    }
    
    return db_optimization
