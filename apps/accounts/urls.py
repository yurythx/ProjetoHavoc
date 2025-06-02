from . import views

from django.urls import path, reverse_lazy
from .views import (
    RegisterView, ProfileView, EditProfileView, AdminSettingsView,
    AtivarContaView, SolicitarCodigoView, TestPageView, CustomLoginView, CustomLogoutView,
    UserListView, UserCreateView, UserUpdateView, UserDeleteView,
    UserDetailView, UserToggleStatusView, PasswordChangeRequestView,
    PasswordChangeConfirmView, AlreadyLoggedInRegisterView, AlreadyLoggedInLoginView
)
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    path('ldap/', views.ldap_login, name='ldap_login'),

    path('test/', TestPageView.as_view(), name='test_page'),

    # Ativação de conta por código
    path('ativar/', AtivarContaView.as_view(), name='ativar_conta'),
    path('solicitar-codigo/', SolicitarCodigoView.as_view(), name='solicitar_codigo'),

    # Registro
    path('register/', RegisterView.as_view(), name='register'),

    # Redirecionamento de signup para register (compatibilidade)
    path('signup/', views.signup_redirect, name='signup_redirect'),

    # Login e logout personalizados com mensagens
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    # Páginas de aviso para usuários já logados
    path('already-logged-in/register/', AlreadyLoggedInRegisterView.as_view(), name='already_logged_in_register'),
    path('already-logged-in/login/', AlreadyLoggedInLoginView.as_view(), name='already_logged_in_login'),

    # Perfil
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', EditProfileView.as_view(), name='edit_profile'),

    # Troca de senha com confirmação por email
    path('password_change/', PasswordChangeRequestView.as_view(), name='password_change'),
    path('password_change/confirm/<uidb64>/<token>/', PasswordChangeConfirmView.as_view(), name='password_change_confirm'),

    # Redefinição de senha
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset_form.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url=reverse_lazy('accounts:password_reset_done')),
        name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'),
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('accounts:password_reset_complete')),
        name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'),
        name='password_reset_complete'),

    # Configurações de Administrador
    path('admin/settings/', AdminSettingsView.as_view(), name='admin_settings'),

    # Gestão de Usuários
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('users/<int:pk>/toggle-status/', UserToggleStatusView.as_view(), name='user_toggle_status'),

]