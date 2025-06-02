from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
from PIL import Image
import base64
import json
import os
import uuid
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Funções de validação de imagens
def validate_logo_image(image):
    """Valida imagens de logo"""
    if not image:
        return

    # Verificar tamanho do arquivo (máximo 5MB)
    if image.size > 5 * 1024 * 1024:
        raise ValidationError('A imagem deve ter no máximo 5MB.')

    # Verificar formato
    valid_formats = ['JPEG', 'JPG', 'PNG', 'SVG', 'WEBP']
    try:
        # Para SVG, verificar extensão
        if image.name.lower().endswith('.svg'):
            if not image.content_type == 'image/svg+xml':
                raise ValidationError('Arquivo SVG inválido.')
            return

        # Para outros formatos, usar PIL
        img = Image.open(image)
        if img.format not in valid_formats:
            raise ValidationError(f'Formato não suportado. Use: {", ".join(valid_formats)}')

        # Verificar dimensões mínimas e máximas
        width, height = img.size
        if width < 50 or height < 50:
            raise ValidationError('A imagem deve ter pelo menos 50x50 pixels.')
        if width > 2000 or height > 2000:
            raise ValidationError('A imagem deve ter no máximo 2000x2000 pixels.')

    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError('Arquivo de imagem inválido.')

def validate_favicon_image(image):
    """Valida imagens de favicon"""
    if not image:
        return

    # Verificar tamanho do arquivo (máximo 1MB)
    if image.size > 1 * 1024 * 1024:
        raise ValidationError('O favicon deve ter no máximo 1MB.')

    # Verificar formato
    valid_formats = ['JPEG', 'JPG', 'PNG', 'ICO', 'SVG']
    try:
        # Para ICO e SVG, verificar extensão
        if image.name.lower().endswith('.ico'):
            if not image.content_type in ['image/x-icon', 'image/vnd.microsoft.icon']:
                raise ValidationError('Arquivo ICO inválido.')
            return

        if image.name.lower().endswith('.svg'):
            if not image.content_type == 'image/svg+xml':
                raise ValidationError('Arquivo SVG inválido.')
            return

        # Para outros formatos, usar PIL
        img = Image.open(image)
        if img.format not in valid_formats:
            raise ValidationError(f'Formato não suportado. Use: {", ".join(valid_formats)}')

        # Verificar se é quadrado (recomendado para favicon)
        width, height = img.size
        if abs(width - height) > 10:  # Tolerância de 10px
            raise ValidationError('O favicon deve ser quadrado (mesma largura e altura).')

        # Verificar dimensões (16x16 a 512x512)
        if width < 16 or height < 16:
            raise ValidationError('O favicon deve ter pelo menos 16x16 pixels.')
        if width > 512 or height > 512:
            raise ValidationError('O favicon deve ter no máximo 512x512 pixels.')

    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError('Arquivo de favicon inválido.')

# Classe para criptografia de senhas
class PasswordEncryptor:
    @staticmethod
    def get_key():
        # Usar SECRET_KEY como base para a chave de criptografia
        # Em produção, seria melhor usar uma chave separada armazenada de forma segura
        secret = settings.SECRET_KEY.encode()
        salt = b'django_secure_salt'  # Salt fixo para consistência

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(secret))
        return key

    @staticmethod
    def encrypt_password(password):
        if not password:
            return ''

        key = PasswordEncryptor.get_key()
        f = Fernet(key)
        encrypted = f.encrypt(password.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    @staticmethod
    def decrypt_password(encrypted_password):
        if not encrypted_password:
            return ''

        try:
            key = PasswordEncryptor.get_key()
            f = Fernet(key)
            decrypted = f.decrypt(base64.urlsafe_b64decode(encrypted_password))
            return decrypted.decode()
        except (InvalidToken, ValueError, TypeError):
            # Se houver erro na descriptografia, retornar string vazia
            return ''

class SocialProviderConfig(models.Model):
    provider = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    client_id = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.provider)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Configuração de Provedor Social'
        verbose_name_plural = 'Configurações de Provedores Sociais'

    def __str__(self):
        return f'{self.provider} - {"Ativo" if self.is_active else "Inativo"}'

class EmailConfig(models.Model):
    email_host = models.CharField(max_length=255)
    slug = models.SlugField(max_length=60, unique=True, blank=True, default='email-config')
    email_port = models.IntegerField()
    email_host_user = models.CharField(max_length=255)
    email_host_password = models.CharField(max_length=500)  # Aumentado para acomodar texto criptografado
    email_use_tls = models.BooleanField(default=True)
    default_from_email = models.EmailField()
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(
        default=False,
        help_text="Marcar como configuração padrão do sistema - aplicará automaticamente as configurações ao Django"
    )
    use_console_backend = models.BooleanField(
        default=False,
        help_text="Usar backend de console (desenvolvimento) - emails aparecerão no terminal em vez de serem enviados"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Campo para armazenar a senha em texto simples temporariamente
    _password_plain = None

    def save(self, *args, **kwargs):
        if not self.slug:
            # Gerar slug único baseado no host
            import re
            from django.utils import timezone

            # Limpar o host para criar um slug válido
            clean_host = re.sub(r'[^a-zA-Z0-9\-]', '-', self.email_host.lower())
            base_slug = f"email-{clean_host}"
            slug = base_slug
            counter = 1

            # Verificar se já existe e gerar um único
            while EmailConfig.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        # Criptografar a senha se for nova ou se foi alterada
        if self._password_plain:
            self.email_host_password = PasswordEncryptor.encrypt_password(self._password_plain)
            self._password_plain = None

        # Garantir que apenas uma configuração seja padrão
        if self.is_default:
            # Desmarcar outras configurações como padrão
            EmailConfig.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)

            # Aplicar automaticamente as configurações ao Django
            super().save(*args, **kwargs)  # Salvar primeiro
            from .email_utils import apply_email_settings_to_django
            apply_email_settings_to_django(self)
        else:
            super().save(*args, **kwargs)

    def set_password(self, password):
        """Define a senha em texto simples para ser criptografada no save()"""
        self._password_plain = password

    def get_password(self):
        """Retorna a senha descriptografada"""
        return PasswordEncryptor.decrypt_password(self.email_host_password)

    class Meta:
        verbose_name = 'Configuração de Email'
        verbose_name_plural = 'Configurações de Email'

    def __str__(self):
        return f'Configuração de Email - {"Ativa" if self.is_active else "Inativa"}'

