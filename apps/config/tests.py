from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import SystemConfig, AppConfig, DatabaseConfig, LDAPConfig, EnvironmentVariable

User = get_user_model()


class ConfigViewsTestCase(TestCase):
    """Testes para as views de configuração"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='testpass123'
        )

    def test_config_view_requires_staff(self):
        """Testa se a view de configuração requer usuário staff"""
        # Usuário não logado
        response = self.client.get(reverse('config:config'))
        self.assertEqual(response.status_code, 302)  # Redirect para login

        # Usuário regular
        self.client.login(username='user', password='testpass123')
        response = self.client.get(reverse('config:config'))
        self.assertEqual(response.status_code, 302)  # Redirect para login

        # Usuário admin
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('config:config'))
        self.assertEqual(response.status_code, 200)

    def test_database_config_list(self):
        """Testa a listagem de configurações de banco"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('config:database-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Configurações de Banco de Dados')

    def test_ldap_config_list(self):
        """Testa a listagem de configurações LDAP"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('config:ldap-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Configurações LDAP')


class DatabaseConfigModelTestCase(TestCase):
    """Testes para o modelo DatabaseConfig"""

    def test_create_database_config(self):
        """Testa criação de configuração de banco"""
        config = DatabaseConfig.objects.create(
            name='Test DB',
            engine='django.db.backends.sqlite3',
            database_name='test.db',
            is_active=True
        )
        self.assertEqual(config.name, 'Test DB')
        self.assertTrue(config.is_active)

    def test_password_encryption(self):
        """Testa criptografia de senha"""
        config = DatabaseConfig.objects.create(
            name='Test DB',
            engine='django.db.backends.postgresql',
            database_name='testdb',
            user='testuser',
            password='testpass'
        )
        config.set_password('testpass')
        config.save()

        # Senha deve estar criptografada
        self.assertNotEqual(config.password, 'testpass')
        # Mas deve ser recuperável
        self.assertEqual(config.get_password(), 'testpass')


class LDAPConfigModelTestCase(TestCase):
    """Testes para o modelo LDAPConfig"""

    def test_create_ldap_config(self):
        """Testa criação de configuração LDAP"""
        config = LDAPConfig.objects.create(
            server='ldap.test.com',
            port=389,
            base_dn='dc=test,dc=com',
            is_active=True
        )
        self.assertEqual(config.server, 'ldap.test.com')
        self.assertEqual(config.port, 389)
        self.assertTrue(config.is_active)


class EnvironmentVariableModelTestCase(TestCase):
    """Testes para o modelo EnvironmentVariable"""

    def test_create_environment_variable(self):
        """Testa criação de variável de ambiente"""
        var = EnvironmentVariable.objects.create(
            key='TEST_VAR',
            value='test_value',
            category='custom',
            description='Variável de teste',
            is_active=True
        )
        self.assertEqual(var.key, 'TEST_VAR')
        self.assertEqual(var.value, 'test_value')
        self.assertTrue(var.is_active)

    def test_sensitive_variable_display(self):
        """Testa exibição de variável sensível"""
        var = EnvironmentVariable.objects.create(
            key='SECRET_KEY',
            value='super-secret-key',
            is_sensitive=True,
            is_active=True
        )
        # Valor sensível deve ser mascarado na exibição
        display_value = var.get_display_value()
        self.assertNotEqual(display_value, 'super-secret-key')
        self.assertIn('*', display_value)
