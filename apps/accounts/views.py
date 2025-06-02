from django.contrib.auth import login, get_user_model, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, TemplateView, UpdateView, View, ListView, DeleteView
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect
from urllib.parse import urlencode
from .decorators import (
    account_activation_required, inactive_user_only, email_verified_required,
    admin_or_superuser_required, anonymous_required, staff_required
)
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.debug import sensitive_variables
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q, Count, Case, When, F, Value
from django.db import models
from django.http import JsonResponse
from django.utils import timezone
from apps.config.models import LDAPConfig, EmailConfig
from ldap3 import Server, Connection, ALL, Tls
from django.contrib.auth.backends import ModelBackend
from apps.accounts.forms import (
    EditProfileForm, UserProfileForm, EmailSettingsForm,
    SocialAuthSettingsForm, LDAPSettingsForm, CustomUserCreationForm,
    UserManagementForm, CodigoAtivacaoForm, SolicitarCodigoForm
)
from apps.accounts.models import SocialAuthSettings, Cargo, Departamento, UserAuditLog
import logging
import ssl

# Configuração de logging
logger = logging.getLogger(__name__)
User = get_user_model()

# Mixins e classes auxiliares
class MessageMixin:
    def add_message(self, level, message):
        messages.add_message(self.request, level, message)

# --- PÁGINA DE TESTES ---
class TestPageView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Página de testes - APENAS para desenvolvimento e administradores"""
    template_name = 'accounts/test_page.html'

    def test_func(self):
        """Apenas staff e superusers podem acessar"""
        return self.request.user.is_staff or self.request.user.is_superuser

    def dispatch(self, request, *args, **kwargs):
        """Verificar autenticação e permissões"""
        # Verificar se usuário está logado
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Verificar se é staff ou superuser
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, '🚫 Acesso negado. Apenas administradores podem acessar esta página.')
            return redirect('pages:home')

        # Bloquear acesso em produção para não-superusers
        if not settings.DEBUG and not request.user.is_superuser:
            messages.warning(request, '⚠️ Página de testes não disponível em produção.')
            return redirect('pages:home')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['debug_mode'] = settings.DEBUG
        context['is_production'] = not settings.DEBUG
        return context

# --- Limitação de tentativas ---
def limit_attempts(request, key_prefix, limit=5, timeout=300, increment=True):
    """
    Controla tentativas por IP com opção de não incrementar (apenas verificar)

    Args:
        request: Request object
        key_prefix: Prefixo para a chave do cache
        limit: Limite de tentativas (padrão: 5)
        timeout: Timeout em segundos (padrão: 300 = 5 minutos)
        increment: Se deve incrementar o contador (padrão: True)

    Returns:
        int: Número atual de tentativas
    """
    ip = request.META.get('REMOTE_ADDR')
    cache_key = f'{key_prefix}:{ip}'
    current_attempts = cache.get(cache_key, 0)

    if increment:
        current_attempts += 1
        cache.set(cache_key, current_attempts, timeout=timeout)

    return current_attempts


def should_check_attempts(request, action_type):
    """
    Determina se devemos verificar limite de tentativas baseado no contexto

    Args:
        request: Request object
        action_type: Tipo de ação ('login', 'register', etc.)

    Returns:
        bool: True se deve verificar tentativas
    """
    # Não verificar se usuário está logado
    if request.user.is_authenticated:
        return False

    # Verificar apenas em POST (tentativas reais)
    if request.method != 'POST':
        return False

    # Verificar se não estamos em uma página de aviso
    if hasattr(request, 'resolver_match') and request.resolver_match:
        view_name = request.resolver_match.url_name
        if view_name and 'already_logged_in' in view_name:
            return False

    return True


# --- Login LDAP ---
@require_http_methods(["GET", "POST"])
@csrf_protect
def ldap_login(request):
    """View para autenticação via LDAP"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Validar campos
        if not username or not password:
            messages.error(request, 'Por favor, preencha todos os campos.')
            return render(request, 'accounts/ldap_login.html')

        # Verificar tentativas de login
        if limit_attempts(request, 'ldap_login_attempts') > 5:
            messages.error(request, 'Muitas tentativas. Tente novamente em 5 minutos.')
            return redirect('accounts:ldap_login')

        # Obter configurações LDAP
        ldap_config = LDAPConfig.objects.filter(is_active=True).first()
        if not ldap_config:
            messages.error(request, 'Configuração LDAP não encontrada ou inativa.')
            logger.error('Tentativa de login LDAP sem configuração ativa')
            return render(request, 'accounts/ldap_login.html')

        try:
            # Configurar TLS para conexão segura
            tls_config = Tls(validate=ssl.CERT_NONE)  # Em produção, use CERT_REQUIRED

            # Conectar ao servidor LDAP
            server_uri = ldap_config.server_uri
            if not server_uri.startswith(('ldap://', 'ldaps://')):
                server_uri = f'ldap://{server_uri}'

            server = Server(server_uri, get_info=ALL, tls=tls_config)

            # Tentar conexão com o servidor
            try:
                conn = Connection(
                    server,
                    user=f"{ldap_config.bind_dn}\\{username}",
                    password=password,
                    auto_bind=True
                )
            except Exception as conn_error:
                logger.error(f'Erro de conexão LDAP: {str(conn_error)}')

                # Verificar o tipo de erro para fornecer mensagens mais específicas
                error_str = str(conn_error).lower()

                if 'invalidcredentials' in error_str or 'invalid credentials' in error_str:
                    messages.error(request, 'Senha incorreta. Por favor, verifique suas credenciais corporativas.')
                elif 'user not found' in error_str or 'no such user' in error_str:
                    messages.error(request, 'Usuário não encontrado no diretório corporativo.')
                elif 'timeout' in error_str:
                    messages.error(request, 'Tempo de conexão esgotado. O servidor LDAP pode estar indisponível.')
                elif 'connection' in error_str:
                    messages.error(request, 'Não foi possível conectar ao servidor LDAP. Verifique sua conexão de rede.')
                else:
                    messages.error(request, 'Não foi possível conectar ao servidor LDAP. Verifique com o administrador.')

                # Adicionar classe de erro ao formulário
                return render(request, 'accounts/ldap_login.html', {'error_field': 'password'})

            # Se chegou aqui, a autenticação foi bem-sucedida
            # Verificar se o usuário existe no Django ou criar um novo
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Criar novo usuário
                email = f"{username}@{ldap_config.domain}" if ldap_config.domain else f"{username}@example.com"
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=None  # Não definimos senha local para usuários LDAP
                )
                user.set_unusable_password()
                user.is_active = True  # Ativar o usuário imediatamente
                user.save()

                # Registrar a criação do usuário
                logger.info(f'Novo usuário LDAP criado: {username}')

            # Fazer login do usuário
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Bem-vindo, {username}! Login LDAP realizado com sucesso.')
            return redirect('accounts:profile')

        except Exception as e:
            messages.error(request, 'Falha na autenticação LDAP. Verifique suas credenciais.')
            logger.error(f'Erro LDAP: {str(e)}')

    return render(request, 'accounts/ldap_login.html')