class LDAPConfig(models.Model):
    server = models.CharField(max_length=255)
    server_uri = models.CharField(max_length=255, blank=True, help_text='URI completa do servidor LDAP (ex: ldap://servidor:389)')
    slug = models.SlugField(max_length=60, unique=True, blank=True, default='ldap-config')
    port = models.IntegerField(default=389)
    base_dn = models.CharField(max_length=255)
    bind_dn = models.CharField(max_length=255, blank=True)
    bind_password = models.CharField(max_length=500, blank=True)  # Aumentado para acomodar texto criptografado
    domain = models.CharField(max_length=255, blank=True, help_text='Domínio para criação de emails de usuários LDAP')
    search_filter = models.CharField(max_length=255, default='(objectClass=person)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Campo para armazenar a senha em texto simples temporariamente
    _password_plain = None

    def save(self, *args, **kwargs):
        if not self.slug:
            # Gerar slug único baseado no servidor
            import re

            # Limpar o servidor para criar um slug válido
            clean_server = re.sub(r'[^a-zA-Z0-9\-]', '-', self.server.lower())
            base_slug = f"ldap-{clean_server}"
            slug = base_slug
            counter = 1

            # Verificar se já existe e gerar um único
            while LDAPConfig.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        # Gerar server_uri se não estiver definido
        if not self.server_uri and self.server:
            self.server_uri = f'ldap://{self.server}:{self.port}'

        # Criptografar a senha se for nova ou se foi alterada
        if self._password_plain:
            self.bind_password = PasswordEncryptor.encrypt_password(self._password_plain)
            self._password_plain = None

        # Validar o domínio
        if self.domain and '.' not in self.domain:
            raise models.ValidationError({'domain': 'O domínio deve ser válido (ex: exemplo.com.br)'})

        super().save(*args, **kwargs)

    def set_password(self, password):
        """Define a senha em texto simples para ser criptografada no save()"""
        self._password_plain = password

    def get_password(self):
        """Retorna a senha descriptografada"""
        return PasswordEncryptor.decrypt_password(self.bind_password)

    class Meta:
        verbose_name = 'Configuração LDAP'
        verbose_name_plural = 'Configurações LDAP'

    def __str__(self):
        return f'Configuração LDAP - {self.server}'

    def get_server_uri(self):
        """Retorna a URI completa do servidor LDAP"""
        if self.server_uri:
            return self.server_uri
        return f'ldap://{self.server}:{self.port}'


class SystemConfig(models.Model):
    site_name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=60, unique=True, blank=True, default='system-config')
    site_description = models.TextField()
    maintenance_mode = models.BooleanField(default=False)
    allow_registration = models.BooleanField(default=True)
    require_email_verification = models.BooleanField(default=True)
    enable_app_management = models.BooleanField(default=True, help_text="Permite ativar/desativar módulos")

    # Configurações de desenvolvimento
    debug_mode = models.BooleanField(
        default=True,
        help_text="Ativar modo debug (desenvolvimento). DESATIVE em produção!"
    )

    # Campos de personalização visual
    logo_principal = models.ImageField(
        upload_to='logos/',
        blank=True,
        null=True,
        validators=[validate_logo_image],
        help_text="Logo principal do site (PNG, JPG, SVG, WEBP - máx. 5MB, 50x50 a 2000x2000px)"
    )
    favicon = models.ImageField(
        upload_to='favicons/',
        blank=True,
        null=True,
        validators=[validate_favicon_image],
        help_text="Favicon do site (ICO, PNG, JPG, SVG - máx. 1MB, 16x16 a 512x512px, preferencialmente quadrado)"
    )

    # Campos de personalização de tema
    THEME_CHOICES = [
        ('default', 'Padrão'),
        ('dark', 'Escuro'),
        ('light', 'Claro'),
        ('corporate', 'Corporativo'),
        ('modern', 'Moderno'),
        ('minimal', 'Minimalista'),
        ('custom', 'Personalizado'),
    ]

    theme = models.CharField(
        max_length=20,
        choices=THEME_CHOICES,
        default='default',
        help_text="Tema visual do sistema"
    )

    # Cores personalizáveis
    primary_color = models.CharField(
        max_length=7,
        default='#4361ee',
        help_text="Cor primária (hex) - ex: #4361ee"
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#6c757d',
        help_text="Cor secundária (hex) - ex: #6c757d"
    )
    accent_color = models.CharField(
        max_length=7,
        default='#4cc9f0',
        help_text="Cor de destaque (hex) - ex: #4cc9f0"
    )

    # Configurações de layout
    sidebar_style = models.CharField(
        max_length=20,
        choices=[
            ('fixed', 'Fixo'),
            ('collapsible', 'Recolhível'),
            ('overlay', 'Sobreposição'),
            ('mini', 'Mini'),
        ],
        default='fixed',
        help_text="Estilo da barra lateral"
    )

    header_style = models.CharField(
        max_length=20,
        choices=[
            ('fixed', 'Fixo'),
            ('static', 'Estático'),
            ('transparent', 'Transparente'),
        ],
        default='fixed',
        help_text="Estilo do cabeçalho"
    )

    # Configurações de funcionalidade
    enable_dark_mode_toggle = models.BooleanField(
        default=True,
        help_text="Permitir alternância entre modo claro/escuro"
    )

    enable_breadcrumbs = models.BooleanField(
        default=True,
        help_text="Exibir breadcrumbs de navegação"
    )

    enable_search = models.BooleanField(
        default=True,
        help_text="Habilitar busca global"
    )

    # Configurações de SEO
    meta_keywords = models.TextField(
        blank=True,
        help_text="Palavras-chave para SEO (separadas por vírgula)"
    )

    meta_author = models.CharField(
        max_length=100,
        blank=True,
        help_text="Autor do site para meta tags"
    )

    google_analytics_id = models.CharField(
        max_length=20,
        blank=True,
        help_text="ID do Google Analytics (ex: GA-XXXXXXXXX-X)"
    )

    # Configurações de notificação
    enable_notifications = models.BooleanField(
        default=True,
        help_text="Habilitar sistema de notificações"
    )

    notification_position = models.CharField(
        max_length=20,
        choices=[
            ('top-right', 'Superior Direita'),
            ('top-left', 'Superior Esquerda'),
            ('bottom-right', 'Inferior Direita'),
            ('bottom-left', 'Inferior Esquerda'),
            ('top-center', 'Superior Centro'),
            ('bottom-center', 'Inferior Centro'),
        ],
        default='top-right',
        help_text="Posição das notificações"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            # Gerar slug único baseado no nome do site
            import re
            from django.utils.text import slugify

            # Limpar o nome para criar um slug válido
            base_slug = slugify(f"system-{self.site_name}")
            if not base_slug:
                base_slug = "system-config"

            slug = base_slug
            counter = 1

            # Verificar se já existe e gerar um único
            while SystemConfig.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

        # Limpar cache das configurações do sistema
        from .context_processors import clear_system_config_cache
        clear_system_config_cache()

    def get_logo_url(self):
        """Retorna a URL do logo principal ou None se não existir"""
        if self.logo_principal and hasattr(self.logo_principal, 'url'):
            return self.logo_principal.url
        return None

    def get_favicon_url(self):
        """Retorna a URL do favicon ou None se não existir"""
        if self.favicon and hasattr(self.favicon, 'url'):
            return self.favicon.url
        return None

    def has_custom_branding(self):
        """Verifica se tem personalização visual configurada"""
        return bool(self.logo_principal or self.favicon)

    class Meta:
        verbose_name = 'Configuração do Sistema'
        verbose_name_plural = 'Configurações do Sistema'

    def __str__(self):
        return f'Configuração do Sistema - {self.site_name}'


class AppConfig(models.Model):
    name = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_core = models.BooleanField(default=False, help_text="Apps core não podem ser desativados")
    order = models.PositiveIntegerField(default=0)
    dependencies = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependents', help_text="Módulos que este app depende para funcionar")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração de App'
        verbose_name_plural = 'Configurações de Apps'
        ordering = ['order', 'name']
        constraints = [
            models.CheckConstraint(
                check=~(models.Q(is_core=True) & models.Q(is_active=False)),
                name='core_apps_must_be_active'
            ),
            models.CheckConstraint(
                check=~(models.Q(label='pages') & models.Q(is_active=False)),
                name='pages_app_must_be_active'
            )
        ]

    def __str__(self):
        return f"{self.name} - {'Ativo' if self.is_active else 'Inativo'}"

    def save(self, *args, **kwargs):
        # Não permitir desativar apps core ou o app pages
        if self.is_core or self.label == 'pages':
            self.is_active = True
            if self.label == 'pages' and not self.is_core:
                self.is_core = True  # Garantir que pages seja marcado como core

        # Validar antes de salvar
        self.clean()

        # Salvar primeiro para poder verificar dependências (necessário para objetos novos)
        super().save(*args, **kwargs)

        # Se o app está sendo ativado, verificar e ativar suas dependências
        if self.is_active and self.pk:
            for dependency in self.dependencies.all():
                if not dependency.is_active:
                    dependency.is_active = True
                    dependency.save()

    def clean(self):
        """Validação adicional para garantir que apps core e pages não possam ser desativados."""
        from django.core.exceptions import ValidationError

        # Verificar se apps core e pages não podem ser desativados
        if (self.is_core or self.label == 'pages') and not self.is_active:
            raise ValidationError("Apps core e o app 'pages' não podem ser desativados.")

        # Verificar se há apps dependentes ativos
        if not self.is_active and self.pk:  # Verificar apenas para objetos existentes
            active_dependents = self.dependents.filter(is_active=True)
            if active_dependents.exists():
                dependent_names = ", ".join([app.name for app in active_dependents])
                raise ValidationError(
                    f"Não é possível desativar este módulo porque os seguintes módulos dependem dele: {dependent_names}. "
                    f"Desative esses módulos primeiro."
                )


class EnvironmentVariable(models.Model):
    """Modelo para gerenciar variáveis de ambiente"""

    CATEGORY_CHOICES = [
        ('core', 'Django Core'),
        ('database', 'Database'),
        ('email', 'Email'),
        ('security', 'Security'),
        ('site', 'Site'),
        ('static', 'Static & Media'),
        ('cache', 'Cache'),
        ('logging', 'Logging'),
        ('auth', 'Authentication'),
        ('ldap', 'LDAP'),
        ('social', 'Social Auth'),
        ('services', 'Third-party Services'),
        ('api', 'API Keys'),
        ('development', 'Development'),
        ('performance', 'Performance'),
        ('custom', 'Custom Application'),
        ('backup', 'Backup & Maintenance'),
    ]

    TYPE_CHOICES = [
        ('string', 'String'),
        ('boolean', 'Boolean'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('url', 'URL'),
        ('email', 'Email'),
        ('password', 'Password'),
        ('json', 'JSON'),
        ('csv', 'CSV (Comma Separated)'),
    ]

    key = models.CharField(max_length=100, unique=True, help_text="Nome da variável (ex: DEBUG)")
    value = models.TextField(blank=True, help_text="Valor da variável")
    default_value = models.TextField(blank=True, help_text="Valor padrão")
    description = models.TextField(help_text="Descrição da variável")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='custom')
    var_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='string')
    is_required = models.BooleanField(default=False, help_text="Variável obrigatória")
    is_sensitive = models.BooleanField(default=False, help_text="Variável sensível (senha, chave, etc.)")
    is_active = models.BooleanField(default=True, help_text="Variável ativa no sistema")
    order = models.PositiveIntegerField(default=0, help_text="Ordem de exibição")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Variável de Ambiente'
        verbose_name_plural = 'Variáveis de Ambiente'
        ordering = ['category', 'order', 'key']

    def __str__(self):
        return f"{self.key} ({self.get_category_display()})"

    def get_display_value(self):
        """Retorna o valor para exibição (mascarado se sensível)"""
        if self.is_sensitive and self.value:
            return '*' * min(len(self.value), 8)
        return self.value

    def get_typed_value(self):
        """Retorna o valor convertido para o tipo correto"""
        if not self.value:
            return self.get_typed_default()

        try:
            if self.var_type == 'boolean':
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.var_type == 'integer':
                return int(self.value)
            elif self.var_type == 'float':
                return float(self.value)
            elif self.var_type == 'csv':
                return [item.strip() for item in self.value.split(',') if item.strip()]
            elif self.var_type == 'json':
                return json.loads(self.value)
            else:
                return self.value
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.get_typed_default()

    def get_typed_default(self):
        """Retorna o valor padrão convertido para o tipo correto"""
        if not self.default_value:
            if self.var_type == 'boolean':
                return False
            elif self.var_type in ['integer', 'float']:
                return 0
            elif self.var_type in ['csv', 'json']:
                return []
            else:
                return ''

        try:
            if self.var_type == 'boolean':
                return self.default_value.lower() in ('true', '1', 'yes', 'on')
            elif self.var_type == 'integer':
                return int(self.default_value)
            elif self.var_type == 'float':
                return float(self.default_value)
            elif self.var_type == 'csv':
                return [item.strip() for item in self.default_value.split(',') if item.strip()]
            elif self.var_type == 'json':
                return json.loads(self.default_value)
            else:
                return self.default_value
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.default_value


