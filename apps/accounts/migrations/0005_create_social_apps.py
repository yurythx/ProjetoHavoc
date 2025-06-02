from django.db import migrations
from django.conf import settings
from django.contrib.sites.models import Site

def create_social_apps(apps, schema_editor):
    SocialApp = apps.get_model('socialaccount', 'SocialApp')
    Site = apps.get_model('sites', 'Site')

    # Get or create the default site
    site, _ = Site.objects.get_or_create(
        id=settings.SITE_ID if hasattr(settings, 'SITE_ID') else 1,
        defaults={'domain': 'example.com', 'name': 'example.com'}
    )

    # Create Google provider
    google_provider = SocialApp.objects.create(
        provider='google',
        name='Google',
        client_id='your-google-client-id',
        secret='your-google-secret',
    )
    google_provider.sites.add(site)

    # Create GitHub provider
    github_provider = SocialApp.objects.create(
        provider='github',
        name='GitHub',
        client_id='your-github-client-id',
        secret='your-github-secret',
    )
    github_provider.sites.add(site)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_socialauthsettings'),
        ('sites', '0002_alter_domain_unique'),
        ('socialaccount', '0003_extra_data_default_dict'),
    ]

    operations = [
        migrations.RunPython(create_social_apps),
    ]