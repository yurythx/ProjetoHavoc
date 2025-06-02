from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
# from django_auth_ldap.backend import LDAPBackend  # Comentado - módulo não instalado
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.db import models
from django.utils import timezone
from allauth.socialaccount.models import SocialAccount
from .tokens import email_confirmation_token

User = get_user_model()

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Tenta autenticar com email ou username
            user = User.objects.get(
                models.Q(username__iexact=username) |
                models.Q(email__iexact=username)
            )
            if user.check_password(password):
                if not user.is_active:
                    self.send_confirmation_email(user)
                    return None
                return user
        except User.DoesNotExist:
            return None

    def send_confirmation_email(self, user):
        token = email_confirmation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        confirmation_link = f"{settings.SITE_DOMAIN}/accounts/confirm-email/{uid}/{token}/"

        context = {
            'user': user,
            'confirmation_link': confirmation_link,
        }

        message = render_to_string('registration/email_confirmation_email.html', context)

        send_mail(
            'Confirme seu email',
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

# class CustomLDAPBackend(LDAPBackend):  # Comentado - módulo django_auth_ldap não instalado
#     def get_or_create_user(self, username, ldap_user):
#         user, created = User.objects.get_or_create(username=username)
#
#         if created:
#             user.email = ldap_user.attrs.get('mail', [None])[0]
#             user.first_name = ldap_user.attrs.get('givenName', [None])[0]
#             user.last_name = ldap_user.attrs.get('sn', [None])[0]
#             user.is_active = True
#             user.email_verificado = True
#             user.provedor_social = 'ldap'
#             user.ultimo_login_social = timezone.now()
#             user.save()
#
#         return user, created