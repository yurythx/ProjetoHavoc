#!/usr/bin/env python
"""
Script para limpar cache de rate limiting
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.cache import cache

def clear_rate_limit_cache():
    """Limpa todo o cache de rate limiting"""
    print("🧹 === LIMPANDO CACHE DE RATE LIMITING ===")
    
    # Limpar cache completo (método mais eficaz)
    cache.clear()
    print("✅ Cache completo limpo")
    
    # Verificar se limpou
    test_key = 'rate_limit:127.0.0.1'
    value = cache.get(test_key)
    if value is None:
        print("✅ Rate limiting resetado com sucesso")
    else:
        print(f"⚠️ Ainda há dados no cache: {value}")
    
    print("\n📊 === NOVOS LIMITES DE RATE LIMITING ===")
    print("👑 Staff/Admin: 1000 requests/minuto")
    print("👤 Usuários: 300 requests/minuto") 
    print("🌐 Anônimos: 100 requests/minuto")
    
    print("\n🎯 Rate limiting otimizado para uso normal do sistema!")

if __name__ == '__main__':
    clear_rate_limit_cache()