# --- Registro ---
@method_decorator(anonymous_required, name='dispatch')
class RegisterView(CreateView):
    template_name = 'accounts/register.html'
    form_class = CustomUserCreationForm

    def dispatch(self, request, *args, **kwargs):
        # Verificar limite de tentativas apenas quando apropriado
        if should_check_attempts(request, 'register'):
            if limit_attempts(request, 'register_attempts', increment=False) >= 5:
                messages.error(request, 'Muitas tentativas. Tente novamente mais tarde.')
                return redirect('accounts:register')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if User.objects.filter(email=form.cleaned_data['email']).exists():
            form.add_error('email', 'Este email já está cadastrado')
            # Incrementar tentativas apenas em erro real
            limit_attempts(self.request, 'register_attempts', increment=True)
            return self.form_invalid(form)

        try:
            user = form.save(commit=False)
            user.is_active = False
            # Garantir que usuários registrados publicamente não tenham privilégios administrativos
            user.is_staff = False
            user.is_superuser = False
            user.save()

            # Adicionar usuário ao grupo "Usuario" por padrão
            usuario_group, created = Group.objects.get_or_create(name='Usuario')
            user.groups.add(usuario_group)

            # Gerar código de ativação
            codigo = user.gerar_codigo_ativacao()

            # Enviar email com código
            subject = "Código de Ativação da Conta"

            # Criar URL absoluta para ativação
            ativar_url = reverse('accounts:ativar_conta')
            activation_link = self.request.build_absolute_uri(ativar_url) + f'?email={user.email}'

            message = render_to_string('accounts/email_codigo_ativacao.html', {
                'user': user,
                'codigo': codigo,
                'request': self.request,
                'activation_link': activation_link,
            })

            email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            email.content_subtype = "html"
            email.send()

            messages.info(
                self.request,
                f"Conta criada com sucesso! Enviamos um código de ativação para {user.email}. "
                f"Verifique seu email e digite o código para ativar sua conta."
            )
            # Redirecionar com email como parâmetro
            url = reverse('accounts:ativar_conta')
            params = urlencode({'email': user.email})
            return HttpResponseRedirect(f'{url}?{params}')

        except Exception as e:
            logger.error(f"Erro ao enviar e-mail de ativação: {e}")
            messages.error(self.request, "Erro ao enviar e-mail. Tente novamente.")
            return self.form_invalid(form)

