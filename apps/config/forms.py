from django import forms
import json
from .models import (
    SocialProviderConfig, EmailConfig, SystemConfig, AppConfig, LDAPConfig,
    EnvironmentVariable, DatabaseConfig, Widget, MenuConfig, Plugin, ConfigBackup
)

class SocialProviderConfigForm(forms.ModelForm):
    class Meta:
        model = SocialProviderConfig
        fields = ['provider', 'client_id', 'secret_key', 'is_active']
        widgets = {
            'secret_key': forms.PasswordInput(),
        }

class EmailConfigForm(forms.ModelForm):
    class Meta:
        model = EmailConfig
        fields = ['email_host', 'email_port', 'email_host_user', 'email_host_password',
                 'email_use_tls', 'default_from_email', 'is_active', 'is_default', 'use_console_backend']
        widgets = {
            'email_host_password': forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicionar classes CSS e ajustar labels
        self.fields['is_default'].label = "Configuração Padrão"
        self.fields['is_default'].help_text = (
            "Marcar como configuração padrão do sistema. "
            "Aplicará automaticamente as configurações ao Django e às variáveis de ambiente."
        )
        self.fields['use_console_backend'].label = "Modo Desenvolvimento"
        self.fields['use_console_backend'].help_text = (
            "Ativar para ver emails no terminal (desenvolvimento). "
            "Desativar para enviar emails reais via SMTP (produção)."
        )

class SystemConfigForm(forms.ModelForm):
    class Meta:
        model = SystemConfig
        fields = ['site_name', 'site_description', 'maintenance_mode',
                 'allow_registration', 'require_email_verification', 'enable_app_management',
                 'debug_mode', 'logo_principal', 'favicon', 'theme', 'primary_color', 'secondary_color',
                 'accent_color', 'sidebar_style', 'header_style', 'enable_dark_mode_toggle',
                 'enable_breadcrumbs', 'enable_search', 'meta_keywords', 'meta_author',
                 'google_analytics_id', 'enable_notifications', 'notification_position']
        widgets = {
            'site_description': forms.Textarea(attrs={'rows': 3}),
            'meta_keywords': forms.Textarea(attrs={'rows': 2}),
            'logo_principal': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'favicon': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.ico'
            }),
            'primary_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),
            'secondary_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),
            'accent_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Adicionar classes CSS aos campos
        for field_name, field in self.fields.items():
            if field_name not in ['logo_principal', 'favicon', 'primary_color', 'secondary_color', 'accent_color']:
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs.update({'class': 'form-check-input'})
                elif isinstance(field.widget, forms.Textarea):
                    field.widget.attrs.update({'class': 'form-control'})
                elif isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})

        # Adicionar help text personalizado
        self.fields['logo_principal'].help_text = (
            "Faça upload do logo principal do site. "
            "Formatos aceitos: PNG, JPG, SVG, WEBP. "
            "Tamanho máximo: 5MB. Dimensões: 50x50 a 2000x2000 pixels."
        )

        self.fields['favicon'].help_text = (
            "Faça upload do favicon do site (ícone que aparece na aba do navegador). "
            "Formatos aceitos: ICO, PNG, JPG, SVG. "
            "Tamanho máximo: 1MB. Dimensões: 16x16 a 512x512 pixels (preferencialmente quadrado)."
        )

        self.fields['primary_color'].help_text = "Cor principal do tema (botões, links, etc.)"
        self.fields['secondary_color'].help_text = "Cor secundária do tema (textos, bordas, etc.)"
        self.fields['accent_color'].help_text = "Cor de destaque do tema (notificações, badges, etc.)"
        self.fields['google_analytics_id'].help_text = "ID do Google Analytics para rastreamento (ex: GA-XXXXXXXXX-X)"

        # Help text para debug_mode com aviso de segurança
        self.fields['debug_mode'].help_text = (
            "⚠️ ATENÇÃO: Ativar modo debug mostra informações detalhadas de erro e permite "
            "ferramentas de desenvolvimento. SEMPRE DESATIVE em produção por segurança!"
        )
        self.fields['debug_mode'].widget.attrs.update({
            'class': 'form-check-input',
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'Desative em produção!'
        })

