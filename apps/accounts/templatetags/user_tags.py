from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter
def has_group(user, group_name):
    """Verifica se o usuário pertence a um grupo específico"""
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()

@register.filter
def is_admin(user):
    """Verifica se o usuário é administrador"""
    if not user or not user.is_authenticated:
        return False
    return (
        user.is_superuser or 
        user.is_staff or 
        user.groups.filter(name='Administrador').exists()
    )

@register.filter
def filter_by_name(queryset, name):
    """Filtra um queryset pelo nome"""
    try:
        return queryset.filter(name=name).exists()
    except:
        return False