# --- Ativação por código ---
@method_decorator(inactive_user_only, name='dispatch')
class AtivarContaView(TemplateView):
    """View para inserir código de ativação"""
    template_name = 'accounts/ativar_conta.html'

    def dispatch(self, request, *args, **kwargs):
        # Verificar se usuário já está logado e ativo
        if request.user.is_authenticated and request.user.is_active:
            messages.info(
                request,
                "🎉 Sua conta já está ativa! Você já está logado no sistema."
            )
            return redirect('accounts:profile')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Pegar email da URL se fornecido
        email_param = self.request.GET.get('email', '')

        # Verificar status do usuário se email foi fornecido
        user_status = None
        if email_param:
            try:
                user = User.objects.get(email=email_param)
                if user.is_active:
                    user_status = 'active'
                else:
                    user_status = 'inactive'
            except User.DoesNotExist:
                user_status = 'not_found'

        # Criar formulários com email pré-preenchido se fornecido
        initial_data = {'email': email_param} if email_param else {}
        context['form'] = CodigoAtivacaoForm(initial=initial_data)
        context['solicitar_form'] = SolicitarCodigoForm(initial=initial_data)
        context['email_param'] = email_param
        context['user_status'] = user_status

        return context

    def post(self, request, *args, **kwargs):
        form = CodigoAtivacaoForm(request.POST)
        solicitar_form = SolicitarCodigoForm()

        if form.is_valid():
            email = form.cleaned_data['email']
            codigo = form.cleaned_data['codigo']

            try:
                user = User.objects.get(email=email, is_active=False)

                # Verificar se o usuário tem código de ativação
                if not user.codigo_ativacao:
                    messages.error(
                        request,
                        "❌ Esta conta não possui um código de ativação válido. "
                        "Solicite um novo código abaixo."
                    )
                else:
                    valido, mensagem = user.verificar_codigo_ativacao(codigo)

                    if valido:
                        # Ativar a conta
                        user.is_active = True
                        user.email_verificado = True
                        user.limpar_codigo_ativacao()
                        user.save()

                        # Fazer login automático
                        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                        messages.success(
                            request,
                            "🎉 Conta ativada com sucesso! Você foi logado automaticamente. "
                            "Bem-vindo ao sistema!"
                        )
                        return redirect('accounts:profile')
                    else:
                        # Fornecer feedback específico baseado no tipo de erro
                        if "expirado" in mensagem.lower():
                            messages.error(
                                request,
                                f"⏰ {mensagem} Use o formulário abaixo para solicitar um novo código."
                            )
                        elif "muitas tentativas" in mensagem.lower():
                            messages.error(
                                request,
                                f"🚫 {mensagem} Use o formulário abaixo para solicitar um novo código."
                            )
                        else:
                            messages.error(request, f"❌ {mensagem}")

            except User.DoesNotExist:
                messages.error(
                    request,
                    "❌ Email não encontrado ou conta já ativada. "
                    "Verifique se o email está correto."
                )
        else:
            # Mostrar erros de validação do formulário
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f"❌ {error}")
                    else:
                        field_name = form.fields[field].label or field
                        messages.error(request, f"❌ {field_name}: {error}")

        context = self.get_context_data()
        context['form'] = form
        context['solicitar_form'] = solicitar_form
        return render(request, self.template_name, context)


class SolicitarCodigoView(View):
    """View para solicitar novo código de ativação"""

    def post(self, request, *args, **kwargs):
        form = SolicitarCodigoForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                user = User.objects.get(email=email, is_active=False)

                # Verificar se pode gerar novo código (limite de tempo)
                if user.codigo_ativacao_criado_em:
                    from django.utils import timezone
                    from datetime import timedelta

                    tempo_limite = user.codigo_ativacao_criado_em + timedelta(minutes=5)
                    if timezone.now() < tempo_limite:
                        tempo_restante = (tempo_limite - timezone.now()).seconds // 60 + 1
                        messages.warning(
                            request,
                            f"⏰ Aguarde {tempo_restante} minutos antes de solicitar um novo código."
                        )
                        return redirect('accounts:ativar_conta')

                # Gerar novo código
                codigo = user.gerar_codigo_ativacao()

                # Enviar email
                subject = "Novo Código de Ativação"

                # Criar URL absoluta para ativação
                ativar_url = reverse('accounts:ativar_conta')
                activation_link = request.build_absolute_uri(ativar_url) + f'?email={user.email}'

                message = render_to_string('accounts/email_codigo_ativacao.html', {
                    'user': user,
                    'codigo': codigo,
                    'novo_codigo': True,
                    'activation_link': activation_link,
                })

                email_obj = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
                email_obj.content_subtype = "html"
                email_obj.send()

                messages.success(
                    request,
                    f"📧 Novo código enviado para {user.email}. Verifique sua caixa de entrada."
                )

            except User.DoesNotExist:
                messages.error(request, "❌ Email não encontrado ou conta já ativada.")
            except Exception as e:
                logger.error(f"Erro ao enviar novo código: {e}")
                messages.error(request, "❌ Erro ao enviar código. Tente novamente.")

        return redirect('accounts:ativar_conta')