class AppConfigForm(forms.ModelForm):
    class Meta:
        model = AppConfig
        fields = ['name', 'description', 'is_active', 'dependencies', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'dependencies': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Desabilitar campo is_active para apps core
        if self.instance and self.instance.is_core:
            self.fields['is_active'].disabled = True
            self.fields['is_active'].help_text = "Apps core não podem ser desativados"

        # Filtrar dependências disponíveis (excluir o próprio app e apps que dependem dele)
        if self.instance and self.instance.pk:
            # Excluir o próprio app das opções de dependência
            self.fields['dependencies'].queryset = AppConfig.objects.exclude(pk=self.instance.pk)

            # Excluir apps que já dependem deste app (para evitar dependências circulares)
            dependent_apps = self.instance.dependents.all()
            if dependent_apps.exists():
                self.fields['dependencies'].queryset = self.fields['dependencies'].queryset.exclude(
                    pk__in=dependent_apps.values_list('pk', flat=True)
                )

        # Adicionar help text para o campo de dependências
        self.fields['dependencies'].help_text = (
            "Selecione os módulos que este app precisa para funcionar. "
            "Quando este app for ativado, suas dependências serão ativadas automaticamente."
        )


class EnvironmentVariableForm(forms.ModelForm):
    class Meta:
        model = EnvironmentVariable
        fields = ['key', 'value', 'default_value', 'description', 'category',
                 'var_type', 'is_required', 'is_sensitive', 'is_active', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'value': forms.Textarea(attrs={'rows': 2}),
            'default_value': forms.Textarea(attrs={'rows': 2}),
            'key': forms.TextInput(attrs={'placeholder': 'Ex: DEBUG, SECRET_KEY'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Adicionar classes CSS
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

        # Campo de valor sensível
        if self.instance and self.instance.is_sensitive:
            self.fields['value'].widget = forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o valor (será mascarado)'
            })

        # Ajustar widget baseado no tipo
        if self.instance and self.instance.var_type:
            self._adjust_widget_by_type()

    def _adjust_widget_by_type(self):
        """Ajusta o widget baseado no tipo da variável"""
        var_type = self.instance.var_type

        if var_type == 'boolean':
            self.fields['value'].widget = forms.Select(
                choices=[('', '---'), ('True', 'True'), ('False', 'False')],
                attrs={'class': 'form-select'}
            )
        elif var_type == 'integer':
            self.fields['value'].widget = forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1'
            })
        elif var_type == 'float':
            self.fields['value'].widget = forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 'any'
            })
        elif var_type == 'email':
            self.fields['value'].widget = forms.EmailInput(attrs={
                'class': 'form-control'
            })
        elif var_type == 'url':
            self.fields['value'].widget = forms.URLInput(attrs={
                'class': 'form-control'
            })

    def clean_key(self):
        """Validar formato da chave"""
        key = self.cleaned_data.get('key', '').upper()

        # Verificar se contém apenas letras, números e underscore
        import re
        if not re.match(r'^[A-Z0-9_]+$', key):
            raise forms.ValidationError(
                'A chave deve conter apenas letras maiúsculas, números e underscore.'
            )

        return key

    def clean_value(self):
        """Validar valor baseado no tipo"""
        value = self.cleaned_data.get('value', '')
        var_type = self.cleaned_data.get('var_type', 'string')

        if not value:
            return value

        try:
            if var_type == 'boolean':
                if value.lower() not in ['true', 'false', '1', '0', 'yes', 'no', 'on', 'off']:
                    raise forms.ValidationError(
                        'Valor booleano deve ser: true/false, 1/0, yes/no, on/off'
                    )
            elif var_type == 'integer':
                int(value)
            elif var_type == 'float':
                float(value)
            elif var_type == 'json':
                json.loads(value)
            elif var_type == 'email':
                from django.core.validators import validate_email
                validate_email(value)
            elif var_type == 'url':
                from django.core.validators import URLValidator
                validator = URLValidator()
                validator(value)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            raise forms.ValidationError(f'Valor inválido para o tipo {var_type}: {str(e)}')
        except forms.ValidationError:
            raise

        return value