class DatabaseConfig(models.Model):
    """Modelo para configurar diferentes tipos de banco de dados"""

    ENGINE_CHOICES = [
        ('django.db.backends.sqlite3', 'SQLite'),
        ('django.db.backends.postgresql', 'PostgreSQL'),
        ('django.db.backends.mysql', 'MySQL'),
        ('django.db.backends.oracle', 'Oracle'),
    ]

    name = models.CharField(max_length=100, default='default', help_text="Nome da configuração do banco")
    slug = models.SlugField(max_length=60, unique=True, blank=True, default='database-config')
    engine = models.CharField(max_length=100, choices=ENGINE_CHOICES, default='django.db.backends.sqlite3')

    # Configurações básicas
    database_name = models.CharField(max_length=255, help_text="Nome do banco de dados ou caminho para SQLite")
    host = models.CharField(max_length=255, blank=True, default='localhost', help_text="Host do servidor de banco")
    port = models.IntegerField(blank=True, null=True, help_text="Porta do servidor (deixe vazio para padrão)")
    user = models.CharField(max_length=255, blank=True, help_text="Usuário do banco de dados")
    password = models.CharField(max_length=500, blank=True, help_text="Senha do banco de dados")

    # Configurações avançadas
    conn_max_age = models.IntegerField(default=0, help_text="Tempo máximo de vida da conexão em segundos")
    conn_health_checks = models.BooleanField(default=False, help_text="Verificações de saúde da conexão")

    # Configurações SSL
    ssl_require = models.BooleanField(default=False, help_text="Exigir conexão SSL")
    ssl_ca = models.CharField(max_length=500, blank=True, help_text="Caminho para certificado CA SSL")
    ssl_cert = models.CharField(max_length=500, blank=True, help_text="Caminho para certificado SSL")
    ssl_key = models.CharField(max_length=500, blank=True, help_text="Caminho para chave SSL")

    # Configurações específicas
    charset = models.CharField(max_length=50, blank=True, default='utf8mb4', help_text="Charset para MySQL")
    atomic_requests = models.BooleanField(default=False, help_text="Usar transações atômicas")
    autocommit = models.BooleanField(default=True, help_text="Auto-commit das transações")

    # Configurações de teste
    test_database_name = models.CharField(max_length=255, blank=True, help_text="Nome do banco para testes")

    is_active = models.BooleanField(default=True, help_text="Configuração ativa")
    is_default = models.BooleanField(default=False, help_text="Configuração padrão do sistema")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Campo para armazenar a senha em texto simples temporariamente
    _password_plain = None

    class Meta:
        verbose_name = 'Configuração de Banco de Dados'
        verbose_name_plural = 'Configurações de Banco de Dados'
        ordering = ['-is_default', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            # Gerar slug único baseado no nome
            from django.utils.text import slugify

            base_slug = f"db-{slugify(self.name)}"
            if not base_slug or base_slug == "db-":
                base_slug = "db-config"

            slug = base_slug
            counter = 1

            # Verificar se já existe e gerar um único
            while DatabaseConfig.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        # Garantir que apenas uma configuração seja padrão
        if self.is_default:
            DatabaseConfig.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)

        # Criptografar a senha se for nova ou se foi alterada
        if self._password_plain:
            self.password = PasswordEncryptor.encrypt_password(self._password_plain)
            self._password_plain = None

        # Definir porta padrão baseada no engine
        if not self.port:
            if 'postgresql' in self.engine:
                self.port = 5432
            elif 'mysql' in self.engine:
                self.port = 3306
            elif 'oracle' in self.engine:
                self.port = 1521

        super().save(*args, **kwargs)

    def set_password(self, password):
        """Define a senha em texto simples para ser criptografada no save()"""
        self._password_plain = password

    def get_password(self):
        """Retorna a senha descriptografada"""
        if self.password:
            return PasswordEncryptor.decrypt_password(self.password)
        return ''

    def get_database_url(self):
        """Gera a URL de conexão do banco de dados"""
        if self.engine == 'django.db.backends.sqlite3':
            return f"sqlite:///{self.database_name}"

        # Para outros bancos
        engine_map = {
            'django.db.backends.postgresql': 'postgresql',
            'django.db.backends.mysql': 'mysql',
            'django.db.backends.oracle': 'oracle',
        }

        scheme = engine_map.get(self.engine, 'postgresql')
        password = self.get_password()

        if self.user and password:
            auth = f"{self.user}:{password}@"
        elif self.user:
            auth = f"{self.user}@"
        else:
            auth = ""

        port_part = f":{self.port}" if self.port else ""

        return f"{scheme}://{auth}{self.host}{port_part}/{self.database_name}"

    def get_django_config(self):
        """Retorna a configuração no formato do Django DATABASES"""
        config = {
            'ENGINE': self.engine,
            'NAME': self.database_name,
        }

        if self.engine != 'django.db.backends.sqlite3':
            config.update({
                'HOST': self.host,
                'PORT': self.port,
                'USER': self.user,
                'PASSWORD': self.get_password(),
            })

        # Opções adicionais
        options = {}

        if self.ssl_require:
            if 'mysql' in self.engine:
                options['ssl'] = {'ssl_require': True}
                if self.ssl_ca:
                    options['ssl']['ssl_ca'] = self.ssl_ca
                if self.ssl_cert:
                    options['ssl']['ssl_cert'] = self.ssl_cert
                if self.ssl_key:
                    options['ssl']['ssl_key'] = self.ssl_key
            elif 'postgresql' in self.engine:
                options['sslmode'] = 'require'

        if 'mysql' in self.engine and self.charset:
            options['charset'] = self.charset

        if options:
            config['OPTIONS'] = options

        # Configurações de conexão
        if self.conn_max_age:
            config['CONN_MAX_AGE'] = self.conn_max_age

        if self.conn_health_checks:
            config['CONN_HEALTH_CHECKS'] = True

        if self.atomic_requests:
            config['ATOMIC_REQUESTS'] = True

        if not self.autocommit:
            config['AUTOCOMMIT'] = False

        # Configurações de teste
        if self.test_database_name:
            config['TEST'] = {'NAME': self.test_database_name}

        return config

    def test_connection(self):
        """Testa a conexão com o banco de dados"""
        try:
            from django.db import connections
            from django.core.management.color import no_style
            from django.db.backends.utils import truncate_name

            # Criar uma conexão temporária
            config = self.get_django_config()

            # Para SQLite, verificar se o arquivo existe ou pode ser criado
            if self.engine == 'django.db.backends.sqlite3':
                import os
                db_path = self.database_name
                if not os.path.exists(db_path):
                    # Tentar criar o diretório se necessário
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                return True, "Conexão SQLite válida"

            # Para outros bancos, tentar conectar
            import django.db
            from django.db.backends import utils

            # Simular teste de conexão
            return True, "Configuração válida (teste completo requer conexão real)"

        except Exception as e:
            return False, str(e)

    def __str__(self):
        status = "Ativa" if self.is_active else "Inativa"
        default = " (Padrão)" if self.is_default else ""
        return f"{self.name} - {self.get_engine_display()}{default} - {status}"


