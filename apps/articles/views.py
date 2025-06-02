# apps/articles/views.py
from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'articles/home.html'