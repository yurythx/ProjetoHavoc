#!/usr/bin/env python
"""
Teste de performance das validações de email
"""
import os
import sys
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.accounts.validators import (
    validate_real_email_basic, 
    validate_real_email, 
    validate_real_email_strict,
    validate_no_disposable
)
from django.core.exceptions import ValidationError

def test_validation_performance():
    """Testa performance dos diferentes níveis de validação"""
    
    print("⚡ TESTE DE PERFORMANCE DE VALIDAÇÃO DE EMAIL")
    print("=" * 60)
    
    test_emails = [
        'usuario@gmail.com',
        'teste@hotmail.com', 
        'contato@outlook.com',
        'user@yahoo.com',
        'email@empresa.com.br'
    ]
    
    validators = [
        ('🟢 BÁSICO (sintaxe + descartáveis)', validate_real_email_basic),
        ('🟡 PADRÃO (+ verificação domínio)', validate_real_email),
        ('🔴 RIGOROSO (+ MX + SMTP)', validate_real_email_strict),
        ('⚡ APENAS DESCARTÁVEIS', validate_no_disposable),
    ]
    
    for validator_name, validator_func in validators:
        print(f"\n{validator_name}")
        print("-" * 50)
        
        total_time = 0
        success_count = 0
        
        for email in test_emails:
            start_time = time.time()
            
            try:
                validator_func(email)
                result = "✅ Válido"
                success_count += 1
            except ValidationError as e:
                result = f"❌ {e.message}"
            except Exception as e:
                result = f"⚠️ Erro: {e}"
            
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # em ms
            total_time += duration
            
            print(f"📧 {email:<25} | {duration:6.1f}ms | {result}")
        
        avg_time = total_time / len(test_emails)
        print(f"\n📊 Resumo:")
        print(f"   ⏱️ Tempo médio: {avg_time:.1f}ms")
        print(f"   ✅ Sucessos: {success_count}/{len(test_emails)}")
        print(f"   🚀 Total: {total_time:.1f}ms")

def test_disposable_emails():
    """Teste específico para emails descartáveis"""
    
    print("\n\n🗑️ TESTE DE EMAILS DESCARTÁVEIS")
    print("=" * 60)
    
    disposable_emails = [
        'teste@10minutemail.com',
        'user@guerrillamail.com', 
        'temp@mailinator.com',
        'fake@yopmail.com',
        'spam@tempmail.org'
    ]
    
    print("🟢 VALIDAÇÃO BÁSICA (deve bloquear todos):")
    print("-" * 40)
    
    for email in disposable_emails:
        start_time = time.time()
        
        try:
            validate_real_email_basic(email)
            result = "✅ Passou (PROBLEMA!)"
        except ValidationError as e:
            result = f"❌ Bloqueado: {e.message}"
        
        end_time = time.time()
        duration = (end_time - start_time) * 1000
        
        print(f"📧 {email:<25} | {duration:6.1f}ms | {result}")

def test_invalid_syntax():
    """Teste para emails com sintaxe inválida"""
    
    print("\n\n❌ TESTE DE SINTAXE INVÁLIDA")
    print("=" * 60)
    
    invalid_emails = [
        'email_sem_arroba.com',
        'email@',
        '@dominio.com',
        'email@dominio',
        'email..duplo@dominio.com'
    ]
    
    print("🟢 VALIDAÇÃO BÁSICA (deve rejeitar todos):")
    print("-" * 40)
    
    for email in invalid_emails:
        start_time = time.time()
        
        try:
            validate_real_email_basic(email)
            result = "✅ Passou (PROBLEMA!)"
        except ValidationError as e:
            result = f"❌ Rejeitado: {e.message}"
        
        end_time = time.time()
        duration = (end_time - start_time) * 1000
        
        print(f"📧 {email:<25} | {duration:6.1f}ms | {result}")

def performance_recommendation():
    """Recomendação de uso baseada na performance"""
    
    print("\n\n💡 RECOMENDAÇÕES DE USO")
    print("=" * 60)
    
    print("🟢 VALIDAÇÃO BÁSICA (recomendada para registro):")
    print("   ⚡ Muito rápida (< 5ms)")
    print("   ✅ Bloqueia emails descartáveis")
    print("   ✅ Valida sintaxe")
    print("   🎯 Ideal para: Formulários de registro, newsletter")
    
    print("\n🟡 VALIDAÇÃO PADRÃO (recomendada para perfis):")
    print("   ⚡ Rápida (< 100ms)")
    print("   ✅ + Verifica se domínio existe")
    print("   🎯 Ideal para: Edição de perfil, contatos importantes")
    
    print("\n🔴 VALIDAÇÃO RIGOROSA (usar com cuidado):")
    print("   ⚠️ Lenta (> 1000ms)")
    print("   ✅ + Verifica MX e SMTP")
    print("   🎯 Ideal para: Validação crítica, verificação manual")
    
    print("\n⚡ APENAS DESCARTÁVEIS (super rápida):")
    print("   ⚡ Instantânea (< 1ms)")
    print("   ✅ Apenas bloqueia emails temporários")
    print("   🎯 Ideal para: Validação adicional, filtros")

if __name__ == "__main__":
    try:
        test_validation_performance()
        test_disposable_emails()
        test_invalid_syntax()
        performance_recommendation()
        
        print("\n🎉 TESTE DE PERFORMANCE CONCLUÍDO!")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