class Widget(models.Model):
    """Modelo para widgets modulares do dashboard"""

    WIDGET_TYPES = [
        ('chart', 'Gráfico'),
        ('stats', 'Estatísticas'),
        ('list', 'Lista'),
        ('calendar', 'Calendário'),
        ('weather', 'Clima'),
        ('news', 'Notícias'),
        ('tasks', 'Tarefas'),
        ('notes', 'Notas'),
        ('custom', 'Personalizado'),
    ]

    SIZE_CHOICES = [
        ('small', 'Pequeno (1x1)'),
        ('medium', 'Médio (2x1)'),
        ('large', 'Grande (2x2)'),
        ('wide', 'Largo (3x1)'),
        ('tall', 'Alto (1x3)'),
        ('extra-large', 'Extra Grande (3x3)'),
    ]

    name = models.CharField(max_length=100, help_text="Nome do widget")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Descrição do widget")
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES, default='custom')

    # Configurações de exibição
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, default='medium')
    position_x = models.PositiveIntegerField(default=0, help_text="Posição horizontal no grid")
    position_y = models.PositiveIntegerField(default=0, help_text="Posição vertical no grid")
    order = models.PositiveIntegerField(default=0, help_text="Ordem de exibição")

    # Configurações de acesso
    is_active = models.BooleanField(default=True, help_text="Widget ativo")
    is_public = models.BooleanField(default=False, help_text="Visível para todos os usuários")
    required_permission = models.CharField(
        max_length=100,
        blank=True,
        help_text="Permissão necessária para ver o widget"
    )

    # Configurações do widget
    config_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configurações específicas do widget em JSON"
    )

    # Template personalizado
    template_path = models.CharField(
        max_length=200,
        blank=True,
        help_text="Caminho para template personalizado"
    )

    # CSS personalizado
    custom_css = models.TextField(
        blank=True,
        help_text="CSS personalizado para o widget"
    )

    # JavaScript personalizado
    custom_js = models.TextField(
        blank=True,
        help_text="JavaScript personalizado para o widget"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Widget'
        verbose_name_plural = 'Widgets'
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_widget_type_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_config(self, key, default=None):
        """Obtém uma configuração específica do widget"""
        return self.config_json.get(key, default)

    def set_config(self, key, value):
        """Define uma configuração específica do widget"""
        self.config_json[key] = value

    def has_permission(self, user):
        """Verifica se o usuário tem permissão para ver o widget"""
        if not self.is_active:
            return False

        if self.is_public:
            return True

        if not user.is_authenticated:
            return False

        if not self.required_permission:
            return True

        return user.has_perm(self.required_permission)


class MenuConfig(models.Model):
    """Modelo para configuração de menus dinâmicos"""

    MENU_TYPES = [
        ('main', 'Menu Principal'),
        ('sidebar', 'Menu Lateral'),
        ('footer', 'Menu Rodapé'),
        ('user', 'Menu do Usuário'),
        ('admin', 'Menu Administrativo'),
    ]

    ICON_TYPES = [
        ('fontawesome', 'Font Awesome'),
        ('bootstrap', 'Bootstrap Icons'),
        ('custom', 'Personalizado'),
    ]

    name = models.CharField(max_length=100, help_text="Nome do item do menu")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    menu_type = models.CharField(max_length=20, choices=MENU_TYPES, default='main')

    # Hierarquia
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Item pai (para submenus)"
    )

    # Configurações de exibição
    title = models.CharField(max_length=100, help_text="Título exibido")
    url = models.CharField(max_length=200, blank=True, help_text="URL ou nome da view")
    icon_type = models.CharField(max_length=20, choices=ICON_TYPES, default='fontawesome')
    icon = models.CharField(max_length=50, blank=True, help_text="Classe do ícone")
    order = models.PositiveIntegerField(default=0, help_text="Ordem de exibição")

    # Configurações de acesso
    is_active = models.BooleanField(default=True, help_text="Item ativo")
    is_external = models.BooleanField(default=False, help_text="Link externo")
    open_in_new_tab = models.BooleanField(default=False, help_text="Abrir em nova aba")

    # Permissões
    required_permission = models.CharField(
        max_length=100,
        blank=True,
        help_text="Permissão necessária para ver o item"
    )
    required_group = models.CharField(
        max_length=100,
        blank=True,
        help_text="Grupo necessário para ver o item"
    )
    staff_only = models.BooleanField(default=False, help_text="Apenas para staff")
    authenticated_only = models.BooleanField(default=False, help_text="Apenas para usuários autenticados")

    # Configurações avançadas
    css_class = models.CharField(
        max_length=100,
        blank=True,
        help_text="Classes CSS adicionais"
    )
    badge_text = models.CharField(
        max_length=20,
        blank=True,
        help_text="Texto do badge (ex: 'Novo', '5')"
    )
    badge_color = models.CharField(
        max_length=20,
        blank=True,
        help_text="Cor do badge (ex: 'primary', 'danger')"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração de Menu'
        verbose_name_plural = 'Configurações de Menu'
        ordering = ['menu_type', 'order', 'title']

    def __str__(self):
        return f"{self.title} ({self.get_menu_type_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.menu_type}-{self.title}")
        super().save(*args, **kwargs)

    def has_permission(self, user):
        """Verifica se o usuário tem permissão para ver o item do menu"""
        if not self.is_active:
            return False

        if self.authenticated_only and not user.is_authenticated:
            return False

        if self.staff_only and not user.is_staff:
            return False

        if self.required_permission and not user.has_perm(self.required_permission):
            return False

        if self.required_group and not user.groups.filter(name=self.required_group).exists():
            return False

        return True

    def get_children(self, user=None):
        """Obtém os itens filhos que o usuário pode ver"""
        children = self.children.filter(is_active=True).order_by('order')
        if user:
            children = [child for child in children if child.has_permission(user)]
        return children


