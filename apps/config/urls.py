from django.urls import path
from .views import (
    ConfigView,
    ConfigDebugView,
    SystemMonitoringView,
    SystemStatusAPIView,
    SocialProviderConfigUpdateView,
    SocialProviderConfigListView,
    SocialProviderConfigCreateView,
    EmailConfigUpdateView,
    EmailConfigListView,
    EmailConfigCreateView,
    EmailConfigTestView,
    EmailConfigSendTestView,
    EmailConfigApplyView,
    EmailConfigToggleModeView,
    EmailConfigSetDefaultView,
    EmailConfigGuideView,
    SystemConfigUpdateView,
    AppConfigListView,
    AppConfigCreateView,
    AppConfigUpdateView,
    ModuleDisabledTestView,
    EnvironmentVariableListView,
    EnvironmentVariableCreateView,
    EnvironmentVariableUpdateView,
    EnvironmentVariableDeleteView,
    EnvironmentVariableExportView,
    EnvironmentVariableImportView,
    DatabaseConfigListView,
    DatabaseConfigCreateView,
    DatabaseConfigUpdateView,
    DatabaseConfigDeleteView,
    DatabaseConfigTestView,
    LDAPConfigListView,
    LDAPConfigCreateView,
    LDAPConfigUpdateView,
    LDAPConfigDeleteView,
    LDAPConfigTestView,
    ConfigUserListView,
    ConfigUserCreateView,
    ConfigUserUpdateView,
    ConfigUserDeleteView,
    ConfigUserDetailView,
    ConfigUserToggleStatusView,
)

# Importar views avançadas
from .views_advanced import (
    WidgetListView, WidgetCreateView, WidgetUpdateView, WidgetDeleteView,
    MenuConfigListView, MenuConfigCreateView, MenuConfigUpdateView, MenuConfigDeleteView,
    PluginListView, PluginCreateView, PluginUpdateView, PluginDeleteView,
    ConfigBackupListView, plugin_toggle, widget_reorder, create_backup, download_backup
)

# Importar views do wizard
from .wizard_views import (
    SetupWizardView, wizard_summary, skip_wizard_step,
    apply_recommendation, wizard_api_status
)
from .views import performance_api

app_name = 'config'

