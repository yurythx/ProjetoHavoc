from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from .models import CustomUser, Cargo, Departamento

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Nome de usuário', 'autocomplete': 'username'}),
        help_text='Obrigatório. 150 caracteres ou menos. Letras, números e @/./+/-/_ apenas.'
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email', 'autocomplete': 'email'}),
        help_text='Digite um email válido e real. Este será usado para recuperação de senha.'
    )

    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'placeholder': 'Senha', 'autocomplete': 'new-password'}),
        help_text='Sua senha deve conter pelo menos 8 caracteres e não pode ser comum.'
    )

    password2 = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirme a senha', 'autocomplete': 'new-password'}),
        help_text='Digite a mesma senha do campo anterior, para verificação.'
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise ValidationError('A senha deve ter pelo menos 8 caracteres.')
        return password1

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Verificar se email já está sendo usado
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('Este email já está sendo usado.')

        # Validação avançada de email (nível básico - rápido)
        from .validators import validate_real_email_basic
        try:
            validate_real_email_basic(email)
        except ValidationError as e:
            raise ValidationError(str(e.message))

        return email


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')


class CodigoAtivacaoForm(forms.Form):
    """Formulário para inserção do código de ativação"""

    email = forms.EmailField(
        label='Email da Conta',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu email',
            'autocomplete': 'email'
        }),
        help_text='Digite o email da conta que deseja ativar'
    )

    codigo = forms.CharField(
        label='Código de Ativação',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '000000',
            'autocomplete': 'off',
            'style': 'font-size: 2rem; letter-spacing: 0.5rem; font-weight: bold;',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric'
        }),
        help_text='Digite o código de 6 dígitos enviado para seu email'
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('O email é obrigatório.')

        # Verificar se existe usuário inativo com este email
        try:
            user = CustomUser.objects.get(email=email, is_active=False)
        except CustomUser.DoesNotExist:
            raise ValidationError(
                'Não encontramos uma conta inativa com este email. '
                'Verifique se o email está correto ou se a conta já foi ativada.'
            )

        return email

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if not codigo:
            raise ValidationError('O código é obrigatório.')

        if not codigo.isdigit():
            raise ValidationError('O código deve conter apenas números.')

        if len(codigo) != 6:
            raise ValidationError('O código deve ter exatamente 6 dígitos.')

        return codigo

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        codigo = cleaned_data.get('codigo')

        if email and codigo:
            try:
                user = CustomUser.objects.get(email=email, is_active=False)

                # Verificar se o usuário tem um código de ativação
                if not user.codigo_ativacao:
                    raise ValidationError(
                        'Esta conta não possui um código de ativação válido. '
                        'Solicite um novo código.'
                    )

                # Verificar se o código não expirou
                if not user.codigo_ativacao_valido():
                    raise ValidationError(
                        'O código de ativação expirou. Solicite um novo código.'
                    )

                # Verificar limite de tentativas
                if user.tentativas_codigo >= 5:
                    raise ValidationError(
                        'Muitas tentativas incorretas. Solicite um novo código.'
                    )

            except CustomUser.DoesNotExist:
                # Erro já tratado em clean_email
                pass

        return cleaned_data


class SolicitarCodigoForm(forms.Form):
    """Formulário para solicitar novo código de ativação"""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu email',
            'autocomplete': 'email'
        }),
        help_text='Digite o email da conta que deseja ativar'
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('O email é obrigatório.')

        try:
            user = CustomUser.objects.get(email=email, is_active=False)
        except CustomUser.DoesNotExist:
            raise ValidationError('Não encontramos uma conta inativa com este email.')

        return email


class EditProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].widget.attrs.update({
            'onchange': 'previewImage(this)'
        })
        # Adicionar opções para cargo e departamento
        self.fields['cargo'].queryset = Cargo.objects.all()
        self.fields['departamento'].queryset = Departamento.objects.all()

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Nome de usuário'}),
        help_text='Obrigatório. 150 caracteres ou menos. Letras, números e @/./+/-/_ apenas.'
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email'}),
        help_text='Digite um email válido. Este será usado para recuperação de senha.',
        validators=[EmailValidator(message="Digite um endereço de email válido.")]
    )

    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Nome'}),
        help_text='Seu nome.'
    )

    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Sobrenome'}),
        help_text='Seu sobrenome.'
    )

    bio = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Fale um pouco sobre você', 'rows': 3}),
        max_length=500,
        required=False
    )

    data_nascimento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    telefone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '(99) 99999-9999'})
    )

    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Selecione um cargo"
    )

    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Selecione um departamento"
    )

    avatar = forms.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'first_name', 'last_name', 'avatar', 'bio',
            'data_nascimento', 'telefone', 'cargo', 'departamento'
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("O email é obrigatório.")
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Este email já está em uso por outro usuário.")
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name and len(first_name.strip()) < 2:
            raise ValidationError("O nome deve ter pelo menos 2 caracteres.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name and len(last_name.strip()) < 2:
            raise ValidationError("O sobrenome deve ter pelo menos 2 caracteres.")
        return last_name

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and avatar.size > 2 * 1024 * 1024:  # 2MB
            raise ValidationError('A imagem deve ter no máximo 2MB.')
        return avatar

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            # Remove caracteres não numéricos
            telefone_numerico = ''.join(filter(str.isdigit, telefone))

            # Verifica se o telefone tem pelo menos 10 dígitos (DDD + número)
            if len(telefone_numerico) < 10:
                raise ValidationError('O telefone deve ter pelo menos 10 dígitos, incluindo o DDD.')

            # Formata o telefone como (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
            if len(telefone_numerico) == 11:  # Celular com 9 dígitos
                telefone_formatado = f'({telefone_numerico[:2]}) {telefone_numerico[2:7]}-{telefone_numerico[7:]}'
            elif len(telefone_numerico) == 10:  # Telefone fixo
                telefone_formatado = f'({telefone_numerico[:2]}) {telefone_numerico[2:6]}-{telefone_numerico[6:]}'
            else:
                telefone_formatado = telefone_numerico

            return telefone_formatado
        return telefone


class UserProfileForm(forms.ModelForm):
    """Formulário somente leitura opcional para ProfileView, se quiser exibir com form."""
    class Meta:
        model = CustomUser
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
            'email': forms.EmailInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
        }


class EmailSettingsForm(forms.Form):
    host = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    port = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    user = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    use_tls = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class SocialAuthSettingsForm(forms.Form):
    google_client_id = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    google_secret = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    github_client_id = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    github_secret = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )


class LDAPSettingsForm(forms.Form):
    server_uri = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='URI do servidor LDAP (ex: ldap://servidor.exemplo.com:389)'
    )
    bind_dn = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='DN de ligação para autenticação no servidor LDAP'
    )
    bind_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True,
        help_text='Senha para autenticação no servidor LDAP'
    )
    domain = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'exemplo.com.br'}),
        help_text='Domínio para criação de emails de usuários LDAP'
    )
    user_search_base = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Base de pesquisa para usuários (ex: ou=users,dc=exemplo,dc=com)'
    )
    group_search_base = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Base de pesquisa para grupos (ex: ou=groups,dc=exemplo,dc=com)'
    )

    def clean_server_uri(self):
        server_uri = self.cleaned_data.get('server_uri')
        if not server_uri:
            raise ValidationError("A URI do servidor é obrigatória.")

        # Verificar se a URI começa com ldap:// ou ldaps://
        if not server_uri.startswith(('ldap://', 'ldaps://')):
            raise ValidationError("A URI deve começar com 'ldap://' ou 'ldaps://'")

        return server_uri

    def clean_domain(self):
        domain = self.cleaned_data.get('domain')
        if not domain:
            raise ValidationError("O domínio é obrigatório.")

        # Verificar se o domínio tem pelo menos um ponto
        if '.' not in domain:
            raise ValidationError("O domínio deve ser válido (ex: exemplo.com.br)")

        # Verificar se o domínio tem pelo menos 4 caracteres
        if len(domain) < 4:
            raise ValidationError("O domínio deve ter pelo menos 4 caracteres.")

        return domain


class UserManagementForm(forms.ModelForm):
    """Formulário para gestão de usuários por administradores"""

    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'}),
        required=False,
        help_text='Deixe em branco para manter a senha atual (apenas na edição)'
    )

    password2 = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirme a senha'}),
        required=False,
        help_text='Digite a mesma senha do campo anterior'
    )

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text='Selecione os grupos do usuário'
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'cargo', 'departamento',
            'telefone', 'data_nascimento', 'bio', 'avatar'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de usuário'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(99) 99999-9999'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Biografia'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'cargo': forms.Select(attrs={'class': 'form-control'}),
            'departamento': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'username': 'Obrigatório. 150 caracteres ou menos. Letras, números e @/./+/-/_ apenas.',
            'email': 'Digite um email válido.',
            'is_active': 'Determina se o usuário pode fazer login no sistema.',
            'is_staff': 'Determina se o usuário pode acessar o painel administrativo.',
        }

    def __init__(self, *args, **kwargs):
        # Extrair o usuário que está fazendo a edição
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

        # Se estamos editando um usuário existente
        if self.instance and self.instance.pk:
            # Tornar senha opcional na edição
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            self.fields['password1'].help_text = 'Deixe em branco para manter a senha atual'

            # Pré-selecionar grupos do usuário
            self.fields['groups'].initial = self.instance.groups.all()
        else:
            # Na criação, senha é obrigatória
            self.fields['password1'].required = True
            self.fields['password2'].required = True
            self.fields['password1'].help_text = 'Senha deve ter pelo menos 8 caracteres'

        # Configurar querysets
        self.fields['cargo'].queryset = Cargo.objects.all()
        self.fields['departamento'].queryset = Departamento.objects.all()

        # Garantir que os grupos básicos existam
        Group.objects.get_or_create(name='Usuario')
        Group.objects.get_or_create(name='Administrador')

        # Aplicar restrições de segurança baseadas no usuário atual
        self._apply_security_restrictions()

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')

        # Se é criação ou se uma senha foi fornecida
        if not self.instance.pk or password1:
            if not password1:
                raise ValidationError('A senha é obrigatória.')
            if len(password1) < 8:
                raise ValidationError('A senha deve ter pelo menos 8 caracteres.')

        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        # Se é criação ou se uma senha foi fornecida
        if not self.instance.pk or password1:
            if password1 != password2:
                raise ValidationError('As senhas não coincidem.')

        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("O email é obrigatório.")

        # Verificar se o email já existe (excluindo o usuário atual na edição)
        queryset = CustomUser.objects.filter(email=email)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError("Este email já está em uso por outro usuário.")

        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError("O nome de usuário é obrigatório.")

        # Verificar se o username já existe (excluindo o usuário atual na edição)
        queryset = CustomUser.objects.filter(username=username)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError("Este nome de usuário já está em uso.")

        return username

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            # Remove caracteres não numéricos
            telefone_numerico = ''.join(filter(str.isdigit, telefone))

            # Verifica se o telefone tem pelo menos 10 dígitos (DDD + número)
            if len(telefone_numerico) < 10:
                raise ValidationError('O telefone deve ter pelo menos 10 dígitos, incluindo o DDD.')

            if len(telefone_numerico) > 11:
                raise ValidationError('O telefone deve ter no máximo 11 dígitos.')

            # Verifica se o DDD é válido (11 a 99)
            ddd = int(telefone_numerico[:2])
            if ddd < 11 or ddd > 99:
                raise ValidationError('DDD inválido. Deve estar entre 11 e 99.')

            # Formata o telefone
            if len(telefone_numerico) == 11:  # Celular com 9 dígitos
                telefone_formatado = f'({telefone_numerico[:2]}) {telefone_numerico[2:7]}-{telefone_numerico[7:]}'
            elif len(telefone_numerico) == 10:  # Telefone fixo
                telefone_formatado = f'({telefone_numerico[:2]}) {telefone_numerico[2:6]}-{telefone_numerico[6:]}'
            else:
                telefone_formatado = telefone_numerico

            return telefone_formatado
        return telefone

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            first_name = first_name.strip()
            if len(first_name) < 2:
                raise ValidationError('O nome deve ter pelo menos 2 caracteres.')
            if not first_name.replace(' ', '').isalpha():
                raise ValidationError('O nome deve conter apenas letras e espaços.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            last_name = last_name.strip()
            if len(last_name) < 2:
                raise ValidationError('O sobrenome deve ter pelo menos 2 caracteres.')
            if not last_name.replace(' ', '').isalpha():
                raise ValidationError('O sobrenome deve conter apenas letras e espaços.')
        return last_name

    def clean_data_nascimento(self):
        data_nascimento = self.cleaned_data.get('data_nascimento')
        if data_nascimento:
            from datetime import date
            hoje = date.today()
            idade = hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))

            if data_nascimento > hoje:
                raise ValidationError('A data de nascimento não pode ser no futuro.')

            if idade < 16:
                raise ValidationError('O usuário deve ter pelo menos 16 anos.')

            if idade > 120:
                raise ValidationError('Data de nascimento inválida.')

        return data_nascimento

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Verificar tamanho do arquivo (máximo 5MB)
            if avatar.size > 5 * 1024 * 1024:
                raise ValidationError('O arquivo de avatar deve ter no máximo 5MB.')

            # Verificar tipo de arquivo
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            import os
            ext = os.path.splitext(avatar.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError('Formato de arquivo inválido. Use JPG, PNG ou GIF.')

        return avatar

    def _apply_security_restrictions(self):
        """Aplicar restrições de segurança baseadas no usuário atual"""
        if not self.current_user:
            return

        # Verificar se o usuário atual é administrador
        is_admin = (
            self.current_user.is_superuser or
            self.current_user.is_staff or
            self.current_user.groups.filter(name='Administrador').exists()
        )

        if not is_admin:
            # Usuários não-administradores não podem alterar permissões
            if 'is_staff' in self.fields:
                self.fields['is_staff'].widget.attrs['disabled'] = True
                self.fields['is_staff'].help_text = 'Apenas administradores podem alterar este campo.'

            # Restringir grupos disponíveis
            if 'groups' in self.fields:
                # Apenas grupo "Usuario" disponível para não-administradores
                self.fields['groups'].queryset = Group.objects.filter(name='Usuario')
                self.fields['groups'].help_text = 'Apenas administradores podem alterar grupos.'

    def clean_is_staff(self):
        """Validar alterações no campo is_staff"""
        is_staff = self.cleaned_data.get('is_staff')

        # Verificar se o usuário atual pode alterar permissões administrativas
        if self.current_user and is_staff:
            is_admin = (
                self.current_user.is_superuser or
                self.current_user.is_staff or
                self.current_user.groups.filter(name='Administrador').exists()
            )

            if not is_admin:
                raise ValidationError(
                    'Apenas administradores ou superusuários podem conceder privilégios administrativos.'
                )

        return is_staff

    def clean_groups(self):
        """Validar alterações nos grupos"""
        groups = self.cleaned_data.get('groups')

        if self.current_user and groups:
            is_admin = (
                self.current_user.is_superuser or
                self.current_user.is_staff or
                self.current_user.groups.filter(name='Administrador').exists()
            )

            # Verificar se está tentando adicionar ao grupo Administrador
            admin_group = Group.objects.filter(name='Administrador').first()
            if admin_group and admin_group in groups and not is_admin:
                raise ValidationError(
                    'Apenas administradores ou superusuários podem adicionar usuários ao grupo Administrador.'
                )

        return groups

    def clean(self):
        """Validações gerais do formulário"""
        cleaned_data = super().clean()

        # Garantir que novos usuários sempre tenham pelo menos o grupo "Usuario"
        if not self.instance.pk:  # Novo usuário
            groups = cleaned_data.get('groups')
            if not groups:
                usuario_group, created = Group.objects.get_or_create(name='Usuario')
                cleaned_data['groups'] = [usuario_group]

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Se uma nova senha foi fornecida, defini-la
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        elif not user.pk:
            # Se é um novo usuário e não tem senha, gerar uma temporária
            import secrets
            import string
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            user.set_password(temp_password)

        # Aplicar restrições de segurança para novos usuários
        if not user.pk:  # Novo usuário
            # Verificar se o usuário atual pode criar administradores
            if self.current_user:
                is_admin = (
                    self.current_user.is_superuser or
                    self.current_user.is_staff or
                    self.current_user.groups.filter(name='Administrador').exists()
                )

                if not is_admin:
                    # Forçar valores seguros para não-administradores
                    user.is_staff = False
                    user.is_superuser = False
            else:
                # Se não há usuário atual (caso de registro público), aplicar valores seguros
                user.is_staff = False
                user.is_superuser = False

        if commit:
            user.save()
            self.save_m2m()  # Salvar relações many-to-many (grupos)

        return user
