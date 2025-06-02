# apps/accounts/signals.py

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .models import CustomUser

# Signal desabilitado - agora usamos sistema de códigos
# @receiver(post_save, sender=CustomUser)
# def send_activation_email(sender, instance, created, **kwargs):
#     if created and not instance.is_active:
#         token = default_token_generator.make_token(instance)
#         uid = urlsafe_base64_encode(force_bytes(instance.pk))

#         activation_link = f"{settings.SITE_DOMAIN}/accounts/activate/{uid}/{token}/"

#         subject = "Ative sua conta"
#         message = render_to_string("accounts/emails/activation_email.html", {
#             'user': instance,
#             'activation_link': activation_link
#         })

#         send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email])