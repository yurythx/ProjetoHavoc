from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CustomUser, Cargo, Departamento, UserAuditLog, SocialAuthSettings


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo', 'total_usuarios', 'created_at']
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome', 'descricao']
    ordering = ['nome']

    def total_usuarios(self, obj):
        return obj.usuarios.count()
    total_usuarios.short_description = 'Total de Usuários'


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'nivel', 'ativo', 'total_usuarios', 'created_at']
    list_filter = ['ativo', 'nivel', 'created_at']
    search_fields = ['nome', 'descricao']
    ordering = ['nivel', 'nome']

    def total_usuarios(self, obj):
        return obj.usuarios.count()
    total_usuarios.short_description = 'Total de Usuários'


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'is_active', 'email_verificado', 'cargo', 'departamento',
        'status_seguranca', 'created_at'
    ]
    list_filter = [
        'is_active', 'email_verificado', 'is_staff', 'is_superuser',
        'cargo', 'departamento', 'provedor_social', 'created_at'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = UserAdmin.fieldsets + (
        ('Informações Pessoais', {
            'fields': ('bio', 'data_nascimento', 'telefone', 'avatar')
        }),
        ('Organização', {
            'fields': ('cargo', 'departamento')
        }),
        ('Autenticação', {
            'fields': ('email_verificado', 'provedor_social', 'uid_social')
        }),
        ('Segurança', {
            'fields': ('ultimo_login_ip', 'tentativas_login_falhadas', 'bloqueado_ate'),
            'classes': ('collapse',)
        }),
        ('Ativação', {
            'fields': ('codigo_ativacao', 'codigo_ativacao_criado_em', 'tentativas_codigo'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'ultimo_login_ip']

    def status_seguranca(self, obj):
        if obj.esta_bloqueado():
            return format_html(
                '<span style="color: red;">🔒 Bloqueado</span>'
            )
        elif obj.tentativas_login_falhadas > 0:
            return format_html(
                '<span style="color: orange;">⚠️ {} tentativas</span>',
                obj.tentativas_login_falhadas
            )
        return format_html('<span style="color: green;">✅ Normal</span>')
    status_seguranca.short_description = 'Status de Segurança'

    actions = ['desbloquear_usuarios', 'resetar_tentativas_login']

    def desbloquear_usuarios(self, request, queryset):
        count = 0
        for user in queryset:
            if user.esta_bloqueado():
                user.desbloquear_conta()
                count += 1
        self.message_user(request, f'{count} usuários desbloqueados.')
    desbloquear_usuarios.short_description = 'Desbloquear usuários selecionados'

    def resetar_tentativas_login(self, request, queryset):
        count = queryset.update(tentativas_login_falhadas=0)
        self.message_user(request, f'Tentativas de login resetadas para {count} usuários.')
    resetar_tentativas_login.short_description = 'Resetar tentativas de login'


@admin.register(UserAuditLog)
class UserAuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'user__email', 'ip_address']
    ordering = ['-timestamp']
    readonly_fields = ['user', 'action', 'ip_address', 'user_agent', 'details', 'timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SocialAuthSettings)
class SocialAuthSettingsAdmin(admin.ModelAdmin):
    list_display = ['provider', 'client_id', 'is_active', 'created_at']
    list_filter = ['provider', 'is_active', 'created_at']
    search_fields = ['provider', 'client_id']
    ordering = ['provider']

    fieldsets = (
        (None, {
            'fields': ('provider', 'client_id', 'secret', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']
