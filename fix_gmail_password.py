#!/usr/bin/env python
"""
Script para corrigir a senha do Gmail usando o sistema de criptografia correto
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.config.models import EmailConfig, PasswordEncryptor

def fix_gmail_password():
    """Corrige a senha do Gmail usando criptografia"""
    print("🔧 CORRIGINDO SENHA DO GMAIL COM CRIPTOGRAFIA")
    print("=" * 60)
    
    try:
        # Buscar configuração do Gmail
        gmail_config = EmailConfig.objects.filter(
            email_host='smtp.gmail.com',
            email_host_user='projetohavoc@gmail.com'
        ).first()
        
        if not gmail_config:
            print("❌ Configuração Gmail não encontrada")
            return False
        
        print(f"📧 Configuração encontrada: {gmail_config.slug}")
        print(f"👤 Usuário: {gmail_config.email_host_user}")
        
        # Verificar senha atual
        current_password = gmail_config.get_password()
        print(f"🔑 Senha atual descriptografada: {'✅ OK' if current_password else '❌ Vazia/Erro'}")
        
        if current_password:
            print(f"🔐 Primeiros 4 chars: {current_password[:4]}...")
        
        # Definir a senha correta usando o método set_password
        correct_password = 'jovbcnpsshqjrooh'
        print(f"\n🔄 Configurando senha correta...")
        
        # Usar o método correto para definir a senha
        gmail_config.set_password(correct_password)
        gmail_config.save()
        
        print("✅ Senha configurada e criptografada com sucesso!")
        
        # Verificar se a senha foi salva corretamente
        gmail_config.refresh_from_db()
        decrypted_password = gmail_config.get_password()
        
        print(f"🧪 Verificação pós-save:")
        print(f"   🔐 Senha criptografada no banco: {gmail_config.email_host_password[:20]}...")
        print(f"   🔓 Senha descriptografada: {'✅ OK' if decrypted_password == correct_password else '❌ Erro'}")
        
        if decrypted_password == correct_password:
            print(f"   ✅ Primeiros 4 chars: {decrypted_password[:4]}...")
            return True
        else:
            print(f"   ❌ Senha não confere!")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao corrigir senha: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_password_encryption():
    """Testa o sistema de criptografia"""
    print("\n🧪 TESTANDO SISTEMA DE CRIPTOGRAFIA")
    print("=" * 40)
    
    test_password = 'jovbcnpsshqjrooh'
    
    try:
        # Testar criptografia
        encrypted = PasswordEncryptor.encrypt_password(test_password)
        print(f"🔐 Senha criptografada: {encrypted[:20]}...")
        
        # Testar descriptografia
        decrypted = PasswordEncryptor.decrypt_password(encrypted)
        print(f"🔓 Senha descriptografada: {decrypted}")
        
        if decrypted == test_password:
            print("✅ Sistema de criptografia funcionando!")
            return True
        else:
            print("❌ Erro no sistema de criptografia!")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de criptografia: {e}")
        return False

def test_email_after_fix():
    """Testa envio de email após correção"""
    print("\n📧 TESTANDO ENVIO DE EMAIL APÓS CORREÇÃO")
    print("=" * 45)
    
    try:
        from apps.config.email_utils import send_test_email
        
        # Buscar configuração do Gmail
        gmail_config = EmailConfig.objects.filter(
            email_host='smtp.gmail.com',
            email_host_user='projetohavoc@gmail.com'
        ).first()
        
        if not gmail_config:
            print("❌ Configuração Gmail não encontrada")
            return False
        
        # Testar envio
        success, message = send_test_email('projetohavoc@gmail.com', gmail_config)
        
        if success:
            print(f"✅ {message}")
            return True
        else:
            print(f"❌ {message}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de email: {e}")
        return False

def show_all_configs():
    """Mostra todas as configurações"""
    print("\n📊 TODAS AS CONFIGURAÇÕES DE EMAIL:")
    print("=" * 40)
    
    configs = EmailConfig.objects.all()
    
    for config in configs:
        password_status = "✅ OK" if config.get_password() else "❌ Vazia/Erro"
        default_status = "⭐ PADRÃO" if config.is_default else ""
        active_status = "✅ ATIVO" if config.is_active else "❌ INATIVO"
        
        print(f"🏷️ {config.slug}")
        print(f"   📧 {config.email_host}:{config.email_port}")
        print(f"   👤 {config.email_host_user}")
        print(f"   🔑 Senha: {password_status}")
        print(f"   {active_status} {default_status}")
        print()

if __name__ == "__main__":
    print("🚀 CORREÇÃO DA SENHA DO GMAIL")
    print("=" * 60)
    
    # Mostrar estado inicial
    show_all_configs()
    
    # Testar sistema de criptografia
    crypto_ok = test_password_encryption()
    
    if crypto_ok:
        # Corrigir senha do Gmail
        fix_ok = fix_gmail_password()
        
        if fix_ok:
            # Testar envio de email
            email_ok = test_email_after_fix()
            
            # Mostrar estado final
            show_all_configs()
            
            if email_ok:
                print("🎉 GMAIL TOTALMENTE FUNCIONAL!")
                print("📧 Agora teste na interface web também!")
            else:
                print("⚠️ Senha corrigida, mas teste de email falhou")
        else:
            print("❌ Falha na correção da senha")
    else:
        print("❌ Sistema de criptografia com problemas")
