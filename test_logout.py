#!/usr/bin/env python
"""
Teste do logout via GET
"""
import requests

# Testar logout via GET
print("🧪 Testando logout via GET...")
response = requests.get('http://127.0.0.1:8000/accounts/logout/')
print(f"Status: {response.status_code}")
print(f"Redirecionou para: {response.url}")

if response.status_code == 200:
    print("✅ Logout via GET funcionando!")
else:
    print("❌ Problema no logout via GET")
