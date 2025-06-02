#!/usr/bin/env python
"""
Script para corrigir emails duplicados antes de aplicar constraint
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Count

def fix_duplicate_emails():
    """Corrige emails duplicados"""
    print("🔧 === CORRIGINDO EMAILS DUPLICADOS ===")
    
    User = get_user_model()
    
    # Encontrar emails duplicados
    duplicate_emails = User.objects.values('email').annotate(
        count=Count('email')
    ).filter(count__gt=1)
    
    print(f"📊 Emails duplicados encontrados: {duplicate_emails.count()}")
    
    for dup in duplicate_emails:
        email = dup['email']
        count = dup['count']
        
        print(f"\n📧 Email duplicado: {email} ({count} usuários)")
        
        # Buscar todos os usuários com este email
        users_with_email = User.objects.filter(email=email).order_by('date_joined')
        
        # Manter o primeiro usuário (mais antigo) com o email original
        first_user = users_with_email.first()
        print(f"   ✅ Mantendo: {first_user.username} (criado em {first_user.date_joined})")
        
        # Alterar email dos outros usuários
        for i, user in enumerate(users_with_email[1:], 1):
            new_email = f"{email.split('@')[0]}_{i}@{email.split('@')[1]}"
            old_email = user.email
            user.email = new_email
            user.save()
            print(f"   🔄 Alterado: {user.username} - {old_email} → {new_email}")
    
    # Verificar se ainda há duplicatas
    remaining_duplicates = User.objects.values('email').annotate(
        count=Count('email')
    ).filter(count__gt=1)
    
    if remaining_duplicates.exists():
        print(f"\n❌ Ainda há {remaining_duplicates.count()} emails duplicados!")
        for dup in remaining_duplicates:
            print(f"   - {dup['email']}: {dup['count']} usuários")
    else:
        print("\n✅ Todos os emails duplicados foram corrigidos!")
    
    # Mostrar estatísticas finais
    total_users = User.objects.count()
    unique_emails = User.objects.values('email').distinct().count()
    
    print(f"\n📊 ESTATÍSTICAS FINAIS:")
    print(f"   👥 Total de usuários: {total_users}")
    print(f"   📧 Emails únicos: {unique_emails}")
    print(f"   ✅ Integridade: {'OK' if total_users == unique_emails else 'PROBLEMA'}")

if __name__ == '__main__':
    fix_duplicate_emails()