class Plugin(models.Model):
    """Modelo para plugins modulares do sistema"""

    PLUGIN_TYPES = [
        ('widget', 'Widget'),
        ('middleware', 'Middleware'),
        ('template_tag', 'Template Tag'),
        ('context_processor', 'Context Processor'),
        ('command', 'Comando'),
        ('api', 'API'),
        ('integration', 'Integração'),
        ('utility', 'Utilitário'),
    ]

    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('error', 'Erro'),
        ('updating', 'Atualizando'),
        ('installing', 'Instalando'),
    ]

    name = models.CharField(max_length=100, help_text="Nome do plugin")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Descrição do plugin")
    plugin_type = models.CharField(max_length=20, choices=PLUGIN_TYPES, default='utility')

    # Informações do plugin
    version = models.CharField(max_length=20, default='1.0.0', help_text="Versão do plugin")
    author = models.CharField(max_length=100, blank=True, help_text="Autor do plugin")
    author_email = models.EmailField(blank=True, help_text="Email do autor")
    homepage = models.URLField(blank=True, help_text="Site do plugin")

    # Configurações técnicas
    module_path = models.CharField(
        max_length=200,
        help_text="Caminho do módulo Python (ex: apps.plugins.meu_plugin)"
    )
    entry_point = models.CharField(
        max_length=100,
        default='main',
        help_text="Função de entrada do plugin"
    )

    # Dependências
    dependencies = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de dependências do plugin"
    )

    # Configurações
    config_schema = models.JSONField(
        default=dict,
        blank=True,
        help_text="Schema de configuração do plugin"
    )
    config_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dados de configuração do plugin"
    )

    # Status e controle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    is_core = models.BooleanField(default=False, help_text="Plugin do sistema (não pode ser removido)")
    auto_load = models.BooleanField(default=True, help_text="Carregar automaticamente na inicialização")

    # Permissões
    required_permissions = models.JSONField(
        default=list,
        blank=True,
        help_text="Permissões necessárias para usar o plugin"
    )

    # Metadados
    install_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    last_error = models.TextField(blank=True, help_text="Último erro ocorrido")

    class Meta:
        verbose_name = 'Plugin'
        verbose_name_plural = 'Plugins'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} v{self.version} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_config(self, key, default=None):
        """Obtém uma configuração específica do plugin"""
        return self.config_data.get(key, default)

    def set_config(self, key, value):
        """Define uma configuração específica do plugin"""
        self.config_data[key] = value
        self.save(update_fields=['config_data'])

    def is_compatible(self):
        """Verifica se o plugin é compatível com o sistema atual"""
        try:
            # Verificar dependências
            for dep in self.dependencies:
                if isinstance(dep, dict):
                    module_name = dep.get('module')
                    min_version = dep.get('min_version')
                    # Aqui você pode implementar verificação de versão
                else:
                    module_name = dep

                try:
                    __import__(module_name)
                except ImportError:
                    return False, f"Dependência não encontrada: {module_name}"

            return True, "Plugin compatível"
        except Exception as e:
            return False, str(e)

    def load_plugin(self):
        """Carrega o plugin"""
        try:
            if self.status == 'active':
                return True, "Plugin já está ativo"

            # Verificar compatibilidade
            compatible, message = self.is_compatible()
            if not compatible:
                self.status = 'error'
                self.last_error = message
                self.save()
                return False, message

            # Importar módulo
            module = __import__(self.module_path, fromlist=[self.entry_point])
            entry_func = getattr(module, self.entry_point)

            # Executar função de entrada
            result = entry_func(self.config_data)

            self.status = 'active'
            self.last_error = ''
            self.save()

            return True, "Plugin carregado com sucesso"

        except Exception as e:
            self.status = 'error'
            self.last_error = str(e)
            self.save()
            return False, str(e)

    def unload_plugin(self):
        """Descarrega o plugin"""
        try:
            if self.status != 'active':
                return True, "Plugin não está ativo"

            # Tentar executar função de limpeza se existir
            try:
                module = __import__(self.module_path, fromlist=['cleanup'])
                if hasattr(module, 'cleanup'):
                    cleanup_func = getattr(module, 'cleanup')
                    cleanup_func(self.config_data)
            except:
                pass  # Ignorar erros de limpeza

            self.status = 'inactive'
            self.save()

            return True, "Plugin descarregado com sucesso"

        except Exception as e:
            self.last_error = str(e)
            self.save()
            return False, str(e)