# --- Perfil ---
@method_decorator(account_activation_required, name='dispatch')
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def dispatch(self, request, *args, **kwargs):
        # Adicionar cabeçalhos para prevenir cache
        response = super().dispatch(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UserProfileForm(instance=self.request.user)
        return context

# --- Editar Perfil ---
@method_decorator(account_activation_required, name='dispatch')
class EditProfileView(LoginRequiredMixin, UpdateView):
    form_class = EditProfileForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def dispatch(self, request, *args, **kwargs):
        # Adicionar cabeçalhos para prevenir cache
        response = super().dispatch(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Perfil atualizado com sucesso!")
        return super().form_valid(form)


# --- Configurações administrativas ---
@method_decorator(admin_or_superuser_required, name='dispatch')
class AdminSettingsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'accounts/admin_settings.html'

    def test_func(self):
        # Verificar se o usuário é um administrador
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Você não tem permissão para acessar esta página.")
        return redirect('accounts:profile')

    def get(self, request):
        # Obter configurações sociais
        google_settings = SocialAuthSettings.objects.filter(provider='google').first()
        github_settings = SocialAuthSettings.objects.filter(provider='github').first()

        # Obter configurações de email
        from apps.config.models import EmailConfig
        email_config = EmailConfig.objects.filter(is_active=True).first()

        # Obter configurações LDAP
        ldap_config = LDAPConfig.objects.filter(is_active=True).first()

        # Preparar dados iniciais para formulários
        social_initial = {}
        if google_settings:
            social_initial.update({
                'google_client_id': google_settings.client_id,
                'google_secret': google_settings.secret
            })
        if github_settings:
            social_initial.update({
                'github_client_id': github_settings.client_id,
                'github_secret': github_settings.secret
            })

        email_initial = {}
        if email_config:
            email_initial = {
                'host': email_config.email_host,
                'port': email_config.email_port,
                'user': email_config.email_host_user,
                'password': email_config.email_host_password,
                'use_tls': email_config.email_use_tls
            }

        ldap_initial = {}
        if ldap_config:
            ldap_initial = {
                'server_uri': ldap_config.server_uri,
                'bind_dn': ldap_config.bind_dn,
                'bind_password': ldap_config.bind_password,
                'domain': ldap_config.domain,
                'user_search_base': ldap_config.base_dn,
                'group_search_base': ''  # Não temos este campo no modelo ainda
            }

        context = {
            'email_form': EmailSettingsForm(initial=email_initial),
            'social_form': SocialAuthSettingsForm(initial=social_initial),
            'ldap_form': LDAPSettingsForm(initial=ldap_initial),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form_type = request.POST.get('form_type')

        if form_type == 'email_settings':
            form = EmailSettingsForm(request.POST)
            if form.is_valid():
                try:
                    # Salvar no modelo em vez de modificar settings diretamente
                    email_config, created = EmailConfig.objects.get_or_create(
                        slug='email-config',
                        defaults={
                            'email_host': form.cleaned_data['host'],
                            'email_port': form.cleaned_data['port'],
                            'email_host_user': form.cleaned_data['user'],
                            'email_host_password': form.cleaned_data['password'],
                            'email_use_tls': form.cleaned_data['use_tls'],
                            'default_from_email': form.cleaned_data['user'],
                            'is_active': True
                        }
                    )

                    if not created:
                        email_config.email_host = form.cleaned_data['host']
                        email_config.email_port = form.cleaned_data['port']
                        email_config.email_host_user = form.cleaned_data['user']
                        email_config.email_host_password = form.cleaned_data['password']
                        email_config.email_use_tls = form.cleaned_data['use_tls']
                        email_config.save()

                    # Atualizar as configurações em tempo de execução
                    settings.EMAIL_HOST = form.cleaned_data['host']
                    settings.EMAIL_PORT = form.cleaned_data['port']
                    settings.EMAIL_HOST_USER = form.cleaned_data['user']
                    settings.EMAIL_HOST_PASSWORD = form.cleaned_data['password']
                    settings.EMAIL_USE_TLS = form.cleaned_data['use_tls']

                    # Testar a conexão com o servidor de email
                    try:
                        from django.core.mail import get_connection
                        connection = get_connection()
                        connection.open()
                        connection.close()
                        messages.success(request, 'Configurações de email atualizadas e testadas com sucesso!')
                    except Exception as e:
                        logger.warning(f"Configurações de email salvas, mas o teste de conexão falhou: {e}")
                        messages.warning(request, 'Configurações de email salvas, mas não foi possível testar a conexão. Verifique os dados.')
                except Exception as e:
                    logger.error(f"Erro ao salvar configurações de email: {e}")
                    messages.error(request, f'Erro ao salvar configurações de email: {str(e)}')
                    return self.get(request)
            else:
                messages.error(request, 'Verifique os erros no formulário de email.')
                return self.get(request)

        elif form_type == 'social_settings':
            form = SocialAuthSettingsForm(request.POST)
            if form.is_valid():
                try:
                    google_settings, _ = SocialAuthSettings.objects.get_or_create(provider='google')
                    google_settings.client_id = form.cleaned_data['google_client_id']
                    google_settings.secret = form.cleaned_data['google_secret']
                    google_settings.save()

                    github_settings, _ = SocialAuthSettings.objects.get_or_create(provider='github')
                    github_settings.client_id = form.cleaned_data['github_client_id']
                    github_settings.secret = form.cleaned_data['github_secret']
                    github_settings.save()

                    messages.success(request, 'Autenticação social atualizada com sucesso!')
                except Exception as e:
                    logger.error(f"Erro ao salvar configurações de autenticação social: {e}")
                    messages.error(request, f'Erro ao salvar configurações de autenticação social: {str(e)}')
                    return self.get(request)
            else:
                messages.error(request, 'Verifique os erros no formulário de autenticação social.')
                return self.get(request)

        elif form_type == 'ldap_settings':
            form = LDAPSettingsForm(request.POST)
            if form.is_valid():
                try:
                    # Extrair servidor e porta da URI
                    server_uri = form.cleaned_data['server_uri']
                    if server_uri.startswith('ldap://'):
                        server_uri = server_uri[7:]  # Remover 'ldap://'
                    elif server_uri.startswith('ldaps://'):
                        server_uri = server_uri[8:]  # Remover 'ldaps://'

                    server_parts = server_uri.split(':')
                    server = server_parts[0]
                    port = 389  # Porta padrão LDAP

                    if len(server_parts) > 1:
                        try:
                            port = int(server_parts[1])
                        except ValueError:
                            form.add_error('server_uri', 'Formato de URI inválido. Use ldap://servidor:porta')
                            messages.error(request, 'Verifique os erros no formulário.')
                            return self.get(request)

                    # Configurar TLS para conexão segura
                    tls_config = Tls(validate=ssl.CERT_NONE)  # Em produção, use CERT_REQUIRED

                    # Tentar conectar ao servidor LDAP para validar as configurações
                    try:
                        test_server = Server(f"ldap://{server}:{port}", get_info=ALL, tls=tls_config)
                        test_conn = Connection(
                            test_server,
                            user=form.cleaned_data['bind_dn'],
                            password=form.cleaned_data['bind_password'],
                            auto_bind=True
                        )
                        test_conn.unbind()
                    except Exception as e:
                        logger.error(f"Erro ao testar conexão LDAP: {e}")
                        form.add_error('server_uri', f'Não foi possível conectar ao servidor LDAP: {str(e)}')
                        messages.error(request, 'Não foi possível conectar ao servidor LDAP. Verifique as configurações.')
                        return self.get(request)

                    # Salvar configurações LDAP
                    ldap_config, created = LDAPConfig.objects.get_or_create(
                        slug='ldap-config',
                        defaults={
                            'server_uri': form.cleaned_data['server_uri'],
                            'server': server,
                            'port': port,
                            'base_dn': form.cleaned_data['user_search_base'],
                            'bind_dn': form.cleaned_data['bind_dn'],
                            'bind_password': form.cleaned_data['bind_password'],
                            'domain': form.cleaned_data['domain'],
                            'is_active': True
                        }
                    )

                    if not created:
                        ldap_config.server_uri = form.cleaned_data['server_uri']
                        ldap_config.server = server
                        ldap_config.port = port
                        ldap_config.base_dn = form.cleaned_data['user_search_base']
                        ldap_config.bind_dn = form.cleaned_data['bind_dn']
                        ldap_config.bind_password = form.cleaned_data['bind_password']
                        ldap_config.domain = form.cleaned_data['domain']
                        ldap_config.is_active = True
                        ldap_config.save()

                    messages.success(request, 'Configurações LDAP atualizadas com sucesso!')
                except Exception as e:
                    logger.error(f"Erro ao salvar configurações LDAP: {e}")
                    messages.error(request, f'Erro ao salvar configurações LDAP: {str(e)}')
                    return self.get(request)
            else:
                messages.error(request, 'Verifique os erros no formulário LDAP.')
                return self.get(request)
        else:
            messages.error(request, 'Formulário inválido.')
            return self.get(request)

        return redirect('accounts:admin_settings')


# --- Páginas de aviso para usuários já logados ---
class AlreadyLoggedInRegisterView(TemplateView):
    """
    Página de aviso quando usuário logado tenta acessar o registro
    """
    template_name = 'accounts/already_logged_in_register.html'

    def dispatch(self, request, *args, **kwargs):
        # Verificar se o usuário está logado, senão redirecionar para login
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class AlreadyLoggedInLoginView(TemplateView):
    """
    Página de aviso quando usuário logado tenta acessar o login
    """
    template_name = 'accounts/already_logged_in_login.html'

    def dispatch(self, request, *args, **kwargs):
        # Verificar se o usuário está logado, senão redirecionar para login
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


# --- Login personalizado ---
@method_decorator(anonymous_required, name='dispatch')
class CustomLoginView(LoginView):
    form_class = AuthenticationForm
    template_name = 'accounts/login.html'

    def dispatch(self, request, *args, **kwargs):
        # Adicionar cabeçalhos para prevenir cache
        response = super().dispatch(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def form_invalid(self, form):
        # Incrementar tentativas apenas em tentativas reais de login falhadas
        if should_check_attempts(self.request, 'login'):
            current_attempts = limit_attempts(self.request, 'login_attempts', increment=True)
            if current_attempts > 5:
                messages.error(self.request, 'Muitas tentativas. Tente novamente em 5 minutos.')
                return redirect('accounts:login')

        # Verificar se há erros específicos para fornecer mensagens mais claras
        if form.errors:
            # Verificar se há erro de credenciais inválidas
            if '__all__' in form.errors:
                for error in form.errors['__all__']:
                    if 'Please enter a correct username and password' in error:
                        messages.error(self.request, 'Senha incorreta. Por favor, verifique suas credenciais.')
                    else:
                        messages.error(self.request, error)

            # Verificar erros específicos de campo
            if 'username' in form.errors:
                messages.error(self.request, 'Nome de usuário inválido ou não encontrado.')

            if 'password' in form.errors:
                messages.error(self.request, 'Senha inválida. Por favor, tente novamente.')

        return super().form_invalid(form)

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_active:
            messages.error(self.request, "Conta inativa. Verifique seu e-mail para ativar.")
            return redirect('accounts:login')

        # Registrar o login bem-sucedido
        logger.info(f"Login bem-sucedido para o usuário: {user.username}")

        # Mensagem de boas-vindas com aviso sobre múltiplas contas
        messages.success(
            self.request,
            f'🎉 Bem-vindo de volta, {user.get_full_name() or user.username}! '
            f'Você está logado no sistema. ⚠️ Para usar uma conta diferente, '
            f'faça logout primeiro.'
        )

        return super().form_valid(form)


# --- LOGOUT PERSONALIZADO ---
class CustomLogoutView(View):
    """View personalizada para logout que aceita GET e POST"""

    def get(self, request, *args, **kwargs):
        """Fazer logout via GET"""
        return self._do_logout(request)

    def post(self, request, *args, **kwargs):
        """Fazer logout via POST"""
        return self._do_logout(request)

    def _do_logout(self, request):
        """Executa o logout do usuário"""
        if request.user.is_authenticated:
            username = request.user.get_full_name() or request.user.username

            # Mensagem de despedida com aviso sobre múltiplas contas
            messages.warning(
                request,
                f'👋 Até logo, {username}! Você saiu do sistema com sucesso. '
                f'⚠️ Agora você pode fazer login com uma conta diferente se necessário.'
            )

            logout(request)

        # Redirecionar para a página inicial
        response = redirect('pages:home')

        # Adicionar cabeçalhos para prevenir cache
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        return response


# =============================================================================
# GESTÃO DE USUÁRIOS
# =============================================================================

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Lista todos os usuários do sistema com otimizações de performance"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name='Administrador').exists()

    def get_queryset(self):
        # Otimização: select_related para ForeignKeys e prefetch_related para ManyToMany
        queryset = User.objects.select_related(
            'cargo', 'departamento'
        ).prefetch_related(
            'groups'
        ).annotate(
            # Adicionar anotações para evitar consultas extras
            total_grupos=models.Count('groups'),
            ultimo_login_formatado=models.Case(
                models.When(last_login__isnull=True, then=models.Value('Nunca')),
                default=models.F('last_login'),
                output_field=models.CharField()
            )
        )

        # Filtros de busca com índices otimizados
        search = self.request.GET.get('search')
        if search:
            # Usar Q objects para busca eficiente
            search_query = (
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
            queryset = queryset.filter(search_query)

        # Filtro por cargo
        cargo_filter = self.request.GET.get('cargo')
        if cargo_filter:
            queryset = queryset.filter(cargo_id=cargo_filter)

        # Filtro por departamento
        departamento_filter = self.request.GET.get('departamento')
        if departamento_filter:
            queryset = queryset.filter(departamento_id=departamento_filter)

        # Filtro por grupo
        group_filter = self.request.GET.get('group')
        if group_filter:
            queryset = queryset.filter(groups__name=group_filter).distinct()

        # Filtro por status
        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status_filter == 'blocked':
            queryset = queryset.filter(bloqueado_ate__gt=timezone.now())
        elif status_filter == 'unverified':
            queryset = queryset.filter(email_verificado=False)

        # Ordenação otimizada
        order_by = self.request.GET.get('order_by', '-created_at')
        if order_by in ['username', '-username', 'email', '-email', 'created_at', '-created_at', 'last_login', '-last_login']:
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Cache para dados que não mudam frequentemente
        from django.core.cache import cache

        # Grupos (cache por 10 minutos)
        groups = cache.get('user_list_groups')
        if groups is None:
            groups = list(Group.objects.values('id', 'name').order_by('name'))
            cache.set('user_list_groups', groups, 600)
        context['groups'] = groups

        # Cargos e Departamentos (cache por 10 minutos)
        cargos = cache.get('user_list_cargos')
        if cargos is None:
            cargos = list(Cargo.objects.filter(ativo=True).values('id', 'nome').order_by('nome'))
            cache.set('user_list_cargos', cargos, 600)
        context['cargos'] = cargos

        departamentos = cache.get('user_list_departamentos')
        if departamentos is None:
            departamentos = list(Departamento.objects.filter(ativo=True).values('id', 'nome').order_by('nome'))
            cache.set('user_list_departamentos', departamentos, 600)
        context['departamentos'] = departamentos

        # Parâmetros de filtro
        context.update({
            'search': self.request.GET.get('search', ''),
            'group_filter': self.request.GET.get('group', ''),
            'cargo_filter': self.request.GET.get('cargo', ''),
            'departamento_filter': self.request.GET.get('departamento', ''),
            'status_filter': self.request.GET.get('status', ''),
            'order_by': self.request.GET.get('order_by', '-created_at'),
        })

        # Estatísticas (cache por 5 minutos)
        stats = cache.get('user_list_stats')
        if stats is None:
            stats = {
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'blocked_users': User.objects.filter(bloqueado_ate__gt=timezone.now()).count(),
                'unverified_users': User.objects.filter(email_verificado=False).count(),
            }
            cache.set('user_list_stats', stats, 300)
        context['stats'] = stats

        return context


class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Criar novo usuário"""
    model = User
    form_class = UserManagementForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name='Administrador').exists()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save(commit=False)

        # Verificar se é usuário LDAP (não tem senha utilizável)
        is_ldap_user = not user.has_usable_password() if hasattr(user, 'has_usable_password') else False

        if is_ldap_user:
            # Usuários LDAP são ativados automaticamente
            user.is_active = True
        else:
            # Usuários normais precisam confirmar email
            user.is_active = False

        # Salvar o usuário primeiro
        user.save()

        # Gerenciar grupos - SEMPRE garantir que novos usuários tenham pelo menos "Usuario"
        groups = form.cleaned_data.get('groups')
        usuario_group, created = Group.objects.get_or_create(name='Usuario')

        if groups:
            # Garantir que o grupo "Usuario" sempre esteja incluído
            if usuario_group not in groups:
                groups = list(groups) + [usuario_group]
            user.groups.set(groups)
        else:
            # Se nenhum grupo foi selecionado, adicionar ao grupo "Usuario" por padrão
            user.groups.add(usuario_group)

        # Salvar relações many-to-many
        form.save_m2m()

        if is_ldap_user:
            # Usuário LDAP - ativação automática
            messages.success(
                self.request,
                f'✅ Usuário LDAP {user.username} criado com sucesso! '
                f'O usuário foi ativado automaticamente e pode fazer login via LDAP.'
            )
        else:
            # Usuário normal - enviar email com código de ativação
            try:
                codigo = user.gerar_codigo_ativacao()

                subject = "Código de Ativação da Conta"
                message = render_to_string('accounts/email_admin_created_user_codigo.html', {
                    'user': user,
                    'codigo': codigo,
                    'admin_user': self.request.user,
                })

                email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
                email.content_subtype = "html"
                email.send()

                messages.success(
                    self.request,
                    f'✅ Usuário {user.username} criado com sucesso! '
                    f'Um código de ativação foi enviado para {user.email}. '
                    f'O usuário deve acessar: {self.request.build_absolute_uri(reverse("accounts:ativar_conta"))}?email={user.email}'
                )
            except Exception as e:
                logger.error(f"Erro ao enviar email de confirmação: {e}")
                messages.warning(
                    self.request,
                    f'⚠️ Usuário {user.username} criado, mas houve erro ao enviar email de confirmação. '
                    f'Você pode reenviar o email de confirmação posteriormente.'
                )

        return super().form_valid(form)

    def send_confirmation_email(self, user):
        """Enviar email de confirmação para o usuário"""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.template.loader import render_to_string
        from django.core.mail import EmailMessage
        from django.conf import settings
        from django.urls import reverse

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_link = self.request.build_absolute_uri(
            reverse('accounts:activate', kwargs={'uidb64': uid, 'token': token})
        )

        subject = "Confirme sua conta - Criada por Administrador"
        message = render_to_string('accounts/email_admin_created_user.html', {
            'user': user,
            'activation_link': activation_link,
            'admin_user': self.request.user,
        })

        email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        email.content_subtype = "html"
        email.send()


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Editar usuário existente"""
    model = User
    form_class = UserManagementForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name='Administrador').exists()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        old_username = self.get_object().username

        # Atualizar grupos
        groups = form.cleaned_data.get('groups')
        if groups:
            user.groups.set(groups)
        else:
            # Se nenhum grupo foi selecionado, manter pelo menos "Usuario"
            usuario_group, created = Group.objects.get_or_create(name='Usuario')
            user.groups.set([usuario_group])

        # Verificar se a senha foi alterada
        password_changed = form.cleaned_data.get('password1')

        success_message = f'✅ Usuário {user.username} atualizado com sucesso!'
        if password_changed:
            success_message += ' A senha foi alterada.'
        if old_username != user.username:
            success_message += f' Nome de usuário alterado de "{old_username}" para "{user.username}".'

        messages.success(self.request, success_message)
        return super().form_valid(form)


class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Deletar usuário"""
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name='Administrador').exists()

    def delete(self, request, *args, **kwargs):
        user = self.get_object()

        # Validações de segurança
        if user == request.user:
            messages.error(
                request,
                '🚫 Você não pode deletar sua própria conta! '
                'Solicite a outro administrador para realizar esta ação.'
            )
            return redirect('accounts:user_list')

        if user.is_superuser:
            messages.error(
                request,
                '🛡️ Não é possível deletar superusuários por questões de segurança! '
                'Remova os privilégios de superusuário antes de tentar deletar.'
            )
            return redirect('accounts:user_list')

        # Verificar se é o último administrador
        admin_count = User.objects.filter(
            Q(is_staff=True) | Q(groups__name='Administrador')
        ).exclude(pk=user.pk).count()

        if (user.is_staff or user.groups.filter(name='Administrador').exists()) and admin_count == 0:
            messages.error(
                request,
                '⚠️ Não é possível deletar o último administrador do sistema! '
                'Crie outro administrador antes de deletar este usuário.'
            )
            return redirect('accounts:user_list')

        username = user.username
        user_groups = list(user.groups.values_list('name', flat=True))

        response = super().delete(request, *args, **kwargs)

        messages.success(
            request,
            f'🗑️ Usuário {username} deletado com sucesso! '
            f'Grupos que o usuário pertencia: {", ".join(user_groups) if user_groups else "Nenhum"}'
        )
        return response


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Visualizar detalhes do usuário"""
    template_name = 'accounts/user_detail.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name='Administrador').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = kwargs.get('pk')
        context['user_obj'] = get_object_or_404(User, pk=user_id)
        return context


class UserToggleStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Ativar/Desativar usuário via AJAX"""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name='Administrador').exists()

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        # Validações de segurança
        if user == request.user:
            return JsonResponse({
                'success': False,
                'message': '🚫 Você não pode desativar sua própria conta!'
            })

        if user.is_superuser:
            return JsonResponse({
                'success': False,
                'message': '🛡️ Não é possível desativar superusuários por questões de segurança!'
            })

        # Verificar se é o último administrador ativo
        if user.is_active and (user.is_staff or user.groups.filter(name='Administrador').exists()):
            admin_count = User.objects.filter(
                Q(is_staff=True) | Q(groups__name='Administrador'),
                is_active=True
            ).exclude(pk=user.pk).count()

            if admin_count == 0:
                return JsonResponse({
                    'success': False,
                    'message': '⚠️ Não é possível desativar o último administrador ativo do sistema!'
                })

        # Alterar status
        old_status = user.is_active
        user.is_active = not user.is_active
        user.save()

        status = 'ativado' if user.is_active else 'desativado'
        icon = '✅' if user.is_active else '⏸️'

        return JsonResponse({
            'success': True,
            'message': f'{icon} Usuário {user.username} {status} com sucesso!',
            'is_active': user.is_active,
            'old_status': old_status
        })


# =============================================================================
# ALTERAÇÃO DE SENHA COM CONFIRMAÇÃO POR EMAIL
# =============================================================================

class PasswordChangeRequestView(LoginRequiredMixin, TemplateView):
    """Solicitar alteração de senha via email"""
    template_name = 'accounts/password_change_request.html'

    def post(self, request):
        """Enviar email de confirmação para alteração de senha"""
        user = request.user

        # Verificar se é usuário LDAP
        if not user.has_usable_password():
            messages.error(
                request,
                '🏢 Usuários LDAP não podem alterar senha através do sistema. '
                'Entre em contato com o administrador de rede para alterar sua senha corporativa.'
            )
            return redirect('accounts:profile')

        try:
            # Gerar token para alteração de senha
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Criar link de confirmação
            confirmation_link = request.build_absolute_uri(
                reverse('accounts:password_change_confirm', kwargs={'uidb64': uid, 'token': token})
            )

            # Enviar email
            subject = "Confirmação para Alteração de Senha"
            message = render_to_string('accounts/email_password_change_request.html', {
                'user': user,
                'confirmation_link': confirmation_link,
            })

            email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            email.content_subtype = "html"
            email.send()

            messages.success(
                request,
                f'📧 Email de confirmação enviado para {user.email}. '
                f'Clique no link recebido para confirmar a alteração de senha.'
            )

        except Exception as e:
            logger.error(f"Erro ao enviar email de confirmação de senha: {e}")
            messages.error(
                request,
                '❌ Erro ao enviar email de confirmação. Tente novamente mais tarde.'
            )

        return redirect('accounts:profile')


class PasswordChangeConfirmView(TemplateView):
    """Confirmar alteração de senha via token do email"""
    template_name = 'accounts/password_change_form.html'

    def get(self, request, uidb64, token):
        """Verificar token e exibir formulário de alteração"""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            # Token válido - exibir formulário
            context = {
                'validlink': True,
                'user': user,
                'uidb64': uidb64,
                'token': token
            }
            return render(request, self.template_name, context)
        else:
            # Token inválido
            context = {'validlink': False}
            return render(request, self.template_name, context)

    def post(self, request, uidb64, token):
        """Processar alteração de senha"""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')

            # Validações
            if not password1 or not password2:
                messages.error(request, 'Por favor, preencha todos os campos.')
                return self.get(request, uidb64, token)

            if password1 != password2:
                messages.error(request, 'As senhas não coincidem.')
                return self.get(request, uidb64, token)

            # Validar força da senha
            try:
                validate_password(password1, user)
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
                return self.get(request, uidb64, token)

            # Alterar senha
            user.set_password(password1)
            user.save()

            # Fazer login automático
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            messages.success(
                request,
                '✅ Senha alterada com sucesso! Você foi logado automaticamente.'
            )
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Link inválido ou expirado.')
            return redirect('accounts:login')


# =============================================================================
# REDIRECIONAMENTO DE SIGNUP PARA REGISTER
# =============================================================================

def signup_redirect(request):
    """
    Redireciona qualquer tentativa de acesso a /accounts/signup/ para /accounts/register/
    Mantém compatibilidade com links antigos ou externos
    """
    messages.info(request, 'Redirecionando para a página de registro...')
    return redirect('accounts:register')


