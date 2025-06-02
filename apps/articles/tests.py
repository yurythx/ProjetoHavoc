from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class ArticleAppTestCase(TestCase):
    """Testes básicos para o app Articles"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )

    def test_articles_home_view(self):
        """Testa a view home do app articles"""
        response = self.client.get(reverse('articles:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Articles')

    def test_articles_home_view_authenticated(self):
        """Testa a view home com usuário autenticado"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('articles:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Articles')