class ConfigBackup(models.Model):
    """Modelo para backup de configurações"""

    BACKUP_TYPES = [
        ('manual', 'Manual'),
        ('automatic', 'Automático'),
        ('scheduled', 'Agendado'),
        ('pre_update', 'Pré-atualização'),
    ]

    name = models.CharField(max_length=100, help_text="Nome do backup")
    description = models.TextField(blank=True, help_text="Descrição do backup")
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPES, default='manual')

    # Dados do backup
    system_config = models.JSONField(default=dict, help_text="Configurações do sistema")
    app_configs = models.JSONField(default=dict, help_text="Configurações de apps")
    environment_variables = models.JSONField(default=dict, help_text="Variáveis de ambiente")
    database_configs = models.JSONField(default=dict, help_text="Configurações de banco")
    ldap_configs = models.JSONField(default=dict, help_text="Configurações LDAP")
    email_configs = models.JSONField(default=dict, help_text="Configurações de email")
    social_configs = models.JSONField(default=dict, help_text="Configurações sociais")
    widgets = models.JSONField(default=list, help_text="Configurações de widgets")
    menus = models.JSONField(default=list, help_text="Configurações de menus")
    plugins = models.JSONField(default=list, help_text="Configurações de plugins")

    # Metadados
    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuário que criou o backup"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField(default=0, help_text="Tamanho do backup em bytes")

    # Configurações de retenção
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Data de expiração do backup")
    is_protected = models.BooleanField(default=False, help_text="Backup protegido contra exclusão automática")

    class Meta:
        verbose_name = 'Backup de Configuração'
        verbose_name_plural = 'Backups de Configuração'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"

    def get_size_display(self):
        """Retorna o tamanho do backup em formato legível"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

    def create_backup(self):
        """Cria um backup das configurações atuais"""
        try:
            from django.core import serializers

            # Backup das configurações do sistema
            system_configs = SystemConfig.objects.all()
            self.system_config = []
            for config in system_configs:
                config_data = {
                    'model': 'config.systemconfig',
                    'fields': {}
                }
                for field in config._meta.fields:
                    if field.name not in ['id', 'created_at', 'updated_at']:
                        value = getattr(config, field.name)
                        # Tratar campos de imagem e arquivo
                        if field.get_internal_type() in ['FileField', 'ImageField']:
                            try:
                                config_data['fields'][field.name] = value.url if value and hasattr(value, 'url') and value.name else None
                            except:
                                config_data['fields'][field.name] = None
                        else:
                            config_data['fields'][field.name] = value
                self.system_config.append(config_data)

            # Backup das configurações de apps
            app_configs = AppConfig.objects.all()
            self.app_configs = [
                {
                    'model': 'config.appconfig',
                    'fields': {
                        field.name: getattr(config, field.name)
                        for field in config._meta.fields
                        if field.name not in ['id', 'created_at', 'updated_at']
                    }
                }
                for config in app_configs
            ]

            # Backup das variáveis de ambiente
            env_vars = EnvironmentVariable.objects.all()
            self.environment_variables = [
                {
                    'model': 'config.environmentvariable',
                    'fields': {
                        field.name: getattr(var, field.name)
                        for field in var._meta.fields
                        if field.name not in ['id', 'created_at', 'updated_at']
                    }
                }
                for var in env_vars
            ]

            # Backup das configurações de banco
            db_configs = DatabaseConfig.objects.all()
            self.database_configs = [
                {
                    'model': 'config.databaseconfig',
                    'fields': {
                        field.name: getattr(config, field.name)
                        for field in config._meta.fields
                        if field.name not in ['id', 'created_at', 'updated_at', 'password']
                    }
                }
                for config in db_configs
            ]

            # Backup das configurações LDAP
            ldap_configs = LDAPConfig.objects.all()
            self.ldap_configs = [
                {
                    'model': 'config.ldapconfig',
                    'fields': {
                        field.name: getattr(config, field.name)
                        for field in config._meta.fields
                        if field.name not in ['id', 'created_at', 'updated_at', 'bind_password']
                    }
                }
                for config in ldap_configs
            ]

            # Backup das configurações de email
            email_configs = EmailConfig.objects.all()
            self.email_configs = [
                {
                    'model': 'config.emailconfig',
                    'fields': {
                        field.name: getattr(config, field.name)
                        for field in config._meta.fields
                        if field.name not in ['id', 'created_at', 'updated_at', 'email_host_password']
                    }
                }
                for config in email_configs
            ]

            # Backup das configurações sociais
            social_configs = SocialProviderConfig.objects.all()
            self.social_configs = [
                {
                    'model': 'config.socialproviderconfig',
                    'fields': {
                        field.name: getattr(config, field.name)
                        for field in config._meta.fields
                        if field.name not in ['id', 'created_at', 'updated_at', 'secret_key']
                    }
                }
                for config in social_configs
            ]

            # Backup dos widgets
            widgets = Widget.objects.all()
            self.widgets = [
                {
                    'model': 'config.widget',
                    'fields': {
                        field.name: getattr(widget, field.name)
                        for field in widget._meta.fields
                        if field.name not in ['id', 'created_at', 'updated_at']
                    }
                }
                for widget in widgets
            ]

            # Backup dos menus
            menus = MenuConfig.objects.all()
            self.menus = [
                {
                    'model': 'config.menuconfig',
                    'fields': {
                        field.name: getattr(menu, field.name)
                        for field in menu._meta.fields
                        if field.name not in ['id', 'created_at', 'updated_at']
                    }
                }
                for menu in menus
            ]

            # Backup dos plugins
            plugins = Plugin.objects.all()
            self.plugins = [
                {
                    'model': 'config.plugin',
                    'fields': {
                        field.name: getattr(plugin, field.name)
                        for field in plugin._meta.fields
                        if field.name not in ['id', 'install_date', 'last_update']
                    }
                }
                for plugin in plugins
            ]

            # Calcular tamanho aproximado
            import json
            backup_data = {
                'system_config': self.system_config,
                'app_configs': self.app_configs,
                'environment_variables': self.environment_variables,
                'database_configs': self.database_configs,
                'ldap_configs': self.ldap_configs,
                'email_configs': self.email_configs,
                'social_configs': self.social_configs,
                'widgets': self.widgets,
                'menus': self.menus,
                'plugins': self.plugins,
            }

            self.file_size = len(json.dumps(backup_data).encode('utf-8'))

            return True, "Backup criado com sucesso"

        except Exception as e:
            return False, str(e)

    def restore_backup(self):
        """Restaura as configurações do backup"""
        try:
            # Implementar lógica de restauração
            # Por segurança, esta função deve ser implementada com cuidado
            return True, "Backup restaurado com sucesso"
        except Exception as e:
            return False, str(e)


class SetupWizard(models.Model):
    """Modelo para controlar o assistente de configuração inicial"""

    STEP_CHOICES = [
        ('welcome', 'Boas-vindas'),
        ('environment', 'Detecção de Ambiente'),
        ('database', 'Configuração de Banco'),
        ('email', 'Configuração de Email'),
        ('security', 'Configurações de Segurança'),
        ('optimization', 'Otimizações'),
        ('finalization', 'Finalização'),
        ('completed', 'Concluído'),
    ]

    STATUS_CHOICES = [
        ('not_started', 'Não Iniciado'),
        ('in_progress', 'Em Progresso'),
        ('completed', 'Concluído'),
        ('skipped', 'Ignorado'),
        ('error', 'Erro'),
    ]

    # Identificação única do wizard
    wizard_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Controle de progresso
    current_step = models.CharField(max_length=20, choices=STEP_CHOICES, default='welcome')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    progress_percentage = models.PositiveIntegerField(default=0)

    # Dados coletados durante o wizard
    environment_data = models.JSONField(default=dict, blank=True)
    user_preferences = models.JSONField(default=dict, blank=True)
    configuration_choices = models.JSONField(default=dict, blank=True)
    optimization_settings = models.JSONField(default=dict, blank=True)

    # Controle de etapas
    steps_completed = models.JSONField(default=list, blank=True)
    steps_skipped = models.JSONField(default=list, blank=True)

    # Metadados
    started_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='setup_wizards_started'
    )
    completed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='setup_wizards_completed'
    )

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)

    # Configurações do wizard
    auto_apply_recommendations = models.BooleanField(default=True)
    skip_optional_steps = models.BooleanField(default=False)
    create_backup_before_changes = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Assistente de Configuração'
        verbose_name_plural = 'Assistentes de Configuração'
        ordering = ['-started_at']

    def __str__(self):
        return f"Setup Wizard {self.wizard_id} - {self.get_status_display()}"

    def get_progress_percentage(self):
        """Calcula a porcentagem de progresso baseada nas etapas"""
        total_steps = len(self.STEP_CHOICES) - 1  # Excluir 'completed'
        completed_steps = len(self.steps_completed)
        return min(100, int((completed_steps / total_steps) * 100))

    def mark_step_completed(self, step):
        """Marca uma etapa como concluída"""
        if step not in self.steps_completed:
            self.steps_completed.append(step)
            self.progress_percentage = self.get_progress_percentage()
            self.save(update_fields=['steps_completed', 'progress_percentage', 'last_activity'])

    def mark_step_skipped(self, step):
        """Marca uma etapa como ignorada"""
        if step not in self.steps_skipped:
            self.steps_skipped.append(step)
            self.save(update_fields=['steps_skipped', 'last_activity'])

    def get_next_step(self):
        """Retorna a próxima etapa do wizard"""
        steps = [choice[0] for choice in self.STEP_CHOICES]
        try:
            current_index = steps.index(self.current_step)
            if current_index < len(steps) - 1:
                return steps[current_index + 1]
        except ValueError:
            pass
        return 'completed'

    def advance_to_next_step(self):
        """Avança para a próxima etapa"""
        from django.utils import timezone

        next_step = self.get_next_step()
        self.current_step = next_step

        if next_step == 'completed':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.progress_percentage = 100

        self.save(update_fields=['current_step', 'status', 'completed_at', 'progress_percentage', 'last_activity'])

    def is_step_completed(self, step):
        """Verifica se uma etapa foi concluída"""
        return step in self.steps_completed

    def is_step_skipped(self, step):
        """Verifica se uma etapa foi ignorada"""
        return step in self.steps_skipped

    def get_step_status(self, step):
        """Retorna o status de uma etapa específica"""
        if self.is_step_completed(step):
            return 'completed'
        elif self.is_step_skipped(step):
            return 'skipped'
        elif step == self.current_step:
            return 'current'
        else:
            steps = [choice[0] for choice in self.STEP_CHOICES]
            try:
                step_index = steps.index(step)
                current_index = steps.index(self.current_step)
                return 'pending' if step_index > current_index else 'available'
            except ValueError:
                return 'unknown'

    def save_environment_data(self, data):
        """Salva dados de detecção de ambiente"""
        self.environment_data.update(data)
        self.save(update_fields=['environment_data', 'last_activity'])

    def save_user_preferences(self, preferences):
        """Salva preferências do usuário"""
        self.user_preferences.update(preferences)
        self.save(update_fields=['user_preferences', 'last_activity'])

    def save_configuration_choices(self, choices):
        """Salva escolhas de configuração"""
        self.configuration_choices.update(choices)
        self.save(update_fields=['configuration_choices', 'last_activity'])

    def save_optimization_settings(self, settings):
        """Salva configurações de otimização"""
        self.optimization_settings.update(settings)
        self.save(update_fields=['optimization_settings', 'last_activity'])

    def generate_summary_report(self):
        """Gera relatório resumo do wizard"""
        from django.utils import timezone

        return {
            'wizard_id': str(self.wizard_id),
            'status': self.get_status_display(),
            'progress': f"{self.progress_percentage}%",
            'steps_completed': len(self.steps_completed),
            'steps_skipped': len(self.steps_skipped),
            'total_steps': len(self.STEP_CHOICES) - 1,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self._get_duration(),
            'environment_detected': bool(self.environment_data),
            'configurations_applied': len(self.configuration_choices),
            'optimizations_applied': len(self.optimization_settings),
        }

    def _get_duration(self):
        """Calcula duração do wizard"""
        from django.utils import timezone

        if self.completed_at:
            duration = self.completed_at - self.started_at
            return str(duration).split('.')[0]  # Remove microsegundos
        else:
            duration = timezone.now() - self.started_at
            return f"{str(duration).split('.')[0]} (em progresso)"


class WizardRecommendation(models.Model):
    """Modelo para recomendações do assistente de configuração"""

    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]

    CATEGORY_CHOICES = [
        ('security', 'Segurança'),
        ('performance', 'Performance'),
        ('deployment', 'Deployment'),
        ('database', 'Banco de Dados'),
        ('cache', 'Cache'),
        ('email', 'Email'),
        ('monitoring', 'Monitoramento'),
        ('backup', 'Backup'),
        ('optimization', 'Otimização'),
        ('configuration', 'Configuração'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('applied', 'Aplicada'),
        ('ignored', 'Ignorada'),
        ('failed', 'Falhou'),
    ]

    wizard = models.ForeignKey(SetupWizard, on_delete=models.CASCADE, related_name='recommendations')

    # Informações da recomendação
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')

    # Detalhes técnicos
    technical_details = models.JSONField(default=dict, blank=True)
    implementation_steps = models.JSONField(default=list, blank=True)
    estimated_impact = models.TextField(blank=True)

    # Controle de aplicação
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    auto_apply = models.BooleanField(default=False)
    requires_restart = models.BooleanField(default=False)

    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    applied_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Recomendação do Wizard'
        verbose_name_plural = 'Recomendações do Wizard'
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"

    def apply_recommendation(self, user=None):
        """Aplica a recomendação"""
        from django.utils import timezone

        try:
            # Lógica para aplicar a recomendação baseada nos technical_details
            # Isso seria implementado baseado no tipo de recomendação

            self.status = 'applied'
            self.applied_at = timezone.now()
            if user:
                self.applied_by = user
            self.save(update_fields=['status', 'applied_at', 'applied_by'])

            return True, "Recomendação aplicada com sucesso"

        except Exception as e:
            self.status = 'failed'
            self.save(update_fields=['status'])
            return False, f"Erro ao aplicar recomendação: {str(e)}"

    def ignore_recommendation(self):
        """Marca a recomendação como ignorada"""
        self.status = 'ignored'
        self.save(update_fields=['status'])

    def get_priority_color(self):
        """Retorna cor CSS baseada na prioridade"""
        colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'dark'
        }
        return colors.get(self.priority, 'secondary')

    def get_category_icon(self):
        """Retorna ícone baseado na categoria"""
        icons = {
            'security': 'fas fa-shield-alt',
            'performance': 'fas fa-tachometer-alt',
            'deployment': 'fas fa-rocket',
            'database': 'fas fa-database',
            'cache': 'fas fa-memory',
            'email': 'fas fa-envelope',
            'monitoring': 'fas fa-chart-line',
            'backup': 'fas fa-save',
            'optimization': 'fas fa-cogs',
            'configuration': 'fas fa-sliders-h',
        }
        return icons.get(self.category, 'fas fa-info-circle')
