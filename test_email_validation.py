#!/usr/bin/env python
"""
Teste do sistema de validação de email
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.accounts.email_validator import EmailValidator, validate_email_simple, validate_email_strict

def test_email_validation():
    """Testa diferentes tipos de email"""
    
    print("🧪 TESTE DE VALIDAÇÃO DE EMAIL")
    print("=" * 60)
    
    # Lista de emails para testar
    test_emails = [
        # Emails válidos
        ('usuario@gmail.com', True, 'Gmail válido'),
        ('teste@hotmail.com', True, 'Hotmail válido'),
        ('contato@empresa.com.br', True, 'Domínio brasileiro válido'),
        ('user@outlook.com', True, 'Outlook válido'),
        
        # Emails com sintaxe inválida
        ('email_sem_arroba.com', False, 'Sem @'),
        ('email@', False, 'Sem domínio'),
        ('@dominio.com', False, 'Sem parte local'),
        ('email@dominio', False, 'Domínio sem TLD'),
        ('email..duplo@dominio.com', False, 'Pontos duplos'),
        
        # Emails descartáveis
        ('teste@10minutemail.com', False, 'Email temporário'),
        ('user@guerrillamail.com', False, 'Email descartável'),
        ('temp@mailinator.com', False, 'Email temporário'),
        ('fake@yopmail.com', False, 'Email descartável'),
        
        # Domínios inexistentes
        ('usuario@dominioquenoexiste12345.com', False, 'Domínio inexistente'),
        ('teste@xyzabc999.net', False, 'Domínio falso'),
        
        # Emails muito longos
        ('a' * 65 + '@dominio.com', False, 'Parte local muito longa'),
        ('usuario@' + 'a' * 250 + '.com', False, 'Domínio muito longo'),
    ]
    
    print("📧 TESTANDO EMAILS:")
    print("-" * 60)
    
    for email, expected_valid, description in test_emails:
        print(f"\n🔍 Testando: {email}")
        print(f"📝 Descrição: {description}")
        print(f"🎯 Esperado: {'✅ Válido' if expected_valid else '❌ Inválido'}")
        
        # Teste com validação simples
        is_valid, message = validate_email_simple(email)
        status = "✅" if is_valid else "❌"
        print(f"📊 Resultado: {status} {message}")
        
        # Verificar se resultado está correto
        if is_valid == expected_valid:
            print("🎉 CORRETO!")
        else:
            print("⚠️ RESULTADO INESPERADO!")
        
        print("-" * 40)

def test_comprehensive_validation():
    """Teste detalhado de um email"""
    
    print("\n🔬 TESTE DETALHADO DE VALIDAÇÃO")
    print("=" * 60)
    
    test_email = "usuario@gmail.com"
    print(f"📧 Email de teste: {test_email}")
    
    result = EmailValidator.validate_email_comprehensive(test_email, check_smtp=False)
    
    print(f"\n📊 Resultado geral: {'✅ VÁLIDO' if result['is_valid'] else '❌ INVÁLIDO'}")
    
    print("\n🔍 Verificações detalhadas:")
    for check_name, check_result in result['checks'].items():
        status = "✅" if check_result['valid'] else "❌"
        print(f"   {check_name.upper()}: {status} {check_result['message']}")
    
    if result['errors']:
        print(f"\n❌ Erros encontrados:")
        for error in result['errors']:
            print(f"   • {error}")
    
    if result['warnings']:
        print(f"\n⚠️ Avisos:")
        for warning in result['warnings']:
            print(f"   • {warning}")

def test_disposable_domains():
    """Teste específico para domínios descartáveis"""
    
    print("\n🗑️ TESTE DE DOMÍNIOS DESCARTÁVEIS")
    print("=" * 60)
    
    disposable_emails = [
        'teste@10minutemail.com',
        'user@guerrillamail.com',
        'temp@mailinator.com',
        'fake@yopmail.com',
        'spam@tempmail.org'
    ]
    
    for email in disposable_emails:
        is_valid, message = EmailValidator.check_disposable_domain(email)
        status = "✅" if is_valid else "❌"
        print(f"{status} {email}: {message}")

if __name__ == "__main__":
    try:
        test_email_validation()
        test_comprehensive_validation()
        test_disposable_domains()
        
        print("\n🎉 TESTE CONCLUÍDO!")
        print("✅ Sistema de validação de email funcionando")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
