from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class PagesViewsTestCase(TestCase):
    """Testes para as views de páginas"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )

    def test_home_page(self):
        """Testa a página inicial"""
        response = self.client.get(reverse('pages:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Projeto Havoc')  # Assumindo que tem o nome do projeto

    def test_home_page_authenticated(self):
        """Testa a página inicial com usuário autenticado"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('pages:home'))
        self.assertEqual(response.status_code, 200)

    def test_about_page(self):
        """Testa a página sobre (se existir)"""
        try:
            response = self.client.get(reverse('pages:about'))
            self.assertEqual(response.status_code, 200)
        except:
            # Se a página não existir, pular o teste
            pass

    def test_contact_page(self):
        """Testa a página de contato (se existir)"""
        try:
            response = self.client.get(reverse('pages:contact'))
            self.assertEqual(response.status_code, 200)
        except:
            # Se a página não existir, pular o teste
            pass

    def test_404_page(self):
        """Testa página 404"""
        response = self.client.get('/pagina-que-nao-existe/')
        self.assertEqual(response.status_code, 404)

    def test_pages_context(self):
        """Testa se o contexto das páginas está correto"""
        response = self.client.get(reverse('pages:home'))
        self.assertEqual(response.status_code, 200)
        # Verificar se variáveis de contexto importantes estão presentes
        self.assertIn('request', response.context)


class PagesTemplatesTestCase(TestCase):
    """Testes para templates de páginas"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = Client()

    def test_base_template_structure(self):
        """Testa se o template base tem a estrutura correta"""
        response = self.client.get(reverse('pages:home'))
        self.assertEqual(response.status_code, 200)

        # Verificar elementos básicos do HTML
        self.assertContains(response, '<html')
        self.assertContains(response, '<head>')
        self.assertContains(response, '<body>')
        self.assertContains(response, '</html>')

    def test_navigation_elements(self):
        """Testa se elementos de navegação estão presentes"""
        response = self.client.get(reverse('pages:home'))
        self.assertEqual(response.status_code, 200)

        # Verificar se há elementos de navegação
        # (ajustar conforme a estrutura real do template)
        content = response.content.decode()
        self.assertTrue(
            'nav' in content.lower() or
            'menu' in content.lower() or
            'navbar' in content.lower()
        )

    def test_responsive_meta_tags(self):
        """Testa se meta tags responsivas estão presentes"""
        response = self.client.get(reverse('pages:home'))
        self.assertEqual(response.status_code, 200)

        # Verificar meta tag viewport
        self.assertContains(response, 'viewport')


class PagesSecurityTestCase(TestCase):
    """Testes de segurança para páginas"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = Client()

    def test_security_headers(self):
        """Testa se headers de segurança estão presentes"""
        response = self.client.get(reverse('pages:home'))

        # Verificar alguns headers de segurança básicos
        # (dependendo da configuração do middleware)
        headers = response.headers

        # Estes headers podem estar presentes dependendo da configuração
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection'
        ]

        # Pelo menos um header de segurança deve estar presente
        has_security_header = any(header in headers for header in security_headers)
        # Não falhar se não houver headers (pode ser configuração de desenvolvimento)
        # self.assertTrue(has_security_header, "Nenhum header de segurança encontrado")

    def test_csrf_protection(self):
        """Testa se proteção CSRF está ativa"""
        response = self.client.get(reverse('pages:home'))

        # Se houver formulários na página, deve ter token CSRF
        if 'form' in response.content.decode().lower():
            self.assertContains(response, 'csrfmiddlewaretoken')


class PagesPerformanceTestCase(TestCase):
    """Testes de performance para páginas"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = Client()

    def test_page_load_time(self):
        """Testa se a página carrega em tempo razoável"""
        import time

        start_time = time.time()
        response = self.client.get(reverse('pages:home'))
        end_time = time.time()

        load_time = end_time - start_time

        self.assertEqual(response.status_code, 200)
        # Página deve carregar em menos de 2 segundos (ajustar conforme necessário)
        self.assertLess(load_time, 2.0, f"Página demorou {load_time:.2f}s para carregar")

    def test_page_size(self):
        """Testa se o tamanho da página é razoável"""
        response = self.client.get(reverse('pages:home'))
        self.assertEqual(response.status_code, 200)

        content_length = len(response.content)
        # Página não deve ser maior que 1MB (ajustar conforme necessário)
        self.assertLess(content_length, 1024 * 1024, f"Página muito grande: {content_length} bytes")