class EnvironmentVariableFilterForm(forms.Form):
    """Formulário para filtrar variáveis de ambiente"""

    category = forms.ChoiceField(
        choices=[('', 'Todas as categorias')] + EnvironmentVariable.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    var_type = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + EnvironmentVariable.TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    is_required = forms.ChoiceField(
        choices=[('', 'Todas'), ('true', 'Obrigatórias'), ('false', 'Opcionais')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    is_sensitive = forms.ChoiceField(
        choices=[('', 'Todas'), ('true', 'Sensíveis'), ('false', 'Não sensíveis')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por chave ou descrição...'
        })
    )


class DatabaseConfigForm(forms.ModelForm):
    """Formulário para configuração de banco de dados"""

    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label='Confirmar Senha'
    )

    class Meta:
        model = DatabaseConfig
        fields = [
            'name', 'engine', 'database_name', 'host', 'port', 'user', 'password',
            'conn_max_age', 'conn_health_checks', 'ssl_require', 'ssl_ca', 'ssl_cert', 'ssl_key',
            'charset', 'atomic_requests', 'autocommit', 'test_database_name', 'is_active', 'is_default'
        ]
        widgets = {
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'ssl_ca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '/path/to/ca-cert.pem'}),
            'ssl_cert': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '/path/to/client-cert.pem'}),
            'ssl_key': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '/path/to/client-key.pem'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Adicionar classes CSS
        for field_name, field in self.fields.items():
            if field_name not in ['password', 'password_confirm']:
                field.widget.attrs.update({'class': 'form-control'})

        # Configurar campos específicos
        self.fields['engine'].widget.attrs.update({'class': 'form-select'})
        self.fields['port'].widget.attrs.update({'placeholder': 'Deixe vazio para usar porta padrão'})

        # Se editando, preencher senha atual
        if self.instance and self.instance.pk:
            self.fields['password'].widget.attrs['placeholder'] = 'Deixe vazio para manter senha atual'
            self.fields['password_confirm'].widget.attrs['placeholder'] = 'Deixe vazio para manter senha atual'

    def clean_password_confirm(self):
        """Validar confirmação de senha"""
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password and password != password_confirm:
            raise forms.ValidationError('As senhas não coincidem.')

        return password_confirm

    def clean_port(self):
        """Validar porta"""
        port = self.cleaned_data.get('port')
        if port and (port < 1 or port > 65535):
            raise forms.ValidationError('A porta deve estar entre 1 e 65535.')
        return port

    def clean(self):
        """Validação geral do formulário"""
        cleaned_data = super().clean()
        engine = cleaned_data.get('engine')
        database_name = cleaned_data.get('database_name')
        host = cleaned_data.get('host')
        user = cleaned_data.get('user')

        # Validações específicas por engine
        if engine == 'django.db.backends.sqlite3':
            if not database_name:
                raise forms.ValidationError({'database_name': 'Nome do arquivo SQLite é obrigatório.'})
        else:
            if not host:
                raise forms.ValidationError({'host': 'Host é obrigatório para este tipo de banco.'})
            if not database_name:
                raise forms.ValidationError({'database_name': 'Nome do banco é obrigatório.'})
            if not user:
                raise forms.ValidationError({'user': 'Usuário é obrigatório para este tipo de banco.'})

        return cleaned_data


class WidgetForm(forms.ModelForm):
    """Formulário para configuração de widgets"""

    class Meta:
        model = Widget
        fields = ['name', 'description', 'widget_type', 'size', 'position_x', 'position_y',
                 'order', 'is_active', 'is_public', 'required_permission', 'config_json',
                 'template_path', 'custom_css', 'custom_js']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'config_json': forms.Textarea(attrs={'rows': 5, 'placeholder': '{"key": "value"}'}),
            'custom_css': forms.Textarea(attrs={'rows': 8, 'placeholder': '.widget-custom { ... }'}),
            'custom_js': forms.Textarea(attrs={'rows': 8, 'placeholder': 'function initWidget() { ... }'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Adicionar classes CSS
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean_config_json(self):
        """Valida o JSON de configuração"""
        config_json = self.cleaned_data.get('config_json')
        if config_json:
            try:
                json.loads(config_json)
            except json.JSONDecodeError:
                raise forms.ValidationError('JSON inválido. Verifique a sintaxe.')
        return config_json


class MenuConfigForm(forms.ModelForm):
    """Formulário para configuração de menus"""

    class Meta:
        model = MenuConfig
        fields = ['name', 'menu_type', 'parent', 'title', 'url', 'icon_type', 'icon',
                 'order', 'is_active', 'is_external', 'open_in_new_tab', 'required_permission',
                 'required_group', 'staff_only', 'authenticated_only', 'css_class',
                 'badge_text', 'badge_color']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrar parent para mostrar apenas itens do mesmo tipo de menu
        if 'menu_type' in self.data:
            menu_type = self.data['menu_type']
            self.fields['parent'].queryset = MenuConfig.objects.filter(
                menu_type=menu_type,
                parent__isnull=True
            )
        elif self.instance.pk:
            self.fields['parent'].queryset = MenuConfig.objects.filter(
                menu_type=self.instance.menu_type,
                parent__isnull=True
            ).exclude(pk=self.instance.pk)

        # Adicionar classes CSS
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        menu_type = cleaned_data.get('menu_type')

        # Verificar se o parent é do mesmo tipo de menu
        if parent and parent.menu_type != menu_type:
            raise forms.ValidationError('O item pai deve ser do mesmo tipo de menu.')

        # Verificar se não está tentando ser pai de si mesmo
        if self.instance.pk and parent and parent.pk == self.instance.pk:
            raise forms.ValidationError('Um item não pode ser pai de si mesmo.')

        return cleaned_data


class PluginForm(forms.ModelForm):
    """Formulário para configuração de plugins"""

    class Meta:
        model = Plugin
        fields = ['name', 'description', 'plugin_type', 'version', 'author', 'author_email',
                 'homepage', 'module_path', 'entry_point', 'dependencies', 'config_schema',
                 'config_data', 'is_core', 'auto_load', 'required_permissions']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'dependencies': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': '["django", "requests", {"module": "numpy", "min_version": "1.0.0"}]'
            }),
            'config_schema': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': '{"type": "object", "properties": {"api_key": {"type": "string"}}}'
            }),
            'config_data': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': '{"api_key": "your-api-key", "timeout": 30}'
            }),
            'required_permissions': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': '["auth.view_user", "config.change_systemconfig"]'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Adicionar classes CSS
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean_dependencies(self):
        """Valida a lista de dependências"""
        dependencies = self.cleaned_data.get('dependencies')
        if dependencies:
            try:
                deps = json.loads(dependencies)
                if not isinstance(deps, list):
                    raise forms.ValidationError('Dependências devem ser uma lista.')
            except json.JSONDecodeError:
                raise forms.ValidationError('JSON inválido para dependências.')
        return dependencies

    def clean_config_schema(self):
        """Valida o schema de configuração"""
        config_schema = self.cleaned_data.get('config_schema')
        if config_schema:
            try:
                json.loads(config_schema)
            except json.JSONDecodeError:
                raise forms.ValidationError('JSON inválido para schema de configuração.')
        return config_schema

    def clean_config_data(self):
        """Valida os dados de configuração"""
        config_data = self.cleaned_data.get('config_data')
        if config_data:
            try:
                json.loads(config_data)
            except json.JSONDecodeError:
                raise forms.ValidationError('JSON inválido para dados de configuração.')
        return config_data

    def clean_required_permissions(self):
        """Valida a lista de permissões necessárias"""
        required_permissions = self.cleaned_data.get('required_permissions')
        if required_permissions:
            try:
                perms = json.loads(required_permissions)
                if not isinstance(perms, list):
                    raise forms.ValidationError('Permissões devem ser uma lista.')
            except json.JSONDecodeError:
                raise forms.ValidationError('JSON inválido para permissões.')
        return required_permissions


