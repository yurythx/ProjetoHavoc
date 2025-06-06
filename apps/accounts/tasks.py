#!/usr/bin/env python
"""
Tarefas assíncronas do Celery para o app accounts

Este arquivo contém todas as tarefas que serão executadas em background,
principalmente relacionadas ao envio de emails.

Como funciona:
1. Função é decorada com @shared_task
2. Web app chama task.delay() para enviar para fila
3. Worker Celery executa a tarefa em background
4. Resultado pode ser verificado via task_id
"""
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.config.models import EmailConfig
import logging
import time

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_activation_email_async(self, user_id, activation_code):
    """
    Envia email de ativação de forma assíncrona

    Args:
        self: Instância da tarefa (bind=True)
        user_id: ID do usuário
        activation_code: Código de ativação

    Returns:
        dict: Resultado da operação
    """
    try:
        # Buscar usuário
        user = User.objects.get(id=user_id)

        logger.info(f"Iniciando envio de email de ativação para {user.email}")

        # Usar sistema de email existente
        try:
            from apps.config.email_utils import send_email_with_config
            use_custom_email = True
        except ImportError:
            logger.warning("Sistema de email personalizado não encontrado, usando Django padrão")
            use_custom_email = False

        # Preparar contexto do template
        context = {
            'user': user,
            'activation_code': activation_code,
            'site_domain': settings.SITE_DOMAIN,
        }

        # Preparar email
        subject = "Código de Ativação da Conta"

        # Renderizar template HTML
        html_message = render_to_string('accounts/emails/activation_email.html', context)
        plain_message = strip_tags(html_message)

        # Enviar email usando sistema existente ou Django padrão
        if use_custom_email:
            result = send_email_with_config(
                subject=subject,
                message=plain_message,
                recipient_list=[user.email],
                html_message=html_message
            )
        else:
            result = send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

        if result:
            logger.info(f"Email de ativação enviado com sucesso para {user.email}")
            return {
                'success': True,
                'message': f'Email enviado para {user.email}',
                'user_id': user_id,
                'email': user.email,
                'task_id': self.request.id
            }
        else:
            raise Exception("send_mail retornou False")

    except User.DoesNotExist:
        error_msg = f"Usuário com ID {user_id} não encontrado"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'user_id': user_id,
            'task_id': self.request.id
        }

    except Exception as e:
        error_msg = f"Erro ao enviar email de ativação: {str(e)}"
        logger.error(error_msg)

        # Retry automático em caso de erro
        if self.request.retries < self.max_retries:
            logger.info(f"Tentativa {self.request.retries + 1}/{self.max_retries + 1}")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        return {
            'success': False,
            'error': error_msg,
            'user_id': user_id,
            'retries': self.request.retries,
            'task_id': self.request.id
        }

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email_async(self, user_id, reset_token):
    """
    Envia email de recuperação de senha de forma assíncrona

    Args:
        self: Instância da tarefa
        user_id: ID do usuário
        reset_token: Token de recuperação

    Returns:
        dict: Resultado da operação
    """
    try:
        user = User.objects.get(id=user_id)

        logger.info(f"Iniciando envio de email de recuperação para {user.email}")

        # Usar sistema de email existente
        try:
            from apps.config.email_utils import send_email_with_config
            use_custom_email = True
        except ImportError:
            logger.warning("Sistema de email personalizado não encontrado, usando Django padrão")
            use_custom_email = False

        context = {
            'user': user,
            'reset_token': reset_token,
            'site_domain': settings.SITE_DOMAIN,
        }

        subject = "Recuperação de Senha"
        html_message = render_to_string('accounts/emails/password_reset_email.html', context)
        plain_message = strip_tags(html_message)

        # Enviar email usando sistema existente ou Django padrão
        if use_custom_email:
            result = send_email_with_config(
                subject=subject,
                message=plain_message,
                recipient_list=[user.email],
                html_message=html_message
            )
        else:
            result = send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

        if result:
            logger.info(f"Email de recuperação enviado com sucesso para {user.email}")
            return {
                'success': True,
                'message': f'Email de recuperação enviado para {user.email}',
                'user_id': user_id,
                'email': user.email,
                'task_id': self.request.id
            }
        else:
            raise Exception("send_mail retornou False")

    except User.DoesNotExist:
        error_msg = f"Usuário com ID {user_id} não encontrado"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'user_id': user_id,
            'task_id': self.request.id
        }

    except Exception as e:
        error_msg = f"Erro ao enviar email de recuperação: {str(e)}"
        logger.error(error_msg)

        if self.request.retries < self.max_retries:
            logger.info(f"Tentativa {self.request.retries + 1}/{self.max_retries + 1}")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        return {
            'success': False,
            'error': error_msg,
            'user_id': user_id,
            'retries': self.request.retries,
            'task_id': self.request.id
        }

