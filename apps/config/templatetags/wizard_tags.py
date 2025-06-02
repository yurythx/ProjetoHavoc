"""
Template tags para o Setup Wizard
"""
from django import template

register = template.Library()


@register.simple_tag
def wizard_step_status(wizard, step_code):
    """Retorna o status de uma etapa específica do wizard"""
    try:
        return wizard.get_step_status(step_code)
    except:
        return 'unknown'


@register.simple_tag
def wizard_is_step_completed(wizard, step_code):
    """Verifica se uma etapa foi concluída"""
    try:
        return wizard.is_step_completed(step_code)
    except:
        return False


@register.simple_tag
def wizard_is_step_skipped(wizard, step_code):
    """Verifica se uma etapa foi ignorada"""
    try:
        return wizard.is_step_skipped(step_code)
    except:
        return False


@register.filter
def get_step_icon(step_status):
    """Retorna o ícone apropriado para o status da etapa"""
    icons = {
        'completed': 'fas fa-check',
        'skipped': 'fas fa-forward',
        'current': 'fas fa-play',
        'pending': 'fas fa-circle',
        'available': 'fas fa-circle-o',
    }
    return icons.get(step_status, 'fas fa-circle')


@register.filter
def get_step_class(step_status):
    """Retorna a classe CSS apropriada para o status da etapa"""
    classes = {
        'completed': 'completed',
        'skipped': 'skipped',
        'current': 'current',
        'pending': 'pending',
        'available': 'available',
    }
    return classes.get(step_status, 'pending')


@register.inclusion_tag('config/wizard/step_indicator.html')
def wizard_step_indicator(wizard, all_steps, current_step):
    """Renderiza o indicador de progresso das etapas"""
    steps_data = []
    
    for step_code, step_name in all_steps:
        if step_code != 'completed':
            status = wizard.get_step_status(step_code)
            steps_data.append({
                'code': step_code,
                'name': step_name,
                'status': status,
                'is_current': step_code == current_step,
                'icon': get_step_icon(status),
                'css_class': get_step_class(status)
            })
    
    return {
        'steps': steps_data,
        'wizard': wizard,
        'current_step': current_step
    }