urlpatterns = [
    path('', ConfigView.as_view(), name='config'),
    path('debug/', ConfigDebugView.as_view(), name='config-debug'),
    path('monitoring/', SystemMonitoringView.as_view(), name='system-monitoring'),
    path('api/status/', SystemStatusAPIView.as_view(), name='system-status-api'),
    path('system/<slug:slug>/', SystemConfigUpdateView.as_view(), name='system-update'),
    path('apps/', AppConfigListView.as_view(), name='app-list'),
    path('apps/create/', AppConfigCreateView.as_view(), name='app-create'),
    path('apps/<int:pk>/', AppConfigUpdateView.as_view(), name='app-update'),
    path('test-module-disabled/', ModuleDisabledTestView.as_view(), name='test-module-disabled'),

    # Email Configuration URLs
    path('email/', EmailConfigListView.as_view(), name='email-list'),
    path('email/guide/', EmailConfigGuideView.as_view(), name='email-guide'),
    path('email/create/', EmailConfigCreateView.as_view(), name='email-create'),
    path('email/<slug:slug>/', EmailConfigUpdateView.as_view(), name='email-update'),
    path('email/<slug:slug>/test/', EmailConfigTestView.as_view(), name='email-test'),
    path('email/<slug:slug>/send-test/', EmailConfigSendTestView.as_view(), name='email-send-test'),
    path('email/<slug:slug>/apply/', EmailConfigApplyView.as_view(), name='email-apply'),
    path('email/<slug:slug>/toggle-mode/', EmailConfigToggleModeView.as_view(), name='email-toggle-mode'),
    path('email/<slug:slug>/set-default/', EmailConfigSetDefaultView.as_view(), name='email-set-default'),

    # Social Provider URLs
    path('social-providers/', SocialProviderConfigListView.as_view(), name='social-provider-list'),
    path('social-providers/create/', SocialProviderConfigCreateView.as_view(), name='social-provider-create'),
    path('social-providers/<slug:slug>/', SocialProviderConfigUpdateView.as_view(), name='social-provider-update'),

    # Environment Variables URLs
    path('environment-variables/', EnvironmentVariableListView.as_view(), name='env-variables'),
    path('environment-variables/create/', EnvironmentVariableCreateView.as_view(), name='env-variable-create'),
    path('environment-variables/<int:pk>/edit/', EnvironmentVariableUpdateView.as_view(), name='env-variable-edit'),
    path('environment-variables/<int:pk>/delete/', EnvironmentVariableDeleteView.as_view(), name='env-variable-delete'),
    path('environment-variables/export/', EnvironmentVariableExportView.as_view(), name='env-variables-export'),
    path('environment-variables/import/', EnvironmentVariableImportView.as_view(), name='env-variables-import'),

    # Database Configuration URLs
    path('database/', DatabaseConfigListView.as_view(), name='database-list'),
    path('database/create/', DatabaseConfigCreateView.as_view(), name='database-create'),
    path('database/<int:pk>/edit/', DatabaseConfigUpdateView.as_view(), name='database-edit'),
    path('database/<int:pk>/delete/', DatabaseConfigDeleteView.as_view(), name='database-delete'),
    path('database/<int:pk>/test/', DatabaseConfigTestView.as_view(), name='database-test'),

    # LDAP Configuration URLs
    path('ldap/', LDAPConfigListView.as_view(), name='ldap-list'),
    path('ldap/create/', LDAPConfigCreateView.as_view(), name='ldap-create'),
    path('ldap/<int:pk>/edit/', LDAPConfigUpdateView.as_view(), name='ldap-edit'),
    path('ldap/<int:pk>/delete/', LDAPConfigDeleteView.as_view(), name='ldap-delete'),
    path('ldap/<int:pk>/test/', LDAPConfigTestView.as_view(), name='ldap-test'),

    # Widget Management URLs
    path('widgets/', WidgetListView.as_view(), name='widget-list'),
    path('widgets/create/', WidgetCreateView.as_view(), name='widget-create'),
    path('widgets/<int:pk>/edit/', WidgetUpdateView.as_view(), name='widget-edit'),
    path('widgets/<int:pk>/delete/', WidgetDeleteView.as_view(), name='widget-delete'),
    path('widgets/reorder/', widget_reorder, name='widget-reorder'),

    # Menu Configuration URLs
    path('menus/', MenuConfigListView.as_view(), name='menu-list'),
    path('menus/create/', MenuConfigCreateView.as_view(), name='menu-create'),
    path('menus/<int:pk>/edit/', MenuConfigUpdateView.as_view(), name='menu-edit'),
    path('menus/<int:pk>/delete/', MenuConfigDeleteView.as_view(), name='menu-delete'),

    # Plugin Management URLs
    path('plugins/', PluginListView.as_view(), name='plugin-list'),
    path('plugins/create/', PluginCreateView.as_view(), name='plugin-create'),
    path('plugins/<int:pk>/edit/', PluginUpdateView.as_view(), name='plugin-edit'),
    path('plugins/<int:pk>/delete/', PluginDeleteView.as_view(), name='plugin-delete'),
    path('plugins/<int:pk>/toggle/', plugin_toggle, name='plugin-toggle'),

    # Backup Management URLs
    path('backups/', ConfigBackupListView.as_view(), name='backup-list'),
    path('backups/create/', create_backup, name='backup-create'),
    path('backups/<int:pk>/download/', download_backup, name='backup-download'),

    # User Management URLs
    path('users/', ConfigUserListView.as_view(), name='user-list'),
    path('users/create/', ConfigUserCreateView.as_view(), name='user-create'),
    path('users/<int:pk>/', ConfigUserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/edit/', ConfigUserUpdateView.as_view(), name='user-edit'),
    path('users/<int:pk>/delete/', ConfigUserDeleteView.as_view(), name='user-delete'),
    path('users/<int:pk>/toggle-status/', ConfigUserToggleStatusView.as_view(), name='user-toggle-status'),

    # Setup Wizard URLs
    path('wizard/', SetupWizardView.as_view(), name='wizard'),
    path('wizard/<uuid:wizard_id>/', SetupWizardView.as_view(), name='wizard_continue'),
    path('wizard/<uuid:wizard_id>/<str:step>/', SetupWizardView.as_view(), name='wizard_step'),
    path('wizard/<uuid:wizard_id>/summary/', wizard_summary, name='wizard_summary'),
    path('wizard/<uuid:wizard_id>/skip/<str:step>/', skip_wizard_step, name='wizard_skip_step'),
    path('wizard/<uuid:wizard_id>/recommendation/<int:recommendation_id>/apply/', apply_recommendation, name='wizard_apply_recommendation'),
    path('wizard/<uuid:wizard_id>/api/status/', wizard_api_status, name='wizard_api_status'),

    # Performance API
    path('api/performance/', performance_api, name='performance_api'),
]