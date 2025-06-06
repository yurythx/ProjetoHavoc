from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('apps.pages.urls', 'pages'), namespace='pages')),

    path('accounts/', include(('apps.accounts.urls', 'accounts'), namespace='accounts')),
    path('accounts/', include('allauth.urls')),

    path('articles/', include(('apps.articles.urls', 'articles'), namespace='articles')),
    path('config/', include(('apps.config.urls', 'config'), namespace='config')),
]

if settings.DEBUG:
    # Servir arquivos estáticos em desenvolvimento
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Servir arquivos de mídia em desenvolvimento
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug Toolbar URLs
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass