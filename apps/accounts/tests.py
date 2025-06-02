"""
Testes completos para o app accounts
"""

from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from django.test.utils import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import time
from datetime import timedelta, date

from .models import CustomUser, Cargo, Departamento, UserAuditLog
from .forms import CustomUserCreationForm, EditProfileForm, CodigoAtivacaoForm

User = get_user_model()

class CustomUserTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_user(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertFalse(self.user.is_active)
        self.assertTrue(self.user.check_password('testpass123'))

    def test_get_avatar_url_no_avatar(self):
        self.assertEqual(self.user.get_avatar_url(), '/static/img/default_avatar.png')

class CustomUserCreationFormTests(TestCase):
    def test_valid_form(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'strongpass123',
            'password2': 'strongpass123'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_password(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'weak',  # senha muito curta
            'password2': 'weak'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)

    def test_duplicate_email(self):
        # Criar um usuário primeiro
        CustomUser.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )

        # Tentar criar outro usuário com o mesmo email
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com',  # email duplicado
            'password1': 'strongpass123',
            'password2': 'strongpass123'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

class EditProfileFormTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_valid_avatar_upload(self):
        # Criar um arquivo de imagem simulado
        avatar = SimpleUploadedFile(
            name='test_avatar.jpg',
            content=b'',  # conteúdo vazio para teste
            content_type='image/jpeg'
        )

        form_data = {
            'username': 'testuser',
            'email': 'test@example.com'
        }
        form_files = {'avatar': avatar}

        form = EditProfileForm(data=form_data, files=form_files, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_large_avatar_upload(self):
        # Criar um arquivo de imagem grande simulado (>2MB)
        large_avatar = SimpleUploadedFile(
            name='large_avatar.jpg',
            content=b'x' * (2 * 1024 * 1024 + 1),  # 2MB + 1 byte
            content_type='image/jpeg'
        )

        form_data = {
            'username': 'testuser',
            'email': 'test@example.com'
        }
        form_files = {'avatar': large_avatar}

        form = EditProfileForm(data=form_data, files=form_files, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)


class LDAPAuthTests(TestCase):
    @patch('apps.accounts.auth_backends.LDAPBackend.authenticate')
    def test_ldap_auth_success(self, mock_auth):
        # Criar usuário mock para teste LDAP
        mock_user = CustomUser.objects.create_user(
            username='ldap_user',
            email='ldap@example.com',
            password='valid_pass'
        )
        mock_auth.return_value = mock_user

        response = self.client.post(reverse('accounts:login'), {
            'username': 'ldap_user',
            'password': 'valid_pass'
        })
        self.assertEqual(response.status_code, 302)


# =============================================================================
# TESTES UNITÁRIOS PARA MODELS
# =============================================================================

class CargoModelTests(TestCase):
    """Testes para o modelo Cargo"""

    def setUp(self):
        self.cargo = Cargo.objects.create(
            nome='Desenvolvedor',
            descricao='Desenvolvedor de software',
            nivel=3
        )

    def test_cargo_creation(self):
        """Testa criação de cargo"""
        self.assertEqual(self.cargo.nome, 'Desenvolvedor')
        self.assertEqual(self.cargo.nivel, 3)
        self.assertTrue(self.cargo.ativo)
        self.assertIsNotNone(self.cargo.created_at)

    def test_cargo_str_representation(self):
        """Testa representação string do cargo"""
        self.assertEqual(str(self.cargo), 'Desenvolvedor')

    def test_cargo_unique_nome(self):
        """Testa unicidade do nome do cargo"""
        with self.assertRaises(Exception):
            Cargo.objects.create(nome='Desenvolvedor', nivel=2)

    def test_cargo_ordering(self):
        """Testa ordenação por nível e nome"""
        cargo1 = Cargo.objects.create(nome='Junior', nivel=1)
        cargo2 = Cargo.objects.create(nome='Senior', nivel=5)

        cargos = list(Cargo.objects.all())
        self.assertEqual(cargos[0], cargo1)  # Menor nível primeiro
        self.assertEqual(cargos[1], self.cargo)
        self.assertEqual(cargos[2], cargo2)


class DepartamentoModelTests(TestCase):
    """Testes para o modelo Departamento"""

    def setUp(self):
        self.departamento = Departamento.objects.create(
            nome='TI',
            descricao='Tecnologia da Informação'
        )

    def test_departamento_creation(self):
        """Testa criação de departamento"""
        self.assertEqual(self.departamento.nome, 'TI')
        self.assertEqual(self.departamento.descricao, 'Tecnologia da Informação')
        self.assertTrue(self.departamento.ativo)

    def test_departamento_str_representation(self):
        """Testa representação string do departamento"""
        self.assertEqual(str(self.departamento), 'TI')

    def test_departamento_unique_nome(self):
        """Testa unicidade do nome do departamento"""
        with self.assertRaises(Exception):
            Departamento.objects.create(nome='TI')


class CustomUserModelTests(TestCase):
    """Testes para o modelo CustomUser"""

    def setUp(self):
        self.cargo, _ = Cargo.objects.get_or_create(
            nome='Desenvolvedor',
            defaults={'nivel': 3}
        )
        self.departamento, _ = Departamento.objects.get_or_create(nome='TI')

        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            data_nascimento=date(1990, 1, 1),
            cargo=self.cargo,
            departamento=self.departamento
        )

    def test_user_creation(self):
        """Testa criação de usuário"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertFalse(self.user.is_active)  # Usuários começam inativos
        self.assertEqual(self.user.cargo, self.cargo)
        self.assertEqual(self.user.departamento, self.departamento)

    def test_get_nome_completo(self):
        """Testa método get_nome_completo"""
        self.assertEqual(self.user.get_nome_completo(), 'Test User')

    def test_get_idade(self):
        """Testa cálculo de idade"""
        idade = self.user.get_idade()
        self.assertIsInstance(idade, int)
        self.assertGreater(idade, 30)  # Nasceu em 1990

    def test_get_idade_sem_data_nascimento(self):
        """Testa get_idade quando não há data de nascimento"""
        user_sem_data = CustomUser.objects.create_user(
            username='semdata',
            email='semdata@example.com',
            password='testpass123'
        )
        self.assertIsNone(user_sem_data.get_idade())

    def test_gerar_codigo_ativacao(self):
        """Testa geração de código de ativação"""
        codigo = self.user.gerar_codigo_ativacao()

        self.assertEqual(len(codigo), 6)
        self.assertTrue(codigo.isdigit())
        self.assertEqual(self.user.codigo_ativacao, codigo)
        self.assertIsNotNone(self.user.codigo_ativacao_criado_em)
        self.assertEqual(self.user.tentativas_codigo, 0)

    def test_codigo_ativacao_valido(self):
        """Testa validação de código de ativação"""
        # Sem código
        self.assertFalse(self.user.codigo_ativacao_valido())

        # Com código válido
        self.user.gerar_codigo_ativacao()
        self.assertTrue(self.user.codigo_ativacao_valido())

        # Código expirado
        self.user.codigo_ativacao_criado_em = timezone.now() - timedelta(hours=1)
        self.user.save()
        self.assertFalse(self.user.codigo_ativacao_valido())

    def test_verificar_codigo_ativacao(self):
        """Testa verificação de código de ativação"""
        codigo = self.user.gerar_codigo_ativacao()

        # Código correto
        valido, mensagem = self.user.verificar_codigo_ativacao(codigo)
        self.assertTrue(valido)
        self.assertEqual(mensagem, "Código válido.")

        # Código incorreto
        valido, mensagem = self.user.verificar_codigo_ativacao('000000')
        self.assertFalse(valido)
        self.assertIn("incorreto", mensagem)
        self.assertEqual(self.user.tentativas_codigo, 1)

    def test_bloqueio_conta(self):
        """Testa sistema de bloqueio de conta"""
        # Conta não bloqueada
        self.assertFalse(self.user.esta_bloqueado())

        # Bloquear conta
        self.user.bloquear_conta(30)
        self.assertTrue(self.user.esta_bloqueado())
        self.assertIsNotNone(self.user.bloqueado_ate)

        # Desbloquear conta
        self.user.desbloquear_conta()
        self.assertFalse(self.user.esta_bloqueado())
        self.assertIsNone(self.user.bloqueado_ate)
        self.assertEqual(self.user.tentativas_login_falhadas, 0)

    def test_tentativas_login_falhadas(self):
        """Testa registro de tentativas de login falhadas"""
        ip = '192.168.1.1'

        # Registrar tentativas
        for i in range(4):
            self.user.registrar_tentativa_login_falhada(ip)
            self.assertEqual(self.user.tentativas_login_falhadas, i + 1)
            self.assertFalse(self.user.esta_bloqueado())

        # Quinta tentativa deve bloquear
        self.user.registrar_tentativa_login_falhada(ip)
        self.assertEqual(self.user.tentativas_login_falhadas, 5)
        self.assertTrue(self.user.esta_bloqueado())

    def test_login_sucesso(self):
        """Testa registro de login bem-sucedido"""
        ip = '192.168.1.1'

        # Simular tentativas falhadas
        self.user.tentativas_login_falhadas = 3
        self.user.bloquear_conta(30)

        # Login bem-sucedido deve limpar tudo
        self.user.registrar_login_sucesso(ip)
        self.assertEqual(self.user.tentativas_login_falhadas, 0)
        self.assertFalse(self.user.esta_bloqueado())
        self.assertEqual(self.user.ultimo_login_ip, ip)


class UserAuditLogModelTests(TestCase):
    """Testes para o modelo UserAuditLog"""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_log_creation(self):
        """Testa criação de log de auditoria"""
        log = UserAuditLog.log_action(
            user=self.user,
            action='login',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            login_method='web'
        )

        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'login')
        self.assertEqual(log.ip_address, '192.168.1.1')
        self.assertEqual(log.user_agent, 'Mozilla/5.0')
        self.assertEqual(log.details['login_method'], 'web')
        self.assertIsNotNone(log.timestamp)

    def test_log_str_representation(self):
        """Testa representação string do log"""
        log = UserAuditLog.log_action(
            user=self.user,
            action='login',
            ip_address='192.168.1.1'
        )

        expected = f'{self.user.username} - Login - {log.timestamp}'
        self.assertEqual(str(log), expected)

    def test_log_ordering(self):
        """Testa ordenação dos logs por timestamp decrescente"""
        log1 = UserAuditLog.log_action(user=self.user, action='login')
        time.sleep(0.01)  # Pequena pausa para garantir timestamps diferentes
        log2 = UserAuditLog.log_action(user=self.user, action='logout')

        logs = list(UserAuditLog.objects.all())
        self.assertEqual(logs[0], log2)  # Mais recente primeiro
        self.assertEqual(logs[1], log1)


# =============================================================================
# TESTES DE INTEGRAÇÃO PARA VIEWS
# =============================================================================

class RegisterViewTests(TestCase):
    """Testes para a view de registro"""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')

    def test_register_get(self):
        """Testa acesso à página de registro"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Criar Conta')

    def test_register_post_valid(self):
        """Testa registro com dados válidos"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'strongpass123',
            'password2': 'strongpass123'
        }

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect após sucesso

        # Verificar se usuário foi criado
        user = CustomUser.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertFalse(user.is_active)  # Deve estar inativo
        self.assertIsNotNone(user.codigo_ativacao)  # Deve ter código

    def test_register_post_invalid_password(self):
        """Testa registro com senha inválida"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'weak',
            'password2': 'weak'
        }

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)  # Permanece na página
        self.assertContains(response, 'A senha deve ter pelo menos 8 caracteres')

    def test_register_duplicate_email(self):
        """Testa registro com email duplicado"""
        # Criar usuário existente
        CustomUser.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='testpass123'
        )

        data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'strongpass123',
            'password2': 'strongpass123'
        }

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Este email já está cadastrado')


class LoginViewTests(TestCase):
    """Testes para a view de login"""

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()

    def test_login_get(self):
        """Testa acesso à página de login"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Entrar')

    def test_login_post_valid(self):
        """Testa login com credenciais válidas"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect após sucesso

        # Verificar se usuário está logado
        user = CustomUser.objects.get(username='testuser')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_login_post_invalid(self):
        """Testa login com credenciais inválidas"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }

        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)  # Permanece na página
        self.assertContains(response, 'credenciais inválidas')

    def test_login_inactive_user(self):
        """Testa login com usuário inativo"""
        self.user.is_active = False
        self.user.save()

        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'conta está inativa')


class ProfileViewTests(TestCase):
    """Testes para a view de perfil"""

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()
        self.profile_url = reverse('accounts:profile')

    def test_profile_requires_login(self):
        """Testa que perfil requer login"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)  # Redirect para login

    def test_profile_authenticated_user(self):
        """Testa acesso ao perfil com usuário autenticado"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')


class UserListViewTests(TestCase):
    """Testes para a view de listagem de usuários"""

    def setUp(self):
        self.client = Client()

        # Criar usuário admin
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.admin_user.is_staff = True
        self.admin_user.is_active = True
        self.admin_user.save()

        # Criar usuários normais
        self.cargo, _ = Cargo.objects.get_or_create(
            nome='Desenvolvedor',
            defaults={'nivel': 3}
        )
        self.departamento, _ = Departamento.objects.get_or_create(nome='TI')

        for i in range(25):  # Criar 25 usuários para testar paginação
            CustomUser.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123',
                cargo=self.cargo,
                departamento=self.departamento
            )

        self.user_list_url = reverse('accounts:user_list')

    def test_user_list_requires_staff(self):
        """Testa que listagem requer privilégios de staff"""
        # Usuário normal
        normal_user = CustomUser.objects.create_user(
            username='normal',
            email='normal@example.com',
            password='testpass123'
        )
        normal_user.is_active = True
        normal_user.save()

        self.client.login(username='normal', password='testpass123')
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_user_list_staff_access(self):
        """Testa acesso à listagem com usuário staff"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lista de Usuários')

    def test_user_list_pagination(self):
        """Testa paginação da listagem"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(self.user_list_url)

        # Deve ter paginação (20 por página)
        self.assertContains(response, 'page')
        self.assertEqual(len(response.context['users']), 20)

    def test_user_list_search(self):
        """Testa busca na listagem"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(self.user_list_url + '?search=user1')

        # Deve encontrar usuários que contenham 'user1'
        self.assertContains(response, 'user1')
        self.assertContains(response, 'user10')  # user10, user11, etc.

    def test_user_list_filters(self):
        """Testa filtros da listagem"""
        self.client.login(username='admin', password='adminpass123')

        # Filtro por cargo
        response = self.client.get(self.user_list_url + f'?cargo={self.cargo.id}')
        self.assertEqual(response.status_code, 200)

        # Filtro por departamento
        response = self.client.get(self.user_list_url + f'?departamento={self.departamento.id}')
        self.assertEqual(response.status_code, 200)

        # Filtro por status
        response = self.client.get(self.user_list_url + '?status=inactive')
        self.assertEqual(response.status_code, 200)


# =============================================================================
# TESTES DE PERFORMANCE
# =============================================================================

class PerformanceTests(TransactionTestCase):
    """Testes de performance para operações críticas"""

    def setUp(self):
        self.client = Client()

        # Criar dados de teste
        self.cargo, _ = Cargo.objects.get_or_create(
            nome='Desenvolvedor',
            defaults={'nivel': 3}
        )
        self.departamento, _ = Departamento.objects.get_or_create(nome='TI')

        # Criar usuário admin
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.admin_user.is_staff = True
        self.admin_user.is_active = True
        self.admin_user.save()

    def test_user_list_performance(self):
        """Testa performance da listagem de usuários"""
        # Criar muitos usuários
        users = []
        for i in range(100):
            users.append(CustomUser(
                username=f'user{i}',
                email=f'user{i}@example.com',
                cargo=self.cargo,
                departamento=self.departamento
            ))
        CustomUser.objects.bulk_create(users)

        self.client.login(username='admin', password='adminpass123')

        # Medir tempo de resposta
        start_time = time.time()
        response = self.client.get(reverse('accounts:user_list'))
        end_time = time.time()

        response_time = end_time - start_time

        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 2.0)  # Deve responder em menos de 2 segundos

        # Verificar se está usando select_related (menos queries)
        with self.assertNumQueries(10):  # Número máximo de queries esperado
            self.client.get(reverse('accounts:user_list'))

    def test_user_creation_performance(self):
        """Testa performance da criação de usuários"""
        start_time = time.time()

        for i in range(10):
            CustomUser.objects.create_user(
                username=f'perfuser{i}',
                email=f'perfuser{i}@example.com',
                password='testpass123'
            )

        end_time = time.time()
        creation_time = end_time - start_time

        self.assertLess(creation_time, 1.0)  # 10 usuários em menos de 1 segundo

    def test_audit_log_performance(self):
        """Testa performance dos logs de auditoria"""
        user = CustomUser.objects.create_user(
            username='audituser',
            email='audit@example.com',
            password='testpass123'
        )

        start_time = time.time()

        # Criar muitos logs
        for i in range(100):
            UserAuditLog.log_action(
                user=user,
                action='login',
                ip_address='192.168.1.1'
            )

        end_time = time.time()
        log_time = end_time - start_time

        self.assertLess(log_time, 1.0)  # 100 logs em menos de 1 segundo


# =============================================================================
# TESTES DE SEGURANÇA
# =============================================================================

class SecurityTests(TestCase):
    """Testes de segurança"""

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()

    def test_rate_limiting_login(self):
        """Testa rate limiting no login"""
        login_url = reverse('accounts:login')

        # Fazer muitas tentativas de login falhadas
        for i in range(6):
            response = self.client.post(login_url, {
                'username': 'testuser',
                'password': 'wrongpassword'
            })

        # Verificar se usuário foi bloqueado
        self.user.refresh_from_db()
        self.assertGreater(self.user.tentativas_login_falhadas, 0)

    def test_account_lockout(self):
        """Testa bloqueio de conta após tentativas falhadas"""
        # Simular 5 tentativas falhadas
        for i in range(5):
            self.user.registrar_tentativa_login_falhada('192.168.1.1')

        # Conta deve estar bloqueada
        self.assertTrue(self.user.esta_bloqueado())

        # Tentar fazer login com conta bloqueada
        login_url = reverse('accounts:login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })

        # Login deve falhar mesmo com senha correta
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_password_validation(self):
        """Testa validação de senhas fracas"""
        register_url = reverse('accounts:register')

        weak_passwords = [
            'password',  # Muito comum
            '123456',    # Muito simples
            'abc',       # Muito curta
            'testuser',  # Igual ao username
        ]

        for weak_password in weak_passwords:
            response = self.client.post(register_url, {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password1': weak_password,
                'password2': weak_password
            })

            # Deve rejeitar senha fraca
            self.assertEqual(response.status_code, 200)  # Permanece na página
            self.assertContains(response, 'senha')  # Mensagem de erro sobre senha

    def test_sql_injection_protection(self):
        """Testa proteção contra SQL injection"""
        # Tentar SQL injection no campo de busca
        self.client.login(username='testuser', password='testpass123')

        malicious_input = "'; DROP TABLE accounts_customuser; --"
        response = self.client.get(
            reverse('accounts:user_list') + f'?search={malicious_input}'
        )

        # Deve retornar normalmente sem executar SQL malicioso
        self.assertEqual(response.status_code, 200)

        # Verificar se tabela ainda existe
        self.assertTrue(CustomUser.objects.filter(username='testuser').exists())

    def test_xss_protection(self):
        """Testa proteção contra XSS"""
        # Tentar XSS no campo de nome
        xss_payload = '<script>alert("XSS")</script>'

        self.user.first_name = xss_payload
        self.user.save()

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))

        # Script não deve ser executado (deve estar escapado)
        self.assertNotContains(response, '<script>')
        self.assertContains(response, '&lt;script&gt;')  # Escapado

    def test_csrf_protection(self):
        """Testa proteção CSRF"""
        # Tentar POST sem token CSRF
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'strongpass123',
            'password2': 'strongpass123'
        })

        # Deve ser rejeitado por falta de token CSRF
        self.assertEqual(response.status_code, 403)

    def test_session_security(self):
        """Testa segurança de sessão"""
        # Fazer login
        self.client.login(username='testuser', password='testpass123')

        # Verificar se sessão foi criada
        self.assertIn('_auth_user_id', self.client.session)

        # Simular logout
        self.client.logout()

        # Verificar se sessão foi limpa
        self.assertNotIn('_auth_user_id', self.client.session)


# =============================================================================
# TESTES DE CACHE
# =============================================================================

class CacheTests(TestCase):
    """Testes para funcionalidades de cache"""

    def setUp(self):
        self.client = Client()
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.admin_user.is_staff = True
        self.admin_user.is_active = True
        self.admin_user.save()

        # Limpar cache antes dos testes
        cache.clear()

    def test_user_list_cache(self):
        """Testa cache da listagem de usuários"""
        self.client.login(username='admin', password='adminpass123')

        # Primeira requisição - deve popular o cache
        response1 = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response1.status_code, 200)

        # Verificar se dados foram cacheados
        self.assertIsNotNone(cache.get('user_list_groups'))
        self.assertIsNotNone(cache.get('user_list_stats'))

        # Segunda requisição - deve usar cache
        response2 = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response2.status_code, 200)

    def test_cache_invalidation(self):
        """Testa invalidação de cache"""
        # Popular cache
        self.client.login(username='admin', password='adminpass123')
        self.client.get(reverse('accounts:user_list'))

        # Verificar se cache existe
        self.assertIsNotNone(cache.get('user_list_stats'))

        # Criar novo usuário (deve invalidar cache)
        CustomUser.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123'
        )

        # Cache de estatísticas deve ser invalidado automaticamente
        # (isso dependeria da implementação de signals para invalidação)

    def tearDown(self):
        cache.clear()
