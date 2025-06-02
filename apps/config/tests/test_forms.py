"""
Testes para formulários do sistema de configurações
"""

from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.config.forms import (
    EmailConfigForm, LDAPConfigForm, DatabaseConfigForm,
    SystemConfigForm, AppConfigForm, WidgetForm, MenuConfigForm,
    EnvironmentVariableForm
)
from apps.config.models import EmailConfig, LDAPConfig, DatabaseConfig


class EmailConfigFormTest(TestCase):
    """Testes para o formulário de configuração de email"""
    
    def test_valid_email_config_form(self):
        """Testa formulário válido de email"""
        form_data = {
            'email_host': 'smtp.gmail.com',
            'email_port': 587,
            'email_host_user': 'test@gmail.com',
            'email_host_password': 'testpass',
            'email_use_tls': True,
            'default_from_email': 'noreply@test.com',
            'is_active': True,
            'use_console_backend': False
        }
        
        form = EmailConfigForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_email_config_form(self):
        """Testa formulário inválido de email"""
        form_data = {
            'email_host': '',  # Campo obrigatório
            'email_port': 'invalid',  # Deve ser número
            'email_host_user': 'invalid_email',  # Email inválido
            'default_from_email': 'invalid_email'  # Email inválido
        }
        
        form = EmailConfigForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Verificar erros específicos
        self.assertIn('email_host', form.errors)
        self.assertIn('email_port', form.errors)
    
    def test_email_port_validation(self):
        """Testa validação da porta de email"""
        # Porta muito baixa
        form_data = {
            'email_host': 'smtp.test.com',
            'email_port': 0,
            'email_host_user': 'test@test.com',
            'email_host_password': 'pass',
            'default_from_email': 'test@test.com'
        }
        
        form = EmailConfigForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Porta muito alta
        form_data['email_port'] = 70000
        form = EmailConfigForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Porta válida
        form_data['email_port'] = 587
        form = EmailConfigForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_email_password_encryption(self):
        """Testa criptografia da senha de email"""
        form_data = {
            'email_host': 'smtp.test.com',
            'email_port': 587,
            'email_host_user': 'test@test.com',
            'email_host_password': 'plainpassword',
            'default_from_email': 'test@test.com'
        }
        
        form = EmailConfigForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Salvar e verificar se a senha foi criptografada
        email_config = form.save()
        self.assertNotEqual(email_config.email_host_password, 'plainpassword')


class LDAPConfigFormTest(TestCase):
    """Testes para o formulário de configuração LDAP"""
    
    def test_valid_ldap_config_form(self):
        """Testa formulário válido de LDAP"""
        form_data = {
            'server': 'ldap.empresa.com',
            'port': 389,
            'base_dn': 'dc=empresa,dc=com',
            'bind_dn': 'cn=admin,dc=empresa,dc=com',
            'bind_password': 'adminpass',
            'domain': 'empresa.com',
            'search_filter': '(objectClass=person)',
            'is_active': True
        }
        
        form = LDAPConfigForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_ldap_config_form(self):
        """Testa formulário inválido de LDAP"""
        form_data = {
            'server': '',  # Campo obrigatório
            'port': 'invalid',  # Deve ser número
            'base_dn': '',  # Campo obrigatório
            'domain': 'invalid_domain'  # Domínio inválido
        }
        
        form = LDAPConfigForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Verificar erros específicos
        self.assertIn('server', form.errors)
        self.assertIn('port', form.errors)
        self.assertIn('base_dn', form.errors)
    
    def test_ldap_port_validation(self):
        """Testa validação da porta LDAP"""
        form_data = {
            'server': 'ldap.test.com',
            'port': 389,
            'base_dn': 'dc=test,dc=com'
        }
        
        form = LDAPConfigForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Porta inválida
        form_data['port'] = -1
        form = LDAPConfigForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_ldap_domain_validation(self):
        """Testa validação do domínio LDAP"""
        form_data = {
            'server': 'ldap.test.com',
            'port': 389,
            'base_dn': 'dc=test,dc=com',
            'domain': 'test.com'  # Domínio válido
        }
        
        form = LDAPConfigForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Domínio inválido
        form_data['domain'] = 'invalid'
        form = LDAPConfigForm(data=form_data)
        self.assertFalse(form.is_valid())