@shared_task
def send_bulk_email_async(subject, message, recipient_list, html_message=None):
    """
    Envia emails em massa de forma assíncrona

    Args:
        subject: Assunto do email
        message: Mensagem em texto plano
        recipient_list: Lista de emails destinatários
        html_message: Mensagem HTML (opcional)

    Returns:
        dict: Resultado da operação
    """
    try:
        logger.info(f"Iniciando envio em massa para {len(recipient_list)} destinatários")

        # Usar sistema de email existente
        try:
            from apps.config.email_utils import send_email_with_config
            use_custom_email = True
        except ImportError:
            logger.warning("Sistema de email personalizado não encontrado, usando Django padrão")
            use_custom_email = False

        # Enviar email usando sistema existente ou Django padrão
        if use_custom_email:
            result = send_email_with_config(
                subject=subject,
                message=message,
                recipient_list=recipient_list,
                html_message=html_message
            )
        else:
            result = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
            )

        logger.info(f"Email em massa enviado com sucesso para {len(recipient_list)} destinatários")
        return {
            'success': True,
            'message': f'Email enviado para {len(recipient_list)} destinatários',
            'recipient_count': len(recipient_list),
            'subject': subject
        }

    except Exception as e:
        error_msg = f"Erro ao enviar email em massa: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'recipient_count': len(recipient_list),
            'subject': subject
        }

@shared_task
def cleanup_expired_users():
    """
    Remove usuários não ativados há mais de 7 dias

    Returns:
        dict: Resultado da limpeza
    """
    try:
        from django.utils import timezone
        from datetime import timedelta

        # Usuários não ativados há mais de 7 dias
        cutoff_date = timezone.now() - timedelta(days=7)
        expired_users = User.objects.filter(
            is_active=False,
            date_joined__lt=cutoff_date
        )

        count = expired_users.count()
        expired_users.delete()

        logger.info(f"Limpeza concluída: {count} usuários expirados removidos")
        return {
            'success': True,
            'message': f'{count} usuários expirados removidos',
            'count': count
        }

    except Exception as e:
        error_msg = f"Erro na limpeza de usuários: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }

def send_activation_email_sync(user, activation_code):
    """
    Envia email de ativação de forma síncrona (para validação antes de salvar usuário)

    Args:
        user: Instância do usuário (ainda não salvo no banco)
        activation_code: Código de ativação

    Returns:
        dict: Resultado da operação
    """
    try:
        logger.info(f"Iniciando envio de email de ativação para {user.email}")

        # Usar sistema de email existente
        try:
            from apps.config.email_utils import send_email_with_config
            use_custom_email = True
        except ImportError:
            logger.warning("Sistema de email personalizado não encontrado, usando Django padrão")
            use_custom_email = False

        # Preparar contexto do template
        context = {
            'user': user,
            'activation_code': activation_code,
            'site_domain': settings.SITE_DOMAIN,
        }

        # Preparar email
        subject = "Código de Ativação da Conta"

        # Renderizar template HTML
        html_message = render_to_string('accounts/emails/activation_email.html', context)
        plain_message = strip_tags(html_message)

        # Enviar email usando sistema existente ou Django padrão
        if use_custom_email:
            result = send_email_with_config(
                subject=subject,
                message=plain_message,
                recipient_list=[user.email],
                html_message=html_message
            )
        else:
            result = send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

        if result:
            logger.info(f"Email de ativação enviado com sucesso para {user.email}")
            return {
                'success': True,
                'message': f'Email enviado para {user.email}',
                'email': user.email
            }
        else:
            raise Exception("send_mail retornou False")

    except Exception as e:
        error_msg = f"Erro ao enviar email de ativação: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'email': user.email
        }

@shared_task
def test_celery_task():
    """
    Tarefa de teste para verificar se o Celery está funcionando

    Returns:
        dict: Resultado do teste
    """
    logger.info("Executando tarefa de teste do Celery")

    # Simular algum processamento
    time.sleep(2)

    return {
        'success': True,
        'message': 'Celery está funcionando perfeitamente!',
        'timestamp': time.time()
    }
