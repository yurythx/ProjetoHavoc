from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import os
import uuid
from typing import Optional

def avatar_upload_path(instance, filename: str) -> str:
    """
    Gera caminho único para upload de avatar
    """
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'avatar/{instance.username}/{filename}'

class Departamento(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, help_text="Descrição do departamento")
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['ativo']),
        ]

    def __str__(self):
        return self.nome

class Cargo(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, help_text="Descrição do cargo")
    nivel = models.PositiveIntegerField(default=1, help_text="Nível hierárquico (1=mais baixo)")
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        ordering = ['nivel', 'nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['nivel']),
            models.Index(fields=['ativo']),
        ]

    def __str__(self):
        return self.nome

class CustomUser(AbstractUser):
    """
    Modelo de usuário personalizado com campos adicionais para:
    - Perfil do usuário (avatar, bio, cargo)
    - Autenticação por email
    - Autenticação social
    """
    # Campos de perfil
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    bio = models.TextField(blank=True, max_length=500)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    data_nascimento = models.DateField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)

    # Campos de autenticação
    is_active = models.BooleanField(default=False)
    email_verificado = models.BooleanField(default=False)  # Tornar default explícito
    ultimo_login_social = models.DateTimeField(null=True, blank=True)
    provedor_social = models.CharField(max_length=30, blank=True)
    uid_social = models.CharField(max_length=255, blank=True)

    # Campos para ativação por código
    codigo_ativacao = models.CharField(max_length=6, blank=True, null=True, db_index=True)
    codigo_ativacao_criado_em = models.DateTimeField(null=True, blank=True)
    tentativas_codigo = models.PositiveIntegerField(default=0)

    # Campos de segurança e auditoria
    ultimo_login_ip = models.GenericIPAddressField(blank=True, null=True)
    tentativas_login_falhadas = models.PositiveIntegerField(default=0)
    bloqueado_ate = models.DateTimeField(blank=True, null=True)

    # Campos de timestamp
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        constraints = [
            models.UniqueConstraint(fields=['email'], name='unique_email_constraint')
        ]
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['email_verificado']),
            models.Index(fields=['codigo_ativacao']),
            models.Index(fields=['created_at']),
        ]

    def get_avatar_url(self):
        return self.avatar.url if self.avatar else '/static/img/default_avatar.png'

    def get_nome_completo(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_full_name(self):
        # Sobrescrever o método padrão para compatibilidade com templates
        return self.get_nome_completo()

    def __str__(self):
        return self.email or self.username

    def clean(self):
        # Validar data de nascimento
        if self.data_nascimento and self.data_nascimento > timezone.now().date():
            raise ValidationError('Data de nascimento não pode ser futura.')

        # Validar email único
        if self.email:
            existing_user = CustomUser.objects.filter(email=self.email).exclude(pk=self.pk).first()
            if existing_user:
                raise ValidationError(f'Este email já está em uso por outro usuário: {existing_user.username}')

    def save(self, *args, **kwargs):
        # Chamar clean() antes de salvar para garantir validação
        self.clean()
        super().save(*args, **kwargs)

    def gerar_codigo_ativacao(self):
        """Gerar um código de ativação de 6 dígitos"""
        import random
        from django.utils import timezone

        self.codigo_ativacao = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.codigo_ativacao_criado_em = timezone.now()
        self.tentativas_codigo = 0
        self.save()
        return self.codigo_ativacao

    def codigo_ativacao_valido(self):
        """Verificar se o código de ativação ainda é válido (30 minutos)"""
        if not self.codigo_ativacao or not self.codigo_ativacao_criado_em:
            return False

        from django.utils import timezone
        from datetime import timedelta

        tempo_limite = self.codigo_ativacao_criado_em + timedelta(minutes=30)
        return timezone.now() <= tempo_limite

    def verificar_codigo_ativacao(self, codigo):
        """Verificar se o código fornecido está correto"""
        if not self.codigo_ativacao_valido():
            return False, "Código expirado. Solicite um novo código."

        if self.tentativas_codigo >= 5:
            return False, "Muitas tentativas incorretas. Solicite um novo código."

        if self.codigo_ativacao == codigo:
            return True, "Código válido."
        else:
            self.tentativas_codigo += 1
            self.save()
            tentativas_restantes = 5 - self.tentativas_codigo
            return False, f"Código incorreto. Você tem {tentativas_restantes} tentativas restantes."

    def limpar_codigo_ativacao(self):
        """Limpar dados do código de ativação após uso"""
        self.codigo_ativacao = None
        self.codigo_ativacao_criado_em = None
        self.tentativas_codigo = 0
        self.save()

    def esta_bloqueado(self) -> bool:
        """Verifica se a conta está bloqueada"""
        if not self.bloqueado_ate:
            return False
        return timezone.now() < self.bloqueado_ate

    def bloquear_conta(self, minutos: int = 30):
        """Bloqueia a conta por um período determinado"""
        from datetime import timedelta
        self.bloqueado_ate = timezone.now() + timedelta(minutes=minutos)
        self.save()

    def desbloquear_conta(self):
        """Desbloqueia a conta"""
        self.bloqueado_ate = None
        self.tentativas_login_falhadas = 0
        self.save()

    def registrar_tentativa_login_falhada(self, ip: Optional[str] = None):
        """Registra uma tentativa de login falhada"""
        self.tentativas_login_falhadas += 1
        if ip:
            self.ultimo_login_ip = ip

        # Bloquear após 5 tentativas falhadas
        if self.tentativas_login_falhadas >= 5:
            self.bloquear_conta(30)  # 30 minutos

        self.save()

    def registrar_login_sucesso(self, ip: Optional[str] = None):
        """Registra um login bem-sucedido"""
        self.tentativas_login_falhadas = 0
        self.bloqueado_ate = None
        if ip:
            self.ultimo_login_ip = ip
        self.save()

    def get_idade(self) -> Optional[int]:
        """Calcula a idade do usuário"""
        if not self.data_nascimento:
            return None

        from datetime import date
        hoje = date.today()
        return hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )


class UserAuditLog(models.Model):
    """
    Log de auditoria para ações importantes dos usuários
    """
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_failed', 'Tentativa de Login Falhada'),
        ('password_change', 'Alteração de Senha'),
        ('profile_update', 'Atualização de Perfil'),
        ('account_activation', 'Ativação de Conta'),
        ('account_blocked', 'Conta Bloqueada'),
        ('account_unblocked', 'Conta Desbloqueada'),
        ('email_verification', 'Verificação de Email'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.get_action_display()} - {self.timestamp}'

    @classmethod
    def log_action(cls, user, action, ip_address=None, user_agent=None, **details):
        """Método conveniente para registrar ações"""
        return cls.objects.create(
            user=user,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )


class SocialAuthSettings(models.Model):
    """
    Configurações para autenticação social
    """
    provider = models.CharField(max_length=30, unique=True)
    client_id = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração de Autenticação Social'
        verbose_name_plural = 'Configurações de Autenticação Social'

    def __str__(self):
        return f'{self.provider} - {self.client_id}'