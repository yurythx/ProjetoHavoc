"""
Decorators personalizados para proteção de rotas
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def account_activation_required(view_func):
    """
    Decorator que verifica se a conta do usuário está ativada.
    Redireciona para página de ativação se não estiver.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Se não está logado, redirecionar para login
            return redirect('accounts:login')

        if not request.user.is_active:
            # Se está logado mas conta não está ativa
            messages.warning(
                request,
                "🔒 Sua conta ainda não foi ativada. Para acessar esta página, você precisa ativar sua conta usando o código enviado por email."
            )
            return redirect(f"{reverse('accounts:ativar_conta')}?email={request.user.email}")

        if not getattr(request.user, 'email_verificado', True):
            # Se conta está ativa mas email não foi verificado
            messages.warning(
                request,
                "📧 Seu email não foi verificado. Complete a verificação para acessar esta página."
            )
            return redirect(f"{reverse('accounts:ativar_conta')}?email={request.user.email}")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def inactive_user_only(view_func):
    """
    Decorator que permite acesso apenas para usuários não autenticados
    ou com contas inativas (para páginas de ativação).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_active:
            # Se usuário está logado e ativo, redirecionar para perfil
            messages.info(
                request,
                "🎉 Sua conta já está ativa! Você já está logado no sistema."
            )
            return redirect('accounts:profile')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def email_verified_required(view_func):
    """
    Decorator que verifica se o email do usuário foi verificado.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not getattr(request.user, 'email_verificado', True):
            messages.warning(
                request,
                "📧 Você precisa verificar seu email antes de acessar esta página."
            )
            return redirect(f"{reverse('accounts:ativar_conta')}?email={request.user.email}")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def admin_or_superuser_required(view_func):
    """
    Decorator que verifica se o usuário é administrador ou superusuário.
    """
    @wraps(view_func)
    @login_required
    @account_activation_required
    def _wrapped_view(request, *args, **kwargs):
        # Verificar se é superuser
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Verificar se está no grupo Administrador
        if request.user.groups.filter(name='Administrador').exists():
            return view_func(request, *args, **kwargs)

        # Se não é admin nem superuser
        messages.error(
            request,
            "🚫 Acesso negado. Você precisa ser administrador para acessar esta página."
        )
        raise PermissionDenied("Acesso restrito a administradores")

    return _wrapped_view


def staff_required(view_func):
    """
    Decorator que verifica se o usuário é staff.
    """
    @wraps(view_func)
    @login_required
    @account_activation_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(
                request,
                "🚫 Acesso negado. Você precisa ser um usuário staff para acessar esta página."
            )
            raise PermissionDenied("Acesso restrito a usuários staff")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def group_required(*group_names):
    """
    Decorator que verifica se o usuário pertence a pelo menos um dos grupos especificados.

    Uso: @group_required('Administrador', 'Usuario')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        @account_activation_required
        def _wrapped_view(request, *args, **kwargs):
            user_groups = request.user.groups.values_list('name', flat=True)

            if not any(group in user_groups for group in group_names):
                group_list = ', '.join(group_names)
                messages.error(
                    request,
                    f"🚫 Acesso negado. Você precisa pertencer a um dos grupos: {group_list}"
                )
                raise PermissionDenied(f"Acesso restrito aos grupos: {group_list}")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def anonymous_required(view_func):
    """
    Decorator que permite acesso apenas para usuários não autenticados.
    Redireciona usuários logados para uma página de aviso adequada.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Determinar o tipo de página que estava tentando acessar
            view_name = request.resolver_match.url_name if request.resolver_match else 'unknown'

            # Evitar loop de redirecionamento - não redirecionar se já estamos nas páginas de aviso
            if view_name in ['already_logged_in_register', 'already_logged_in_login']:
                return view_func(request, *args, **kwargs)

            if view_name == 'register':
                # Para registro, mostrar página específica explicando o motivo
                return redirect('accounts:already_logged_in_register')
            elif view_name == 'login':
                # Para login, mostrar página específica explicando o motivo
                return redirect('accounts:already_logged_in_login')
            else:
                # Para outras páginas, redirecionar para o perfil com mensagem
                messages.info(
                    request,
                    "🎉 Você já está logado no sistema!"
                )
                return redirect('accounts:profile')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def account_complete_required(view_func):
    """
    Decorator que verifica se a conta está completamente configurada.
    Pode ser usado para verificar se perfil foi preenchido, etc.
    """
    @wraps(view_func)
    @login_required
    @account_activation_required
    def _wrapped_view(request, *args, **kwargs):
        # Verificar se perfil está completo (exemplo)
        user = request.user

        # Verificações básicas de perfil completo
        if not user.first_name or not user.last_name:
            messages.warning(
                request,
                "📝 Complete seu perfil antes de acessar esta página."
            )
            return redirect('accounts:edit_profile')

        return view_func(request, *args, **kwargs)

    return _wrapped_view