class ConfigBackupForm(forms.ModelForm):
    """Formulário para criação de backup de configurações"""

    class Meta:
        model = ConfigBackup
        fields = ['name', 'description', 'backup_type']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Adicionar classes CSS
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class LDAPConfigForm(forms.ModelForm):
    """Formulário para configuração LDAP"""

    bind_password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label='Confirmar Senha de Bind'
    )

    class Meta:
        model = LDAPConfig
        fields = [
            'server', 'port', 'server_uri', 'base_dn', 'bind_dn', 'bind_password',
            'domain', 'search_filter', 'is_active'
        ]
        widgets = {
            'bind_password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'search_filter': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(objectClass=person)'
            }),
            'server_uri': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ldap://servidor.exemplo.com:389'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Adicionar classes CSS
        for field_name, field in self.fields.items():
            if field_name not in ['bind_password', 'bind_password_confirm']:
                field.widget.attrs.update({'class': 'form-control'})

        # Configurar placeholders
        self.fields['server'].widget.attrs.update({
            'placeholder': 'servidor.exemplo.com'
        })
        self.fields['base_dn'].widget.attrs.update({
            'placeholder': 'dc=exemplo,dc=com'
        })
        self.fields['bind_dn'].widget.attrs.update({
            'placeholder': 'cn=admin,dc=exemplo,dc=com'
        })
        self.fields['domain'].widget.attrs.update({
            'placeholder': 'exemplo.com'
        })

        # Se editando, preencher senha atual
        if self.instance and self.instance.pk:
            self.fields['bind_password'].widget.attrs['placeholder'] = 'Deixe vazio para manter senha atual'
            self.fields['bind_password_confirm'].widget.attrs['placeholder'] = 'Deixe vazio para manter senha atual'

    def clean_bind_password_confirm(self):
        """Validar confirmação de senha"""
        password = self.cleaned_data.get('bind_password')
        password_confirm = self.cleaned_data.get('bind_password_confirm')

        if password and password != password_confirm:
            raise forms.ValidationError('As senhas não coincidem.')

        return password_confirm

    def clean_port(self):
        """Validar porta LDAP"""
        port = self.cleaned_data.get('port')
        if port and (port < 1 or port > 65535):
            raise forms.ValidationError('A porta deve estar entre 1 e 65535.')
        return port

    def clean_server_uri(self):
        """Validar URI do servidor"""
        server_uri = self.cleaned_data.get('server_uri')
        if server_uri and not (server_uri.startswith('ldap://') or server_uri.startswith('ldaps://')):
            raise forms.ValidationError('URI deve começar com ldap:// ou ldaps://')
        return server_uri

    def save(self, commit=True):
        """Salvar com tratamento de senha"""
        instance = super().save(commit=False)

        # Tratar senha
        password = self.cleaned_data.get('bind_password')
        if password:
            instance.set_password(password)

        if commit:
            instance.save()

        return instance