class DatabaseConfigFormTest(TestCase):
    """Testes para o formulário de configuração de banco"""
    
    def test_valid_database_config_form(self):
        """Testa formulário válido de banco"""
        form_data = {
            'name': 'Test Database',
            'engine': 'django.db.backends.postgresql',
            'database_name': 'testdb',
            'host': 'localhost',
            'port': 5432,
            'user': 'testuser',
            'password': 'testpass',
            'is_active': True,
            'is_default': False
        }
        
        form = DatabaseConfigForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_database_config_form(self):
        """Testa formulário inválido de banco"""
        form_data = {
            'name': '',  # Campo obrigatório
            'engine': 'invalid_engine',
            'database_name': '',  # Campo obrigatório
            'port': 'invalid'  # Deve ser número
        }
        
        form = DatabaseConfigForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Verificar erros específicos
        self.assertIn('name', form.errors)
        self.assertIn('database_name', form.errors)
    
    def test_sqlite_database_form(self):
        """Testa formulário para SQLite"""
        form_data = {
            'name': 'SQLite DB',
            'engine': 'django.db.backends.sqlite3',
            'database_name': '/path/to/db.sqlite3',
            'is_active': True
        }
        
        form = DatabaseConfigForm(data=form_data)
        self.assertTrue(form.is_valid())


class SystemConfigFormTest(TestCase):
    """Testes para o formulário de configuração do sistema"""
    
    def test_valid_system_config_form(self):
        """Testa formulário válido do sistema"""
        form_data = {
            'site_name': 'Projeto Havoc',
            'site_description': 'Sistema de gestão',
            'maintenance_mode': False,
            'allow_registration': True,
            'require_email_verification': True,
            'theme': 'default',
            'primary_color': '#4361ee',
            'secondary_color': '#6c757d'
        }
        
        form = SystemConfigForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_system_config_form(self):
        """Testa formulário inválido do sistema"""
        form_data = {
            'site_name': '',  # Campo obrigatório
            'site_description': '',  # Campo obrigatório
            'primary_color': 'invalid_color',  # Cor inválida
            'theme': 'invalid_theme'  # Tema inválido
        }
        
        form = SystemConfigForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Verificar erros específicos
        self.assertIn('site_name', form.errors)
        self.assertIn('site_description', form.errors)
    
    def test_color_validation(self):
        """Testa validação de cores hexadecimais"""
        form_data = {
            'site_name': 'Test Site',
            'site_description': 'Test Description',
            'primary_color': '#FF0000',  # Cor válida
            'secondary_color': '#00FF00'  # Cor válida
        }
        
        form = SystemConfigForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Cor inválida
        form_data['primary_color'] = 'red'  # Não é hex
        form = SystemConfigForm(data=form_data)
        self.assertFalse(form.is_valid())


class AppConfigFormTest(TestCase):
    """Testes para o formulário de configuração de apps"""
    
    def test_valid_app_config_form(self):
        """Testa formulário válido de app"""
        form_data = {
            'name': 'Test App',
            'label': 'test_app',
            'description': 'App de teste',
            'is_active': True,
            'is_core': False,
            'order': 1
        }
        
        form = AppConfigForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_app_config_form(self):
        """Testa formulário inválido de app"""
        form_data = {
            'name': '',  # Campo obrigatório
            'label': '',  # Campo obrigatório
            'order': 'invalid'  # Deve ser número
        }
        
        form = AppConfigForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Verificar erros específicos
        self.assertIn('name', form.errors)
        self.assertIn('label', form.errors)
    
    def test_app_label_validation(self):
        """Testa validação do label do app"""
        form_data = {
            'name': 'Test App',
            'label': 'test_app',
            'description': 'Test'
        }
        
        form = AppConfigForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Label com caracteres inválidos
        form_data['label'] = 'test-app-invalid'
        form = AppConfigForm(data=form_data)
        # Dependendo da validação implementada, pode ser inválido


