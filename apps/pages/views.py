# apps/pages/views.py
from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse

class HomeView(TemplateView):
    template_name = 'pages/home.html'

class SobreView(TemplateView):
    template_name = 'pages/sobre.html'

class ContatoView(TemplateView):
    template_name = 'pages/contato.html'

    def post(self, request, *args, **kwargs):
        """Processa o formulário de contato"""
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        empresa = request.POST.get('empresa')
        assunto = request.POST.get('assunto')
        mensagem = request.POST.get('mensagem')
        newsletter = request.POST.get('newsletter')

        # Aqui você pode implementar o envio de email, salvar no banco, etc.
        # Por enquanto, vamos apenas mostrar uma mensagem de sucesso

        if nome and email and assunto and mensagem:
            messages.success(
                request,
                f'Obrigado {nome}! Sua mensagem foi enviada com sucesso. '
                'Entraremos em contato em breve.'
            )

            # Log da mensagem (opcional)
            print(f"Nova mensagem de contato:")
            print(f"Nome: {nome}")
            print(f"Email: {email}")
            print(f"Telefone: {telefone}")
            print(f"Empresa: {empresa}")
            print(f"Assunto: {assunto}")
            print(f"Mensagem: {mensagem}")
            print(f"Newsletter: {'Sim' if newsletter else 'Não'}")

            return HttpResponseRedirect(reverse('pages:contato'))
        else:
            messages.error(
                request,
                'Por favor, preencha todos os campos obrigatórios.'
            )

        return self.get(request, *args, **kwargs)