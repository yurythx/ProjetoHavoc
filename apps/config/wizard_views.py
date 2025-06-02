"""
Views do Assistente de Configuração (Setup Wizard)
Projeto Havoc - Sistema de Configuração Guiada
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
import json
import logging

from .models import SetupWizard, WizardRecommendation, SystemConfig
from .environment_detector import environment_detector

logger = logging.getLogger(__name__)


def is_staff_user(user):
    """Verifica se o usuário é staff"""
    return user.is_authenticated and user.is_staff


class SetupWizardView(View):
    """View principal do assistente de configuração"""
    
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_staff_user))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, wizard_id=None, step=None):
        """Exibe uma etapa do wizard"""
        try:
            # Obter ou criar wizard
            if wizard_id:
                wizard = get_object_or_404(SetupWizard, wizard_id=wizard_id)
            else:
                # Verificar se já existe um wizard em progresso
                existing_wizard = SetupWizard.objects.filter(
                    started_by=request.user,
                    status__in=['not_started', 'in_progress']
                ).first()
                
                if existing_wizard:
                    wizard = existing_wizard
                else:
                    # Criar novo wizard
                    wizard = SetupWizard.objects.create(
                        started_by=request.user,
                        status='in_progress'
                    )
            
            # Definir etapa atual
            if step and step in [choice[0] for choice in SetupWizard.STEP_CHOICES]:
                wizard.current_step = step
                wizard.save(update_fields=['current_step', 'last_activity'])
            
            current_step = wizard.current_step
            
            # Preparar contexto baseado na etapa
            context = self._get_step_context(wizard, current_step)
            
            # Template baseado na etapa
            template_name = f'config/wizard/{current_step}.html'
            
            return render(request, template_name, context)
            
        except Exception as e:
            logger.error(f"Erro no wizard: {e}")
            messages.error(request, f"Erro no assistente de configuração: {str(e)}")
            return redirect('config:config')
    
    def post(self, request, wizard_id, step=None):
        """Processa dados de uma etapa do wizard"""
        try:
            wizard = get_object_or_404(SetupWizard, wizard_id=wizard_id)
            current_step = step or wizard.current_step
            
            # Processar dados baseado na etapa
            success = self._process_step_data(wizard, current_step, request.POST)
            
            if success:
                # Marcar etapa como concluída
                wizard.mark_step_completed(current_step)
                
                # Avançar para próxima etapa
                next_step = wizard.get_next_step()
                
                if next_step == 'completed':
                    wizard.advance_to_next_step()
                    messages.success(request, "Assistente de configuração concluído com sucesso!")
                    return redirect('config:wizard_summary', wizard_id=wizard.wizard_id)
                else:
                    wizard.advance_to_next_step()
                    return redirect('config:wizard_step', wizard_id=wizard.wizard_id, step=next_step)
            else:
                messages.error(request, "Erro ao processar dados da etapa.")
                return redirect('config:wizard_step', wizard_id=wizard.wizard_id, step=current_step)
                
        except Exception as e:
            logger.error(f"Erro ao processar etapa do wizard: {e}")
            messages.error(request, f"Erro ao processar etapa: {str(e)}")
            return redirect('config:wizard_step', wizard_id=wizard_id, step=current_step)
    
    def _get_step_context(self, wizard, step):
        """Prepara contexto específico para cada etapa"""
        base_context = {
            'wizard': wizard,
            'current_step': step,
            'step_info': self._get_step_info(step),
            'progress_percentage': wizard.get_progress_percentage(),
            'all_steps': SetupWizard.STEP_CHOICES,
        }
        
        if step == 'welcome':
            base_context.update({
                'system_config': SystemConfig.objects.first(),
                'is_first_setup': not SystemConfig.objects.exists(),
            })
            
        elif step == 'environment':
            # Executar detecção de ambiente
            env_data = environment_detector.detect_full_environment()
            wizard.save_environment_data(env_data)
            
            base_context.update({
                'environment_data': env_data,
                'recommendations': self._generate_environment_recommendations(wizard, env_data),
            })
            
        elif step == 'database':
            base_context.update({
                'current_db_config': settings.DATABASES.get('default', {}),
                'supported_engines': [
                    ('django.db.backends.sqlite3', 'SQLite'),
                    ('django.db.backends.postgresql', 'PostgreSQL'),
                    ('django.db.backends.mysql', 'MySQL'),
                ],
            })
            
        elif step == 'email':
            base_context.update({
                'current_email_config': {
                    'host': getattr(settings, 'EMAIL_HOST', ''),
                    'port': getattr(settings, 'EMAIL_PORT', 587),
                    'use_tls': getattr(settings, 'EMAIL_USE_TLS', True),
                },
            })
            
        elif step == 'security':
            base_context.update({
                'security_checks': self._get_security_checks(),
                'current_debug': settings.DEBUG,
            })
            
        elif step == 'optimization':
            base_context.update({
                'optimization_options': self._get_optimization_options(),
                'performance_data': wizard.environment_data.get('performance', {}),
            })
            
        elif step == 'finalization':
            base_context.update({
                'summary': wizard.generate_summary_report(),
                'recommendations': wizard.recommendations.filter(status='pending'),
            })
        
        return base_context
    
    def _get_step_info(self, step):
        """Retorna informações sobre a etapa"""
        step_info = {
            'welcome': {
                'title': 'Bem-vindo ao Assistente de Configuração',
                'description': 'Configure seu sistema Projeto Havoc de forma guiada',
                'icon': 'fas fa-magic',
            },
            'environment': {
                'title': 'Detecção de Ambiente',
                'description': 'Analisando seu ambiente de execução',
                'icon': 'fas fa-search',
            },
            'database': {
                'title': 'Configuração de Banco de Dados',
                'description': 'Configure a conexão com o banco de dados',
                'icon': 'fas fa-database',
            },
            'email': {
                'title': 'Configuração de Email',
                'description': 'Configure o sistema de envio de emails',
                'icon': 'fas fa-envelope',
            },
            'security': {
                'title': 'Configurações de Segurança',
                'description': 'Configure as opções de segurança do sistema',
                'icon': 'fas fa-shield-alt',
            },
            'optimization': {
                'title': 'Otimizações',
                'description': 'Aplique otimizações recomendadas',
                'icon': 'fas fa-rocket',
            },
            'finalization': {
                'title': 'Finalização',
                'description': 'Revise e aplique as configurações',
                'icon': 'fas fa-check-circle',
            },
        }
        return step_info.get(step, {})
    
    def _process_step_data(self, wizard, step, post_data):
        """Processa dados específicos de cada etapa"""
        try:
            if step == 'welcome':
                preferences = {
                    'auto_apply': post_data.get('auto_apply') == 'on',
                    'skip_optional': post_data.get('skip_optional') == 'on',
                    'create_backup': post_data.get('create_backup') == 'on',
                }
                wizard.save_user_preferences(preferences)
                
            elif step == 'environment':
                # Dados já salvos durante a detecção
                pass
                
            elif step == 'database':
                db_config = {
                    'engine': post_data.get('db_engine'),
                    'name': post_data.get('db_name'),
                    'host': post_data.get('db_host'),
                    'port': post_data.get('db_port'),
                    'user': post_data.get('db_user'),
                    'password': post_data.get('db_password'),
                    'apply': post_data.get('apply_db_config') == 'on',
                }
                wizard.save_configuration_choices({'database': db_config})
                
            elif step == 'email':
                email_config = {
                    'host': post_data.get('email_host'),
                    'port': post_data.get('email_port'),
                    'user': post_data.get('email_user'),
                    'password': post_data.get('email_password'),
                    'use_tls': post_data.get('email_use_tls') == 'on',
                    'apply': post_data.get('apply_email_config') == 'on',
                }
                wizard.save_configuration_choices({'email': email_config})
                
            elif step == 'security':
                security_config = {
                    'disable_debug': post_data.get('disable_debug') == 'on',
                    'enable_https': post_data.get('enable_https') == 'on',
                    'secure_cookies': post_data.get('secure_cookies') == 'on',
                    'apply': post_data.get('apply_security_config') == 'on',
                }
                wizard.save_configuration_choices({'security': security_config})
                
            elif step == 'optimization':
                opt_config = {
                    'enable_cache': post_data.get('enable_cache') == 'on',
                    'compress_static': post_data.get('compress_static') == 'on',
                    'optimize_db': post_data.get('optimize_db') == 'on',
                    'apply': post_data.get('apply_optimizations') == 'on',
                }
                wizard.save_optimization_settings({'optimization': opt_config})
                
            elif step == 'finalization':
                # Aplicar configurações se solicitado
                if post_data.get('apply_all_configs') == 'on':
                    success, message = wizard.apply_configurations()
                    if not success:
                        logger.error(f"Erro ao aplicar configurações: {message}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar dados da etapa {step}: {e}")
            return False
    
    def _generate_environment_recommendations(self, wizard, env_data):
        """Gera recomendações baseadas na detecção de ambiente"""
        recommendations = []
        
        try:
            # Recomendações de segurança
            if env_data.get('environment', {}).get('django', {}).get('debug'):
                rec = WizardRecommendation.objects.create(
                    wizard=wizard,
                    title="Desativar DEBUG em produção",
                    description="O modo DEBUG está ativo, o que pode expor informações sensíveis.",
                    category='security',
                    priority='critical',
                    technical_details={'setting': 'DEBUG', 'current_value': True, 'recommended_value': False},
                    auto_apply=True
                )
                recommendations.append(rec)
            
            # Recomendações de performance
            cache_info = env_data.get('environment', {}).get('cache', {})
            if not cache_info.get('recommended', False):
                rec = WizardRecommendation.objects.create(
                    wizard=wizard,
                    title="Configurar Redis para cache",
                    description="Sistema de cache atual não é otimizado para produção.",
                    category='performance',
                    priority='high',
                    technical_details={'current_backend': cache_info.get('backend'), 'recommended': 'Redis'},
                    auto_apply=False
                )
                recommendations.append(rec)
            
            # Recomendações de deployment
            web_server = env_data.get('environment', {}).get('web_server', {})
            if web_server.get('type') == 'development':
                rec = WizardRecommendation.objects.create(
                    wizard=wizard,
                    title="Configurar servidor web para produção",
                    description="Servidor de desenvolvimento não é adequado para produção.",
                    category='deployment',
                    priority='high',
                    technical_details={'current_server': web_server.get('server'), 'recommended': 'Gunicorn + Nginx'},
                    auto_apply=False
                )
                recommendations.append(rec)
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendações: {e}")
        
        return recommendations
    
    def _get_security_checks(self):
        """Retorna verificações de segurança"""
        return [
            {
                'name': 'DEBUG Mode',
                'current': settings.DEBUG,
                'recommended': False,
                'description': 'Modo debug deve estar desativado em produção'
            },
            {
                'name': 'SECRET_KEY',
                'current': not settings.SECRET_KEY.startswith('django-insecure-'),
                'recommended': True,
                'description': 'Chave secreta deve ser segura'
            },
            {
                'name': 'ALLOWED_HOSTS',
                'current': len(settings.ALLOWED_HOSTS) > 0,
                'recommended': True,
                'description': 'Hosts permitidos devem estar configurados'
            },
        ]
    
    def _get_optimization_options(self):
        """Retorna opções de otimização"""
        return [
            {
                'name': 'Cache Redis',
                'description': 'Configurar Redis para cache de alta performance',
                'impact': 'Alto',
                'difficulty': 'Médio'
            },
            {
                'name': 'Compressão de Arquivos Estáticos',
                'description': 'Comprimir CSS e JavaScript para carregamento mais rápido',
                'impact': 'Médio',
                'difficulty': 'Baixo'
            },
            {
                'name': 'Otimização de Banco de Dados',
                'description': 'Configurar índices e otimizações de queries',
                'impact': 'Alto',
                'difficulty': 'Alto'
            },
        ]


@login_required
@user_passes_test(is_staff_user)
def wizard_summary(request, wizard_id):
    """Exibe resumo do wizard concluído"""
    wizard = get_object_or_404(SetupWizard, wizard_id=wizard_id)
    
    context = {
        'wizard': wizard,
        'summary': wizard.generate_summary_report(),
        'recommendations': wizard.recommendations.all(),
        'applied_configs': wizard.configuration_choices,
    }
    
    return render(request, 'config/wizard/summary.html', context)


@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def skip_wizard_step(request, wizard_id, step):
    """Pula uma etapa do wizard"""
    try:
        wizard = get_object_or_404(SetupWizard, wizard_id=wizard_id)
        wizard.mark_step_skipped(step)
        
        next_step = wizard.get_next_step()
        if next_step == 'completed':
            wizard.advance_to_next_step()
            return JsonResponse({'success': True, 'redirect': f'/config/wizard/{wizard_id}/summary/'})
        else:
            wizard.advance_to_next_step()
            return JsonResponse({'success': True, 'redirect': f'/config/wizard/{wizard_id}/{next_step}/'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def apply_recommendation(request, wizard_id, recommendation_id):
    """Aplica uma recomendação específica"""
    try:
        wizard = get_object_or_404(SetupWizard, wizard_id=wizard_id)
        recommendation = get_object_or_404(WizardRecommendation, id=recommendation_id, wizard=wizard)
        
        success, message = recommendation.apply_recommendation(request.user)
        
        return JsonResponse({
            'success': success,
            'message': message,
            'status': recommendation.get_status_display()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(is_staff_user)
def wizard_api_status(request, wizard_id):
    """API para status do wizard"""
    try:
        wizard = get_object_or_404(SetupWizard, wizard_id=wizard_id)
        
        return JsonResponse({
            'wizard_id': str(wizard.wizard_id),
            'current_step': wizard.current_step,
            'status': wizard.status,
            'progress': wizard.progress_percentage,
            'steps_completed': wizard.steps_completed,
            'steps_skipped': wizard.steps_skipped,
            'recommendations_count': wizard.recommendations.count(),
            'pending_recommendations': wizard.recommendations.filter(status='pending').count(),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