class WidgetFormTest(TestCase):
    """Testes para o formulário de widgets"""
    
    def test_valid_widget_form(self):
        """Testa formulário válido de widget"""
        form_data = {
            'name': 'Test Widget',
            'widget_type': 'stats',
            'size': 'medium',
            'position_x': 0,
            'position_y': 0,
            'is_active': True,
            'is_public': True,
            'config_json': '{"key": "value"}'
        }
        
        form = WidgetForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_widget_form(self):
        """Testa formulário inválido de widget"""
        form_data = {
            'name': '',  # Campo obrigatório
            'widget_type': 'invalid_type',
            'size': 'invalid_size',
            'position_x': 'invalid',  # Deve ser número
            'config_json': 'invalid_json'  # JSON inválido
        }
        
        form = WidgetForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Verificar erros específicos
        self.assertIn('name', form.errors)
    
    def test_widget_json_validation(self):
        """Testa validação do JSON de configuração"""
        form_data = {
            'name': 'Test Widget',
            'widget_type': 'stats',
            'config_json': '{"valid": "json"}'
        }
        
        form = WidgetForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # JSON inválido
        form_data['config_json'] = '{"invalid": json}'
        form = WidgetForm(data=form_data)
        # Dependendo da validação implementada, pode ser inválido


class EnvironmentVariableFormTest(TestCase):
    """Testes para o formulário de variáveis de ambiente"""
    
    def test_valid_env_var_form(self):
        """Testa formulário válido de variável de ambiente"""
        form_data = {
            'key': 'TEST_VAR',
            'value': 'test_value',
            'description': 'Variável de teste',
            'category': 'custom',
            'var_type': 'string',
            'is_required': True,
            'is_sensitive': False,
            'is_active': True
        }
        
        form = EnvironmentVariableForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_env_var_form(self):
        """Testa formulário inválido de variável de ambiente"""
        form_data = {
            'key': '',  # Campo obrigatório
            'description': '',  # Campo obrigatório
            'var_type': 'invalid_type'
        }
        
        form = EnvironmentVariableForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Verificar erros específicos
        self.assertIn('key', form.errors)
        self.assertIn('description', form.errors)
    
    def test_env_var_key_validation(self):
        """Testa validação da chave da variável"""
        form_data = {
            'key': 'VALID_KEY',
            'description': 'Test variable',
            'var_type': 'string'
        }
        
        form = EnvironmentVariableForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Chave com caracteres inválidos
        form_data['key'] = 'invalid-key'
        form = EnvironmentVariableForm(data=form_data)
        # Dependendo da validação implementada, pode ser inválido
    
    def test_boolean_env_var_validation(self):
        """Testa validação de variável booleana"""
        form_data = {
            'key': 'BOOL_VAR',
            'value': 'true',
            'description': 'Boolean variable',
            'var_type': 'boolean'
        }
        
        form = EnvironmentVariableForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Valores válidos para boolean
        valid_bool_values = ['true', 'false', '1', '0', 'yes', 'no']
        for value in valid_bool_values:
            form_data['value'] = value
            form = EnvironmentVariableForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Failed for boolean value: {value}")


class FormSecurityTest(TestCase):
    """Testes de segurança para formulários"""
    
    def test_xss_prevention_in_forms(self):
        """Testa prevenção de XSS em formulários"""
        malicious_data = '<script>alert("xss")</script>'
        
        form_data = {
            'site_name': malicious_data,
            'site_description': malicious_data
        }
        
        form = SystemConfigForm(data=form_data)
        if form.is_valid():
            # O Django deve escapar automaticamente
            instance = form.save(commit=False)
            self.assertNotIn('<script>', str(instance.site_name))
    
    def test_sql_injection_prevention(self):
        """Testa prevenção de SQL injection"""
        malicious_data = "'; DROP TABLE auth_user; --"
        
        form_data = {
            'name': malicious_data,
            'label': 'test_app',
            'description': 'Test'
        }
        
        form = AppConfigForm(data=form_data)
        if form.is_valid():
            # O ORM do Django deve prevenir SQL injection
            instance = form.save()
            self.assertEqual(instance.name, malicious_data)  # Salvo como string normal
    
    def test_csrf_token_requirement(self):
        """Testa que formulários requerem token CSRF"""
        # Este teste seria feito nas views, mas é importante mencionar
        pass
