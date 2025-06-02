# apps/articles/urls.py
from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
]