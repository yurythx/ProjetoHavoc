"""
Views avançadas para funcionalidades modulares do app config.
"""

from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
import json

from .models import Widget, MenuConfig, Plugin, ConfigBackup

def staff_required(view_func):
    """Decorator personalizado que verifica se o usuário é staff e redireciona para o login correto."""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())

        if not request.user.is_staff:
            raise PermissionDenied("Você precisa ser um usuário staff para acessar esta página.")

        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ==================== VIEWS DE WIDGETS ====================

@method_decorator(staff_required, name='dispatch')
class WidgetListView(ListView):
    model = Widget
    template_name = 'config/widgets/widget_list.html'
    context_object_name = 'widgets'
    paginate_by = 20

    def get_queryset(self):
        queryset = Widget.objects.all()

        # Filtros
        widget_type = self.request.GET.get('type')
        if widget_type:
            queryset = queryset.filter(widget_type=widget_type)

        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset.order_by('order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['widget_types'] = Widget.WIDGET_TYPES
        context['current_type'] = self.request.GET.get('type', '')
        context['current_status'] = self.request.GET.get('status', '')
        return context


@method_decorator(staff_required, name='dispatch')
class WidgetCreateView(CreateView):
    model = Widget
    template_name = 'config/widgets/widget_form.html'
    fields = ['name', 'description', 'widget_type', 'size', 'is_active', 'is_public',
              'required_permission', 'template_path', 'custom_css', 'custom_js']
    success_url = reverse_lazy('config:widget-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Adicionar classes CSS aos campos
        form.fields['name'].widget.attrs.update({'class': 'form-control'})
        form.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 3})
        form.fields['widget_type'].widget.attrs.update({'class': 'form-select'})
        form.fields['size'].widget.attrs.update({'class': 'form-select'})
        form.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['is_public'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['required_permission'].widget.attrs.update({'class': 'form-control'})
        form.fields['template_path'].widget.attrs.update({'class': 'form-control'})
        form.fields['custom_css'].widget.attrs.update({'class': 'form-control', 'rows': 5})
        form.fields['custom_js'].widget.attrs.update({'class': 'form-control', 'rows': 5})
        return form

    def form_valid(self, form):
        messages.success(self.request, f'Widget "{form.instance.name}" criado com sucesso!')
        return super().form_valid(form)


@method_decorator(staff_required, name='dispatch')
class WidgetUpdateView(UpdateView):
    model = Widget
    template_name = 'config/widgets/widget_form.html'
    fields = ['name', 'description', 'widget_type', 'size', 'position_x', 'position_y',
              'order', 'is_active', 'is_public', 'required_permission', 'config_json',
              'template_path', 'custom_css', 'custom_js']
    success_url = reverse_lazy('config:widget-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Adicionar classes CSS aos campos
        form.fields['name'].widget.attrs.update({'class': 'form-control'})
        form.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 3})
        form.fields['widget_type'].widget.attrs.update({'class': 'form-select'})
        form.fields['size'].widget.attrs.update({'class': 'form-select'})
        form.fields['position_x'].widget.attrs.update({'class': 'form-control', 'type': 'number'})
        form.fields['position_y'].widget.attrs.update({'class': 'form-control', 'type': 'number'})
        form.fields['order'].widget.attrs.update({'class': 'form-control', 'type': 'number'})
        form.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['is_public'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['required_permission'].widget.attrs.update({'class': 'form-control'})
        form.fields['config_json'].widget.attrs.update({'class': 'form-control', 'rows': 5})
        form.fields['template_path'].widget.attrs.update({'class': 'form-control'})
        form.fields['custom_css'].widget.attrs.update({'class': 'form-control', 'rows': 5})
        form.fields['custom_js'].widget.attrs.update({'class': 'form-control', 'rows': 5})
        return form

    def form_valid(self, form):
        messages.success(self.request, f'Widget "{form.instance.name}" atualizado com sucesso!')
        return super().form_valid(form)


@method_decorator(staff_required, name='dispatch')
class WidgetDeleteView(DeleteView):
    model = Widget
    template_name = 'config/widgets/widget_confirm_delete.html'
    success_url = reverse_lazy('config:widget-list')

    def delete(self, request, *args, **kwargs):
        widget = self.get_object()
        messages.success(request, f'Widget "{widget.name}" removido com sucesso!')
        return super().delete(request, *args, **kwargs)


# ==================== VIEWS DE MENUS ====================

@method_decorator(staff_required, name='dispatch')
class MenuConfigListView(ListView):
    model = MenuConfig
    template_name = 'config/menus/menu_list.html'
    context_object_name = 'menus'

    def get_queryset(self):
        queryset = MenuConfig.objects.filter(parent__isnull=True)

        menu_type = self.request.GET.get('type')
        if menu_type:
            queryset = queryset.filter(menu_type=menu_type)

        return queryset.order_by('menu_type', 'order', 'title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_types'] = MenuConfig.MENU_TYPES
        context['current_type'] = self.request.GET.get('type', '')
        return context


@method_decorator(staff_required, name='dispatch')
class MenuConfigCreateView(CreateView):
    model = MenuConfig
    template_name = 'config/menus/menu_form.html'
    fields = ['name', 'menu_type', 'parent', 'title', 'url', 'icon_type', 'icon',
              'order', 'is_active', 'is_external', 'open_in_new_tab', 'required_permission',
              'required_group', 'staff_only', 'authenticated_only', 'css_class',
              'badge_text', 'badge_color']
    success_url = reverse_lazy('config:menu-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Adicionar classes CSS aos campos
        form.fields['name'].widget.attrs.update({'class': 'form-control'})
        form.fields['menu_type'].widget.attrs.update({'class': 'form-select'})
        form.fields['parent'].widget.attrs.update({'class': 'form-select'})
        form.fields['title'].widget.attrs.update({'class': 'form-control'})
        form.fields['url'].widget.attrs.update({'class': 'form-control'})
        form.fields['icon_type'].widget.attrs.update({'class': 'form-select'})
        form.fields['icon'].widget.attrs.update({'class': 'form-control'})
        form.fields['order'].widget.attrs.update({'class': 'form-control', 'type': 'number'})
        form.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['is_external'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['open_in_new_tab'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['required_permission'].widget.attrs.update({'class': 'form-control'})
        form.fields['required_group'].widget.attrs.update({'class': 'form-control'})
        form.fields['staff_only'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['authenticated_only'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['css_class'].widget.attrs.update({'class': 'form-control'})
        form.fields['badge_text'].widget.attrs.update({'class': 'form-control'})
        form.fields['badge_color'].widget.attrs.update({'class': 'form-select'})
        return form

    def form_valid(self, form):
        messages.success(self.request, f'Item de menu "{form.instance.title}" criado com sucesso!')
        return super().form_valid(form)


@method_decorator(staff_required, name='dispatch')
class MenuConfigUpdateView(UpdateView):
    model = MenuConfig
    template_name = 'config/menus/menu_form.html'
    fields = ['name', 'menu_type', 'parent', 'title', 'url', 'icon_type', 'icon',
              'order', 'is_active', 'is_external', 'open_in_new_tab', 'required_permission',
              'required_group', 'staff_only', 'authenticated_only', 'css_class',
              'badge_text', 'badge_color']
    success_url = reverse_lazy('config:menu-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Adicionar classes CSS aos campos
        form.fields['name'].widget.attrs.update({'class': 'form-control'})
        form.fields['menu_type'].widget.attrs.update({'class': 'form-select'})
        form.fields['parent'].widget.attrs.update({'class': 'form-select'})
        form.fields['title'].widget.attrs.update({'class': 'form-control'})
        form.fields['url'].widget.attrs.update({'class': 'form-control'})
        form.fields['icon_type'].widget.attrs.update({'class': 'form-select'})
        form.fields['icon'].widget.attrs.update({'class': 'form-control'})
        form.fields['order'].widget.attrs.update({'class': 'form-control', 'type': 'number'})
        form.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['is_external'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['open_in_new_tab'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['required_permission'].widget.attrs.update({'class': 'form-control'})
        form.fields['required_group'].widget.attrs.update({'class': 'form-control'})
        form.fields['staff_only'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['authenticated_only'].widget.attrs.update({'class': 'form-check-input'})
        form.fields['css_class'].widget.attrs.update({'class': 'form-control'})
        form.fields['badge_text'].widget.attrs.update({'class': 'form-control'})
        form.fields['badge_color'].widget.attrs.update({'class': 'form-select'})
        return form

    def form_valid(self, form):
        messages.success(self.request, f'Item de menu "{form.instance.title}" atualizado com sucesso!')
        return super().form_valid(form)


@method_decorator(staff_required, name='dispatch')
class MenuConfigDeleteView(DeleteView):
    model = MenuConfig
    template_name = 'config/menus/menu_confirm_delete.html'
    success_url = reverse_lazy('config:menu-list')

    def delete(self, request, *args, **kwargs):
        menu = self.get_object()
        messages.success(request, f'Item de menu "{menu.title}" removido com sucesso!')
        return super().delete(request, *args, **kwargs)


# ==================== VIEWS DE PLUGINS ====================

@method_decorator(staff_required, name='dispatch')
class PluginListView(ListView):
    model = Plugin
    template_name = 'config/plugins/plugin_list.html'
    context_object_name = 'plugins'
    paginate_by = 20

    def get_queryset(self):
        queryset = Plugin.objects.all()

        plugin_type = self.request.GET.get('type')
        if plugin_type:
            queryset = queryset.filter(plugin_type=plugin_type)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plugin_types'] = Plugin.PLUGIN_TYPES
        context['status_choices'] = Plugin.STATUS_CHOICES
        context['current_type'] = self.request.GET.get('type', '')
        context['current_status'] = self.request.GET.get('status', '')
        return context


@method_decorator(staff_required, name='dispatch')
class PluginCreateView(CreateView):
    model = Plugin
    template_name = 'config/plugins/plugin_form.html'
    fields = ['name', 'description', 'plugin_type', 'version', 'author', 'author_email',
              'homepage', 'module_path', 'entry_point', 'dependencies', 'config_schema',
              'is_core', 'auto_load', 'required_permissions']
    success_url = reverse_lazy('config:plugin-list')

    def form_valid(self, form):
        messages.success(self.request, f'Plugin "{form.instance.name}" criado com sucesso!')
        return super().form_valid(form)


@method_decorator(staff_required, name='dispatch')
class PluginUpdateView(UpdateView):
    model = Plugin
    template_name = 'config/plugins/plugin_form.html'
    fields = ['name', 'description', 'plugin_type', 'version', 'author', 'author_email',
              'homepage', 'module_path', 'entry_point', 'dependencies', 'config_schema',
              'config_data', 'is_core', 'auto_load', 'required_permissions']
    success_url = reverse_lazy('config:plugin-list')

    def form_valid(self, form):
        messages.success(self.request, f'Plugin "{form.instance.name}" atualizado com sucesso!')
        return super().form_valid(form)


@method_decorator(staff_required, name='dispatch')
class PluginDeleteView(DeleteView):
    model = Plugin
    template_name = 'config/plugins/plugin_confirm_delete.html'
    success_url = reverse_lazy('config:plugin-list')

    def get_object(self):
        plugin = super().get_object()
        if plugin.is_core:
            raise PermissionDenied("Plugins do sistema não podem ser removidos.")
        return plugin

    def delete(self, request, *args, **kwargs):
        plugin = self.get_object()
        # Descarregar plugin antes de remover
        plugin.unload_plugin()
        messages.success(request, f'Plugin "{plugin.name}" removido com sucesso!')
        return super().delete(request, *args, **kwargs)


# ==================== VIEWS DE AÇÕES ====================

@staff_required
def plugin_toggle(request, pk):
    """Ativa/desativa um plugin"""
    plugin = get_object_or_404(Plugin, pk=pk)

    if request.method == 'POST':
        if plugin.status == 'active':
            success, message = plugin.unload_plugin()
            action = 'desativado'
        else:
            success, message = plugin.load_plugin()
            action = 'ativado'

        if success:
            messages.success(request, f'Plugin "{plugin.name}" {action} com sucesso!')
        else:
            messages.error(request, f'Erro ao {action.replace("ado", "ar")} plugin: {message}')

    return redirect('config:plugin-list')


@staff_required
def widget_reorder(request):
    """Reordena widgets via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            widgets_order = data.get('widgets', [])

            with transaction.atomic():
                for item in widgets_order:
                    widget_id = item.get('id')
                    order = item.get('order')
                    position_x = item.get('x', 0)
                    position_y = item.get('y', 0)

                    Widget.objects.filter(id=widget_id).update(
                        order=order,
                        position_x=position_x,
                        position_y=position_y
                    )

            return JsonResponse({'success': True, 'message': 'Ordem atualizada com sucesso!'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Método não permitido'})


# ==================== VIEWS DE BACKUP ====================

@method_decorator(staff_required, name='dispatch')
class ConfigBackupListView(ListView):
    model = ConfigBackup
    template_name = 'config/backup/backup_list.html'
    context_object_name = 'backups'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['backup_types'] = ConfigBackup.BACKUP_TYPES
        return context


@staff_required
def create_backup(request):
    """Cria um novo backup das configurações"""
    if request.method == 'POST':
        name = request.POST.get('name', f'Backup {timezone.now().strftime("%d/%m/%Y %H:%M")}')
        description = request.POST.get('description', '')

        backup = ConfigBackup(
            name=name,
            description=description,
            backup_type='manual',
            created_by=request.user
        )

        success, message = backup.create_backup()

        if success:
            backup.save()
            messages.success(request, f'Backup "{name}" criado com sucesso!')
        else:
            messages.error(request, f'Erro ao criar backup: {message}')

    return redirect('config:backup-list')


@staff_required
def download_backup(request, pk):
    """Faz download de um backup"""
    backup = get_object_or_404(ConfigBackup, pk=pk)

    # Criar arquivo JSON com os dados do backup
    backup_data = {
        'metadata': {
            'name': backup.name,
            'description': backup.description,
            'created_at': backup.created_at.isoformat(),
            'created_by': backup.created_by.username if backup.created_by else None,
            'version': '1.0'
        },
        'data': {
            'system_config': backup.system_config,
            'app_configs': backup.app_configs,
            'environment_variables': backup.environment_variables,
            'database_configs': backup.database_configs,
            'ldap_configs': backup.ldap_configs,
            'email_configs': backup.email_configs,
            'social_configs': backup.social_configs,
            'widgets': backup.widgets,
            'menus': backup.menus,
            'plugins': backup.plugins,
        }
    }

    response = HttpResponse(
        json.dumps(backup_data, indent=2, ensure_ascii=False),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="backup_{backup.id}_{backup.created_at.strftime("%Y%m%d_%H%M%S")}.json"'

    return response
