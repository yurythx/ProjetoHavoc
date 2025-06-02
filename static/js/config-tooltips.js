/**
 * Sistema de Tooltips para Configurações
 * Projeto Havoc - Sistema de Configurações Modular
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    initializeHelpSystem();
    initializeFormValidation();
});

/**
 * Inicializar tooltips do Bootstrap
 */
function initializeTooltips() {
    // Inicializar tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            html: true,
            delay: { show: 500, hide: 100 }
        });
    });

    // Adicionar tooltips personalizados para campos específicos
    addCustomTooltips();
}

/**
 * Adicionar tooltips personalizados
 */
function addCustomTooltips() {
    const tooltipData = {
        // Configurações de Email
        'email_host': {
            title: 'Servidor SMTP',
            content: 'Endereço do servidor SMTP para envio de emails.<br><strong>Exemplos:</strong><br>• Gmail: smtp.gmail.com<br>• Outlook: smtp-mail.outlook.com<br>• Yahoo: smtp.mail.yahoo.com'
        },
        'email_port': {
            title: 'Porta SMTP',
            content: 'Porta do servidor SMTP.<br><strong>Portas comuns:</strong><br>• 25 (não criptografada)<br>• 587 (TLS)<br>• 465 (SSL)'
        },
        'email_use_tls': {
            title: 'Usar TLS',
            content: 'Transport Layer Security para conexão segura.<br><strong>Recomendado:</strong> Sempre ativar para segurança.'
        },
        'use_console_backend': {
            title: 'Modo Console',
            content: 'Em modo console, emails aparecem no terminal em vez de serem enviados.<br><strong>Útil para:</strong> Desenvolvimento e testes.'
        },

        // Configurações do Sistema
        'site_name': {
            title: 'Nome do Site',
            content: 'Nome principal do sistema que aparece no cabeçalho e títulos.'
        },
        'maintenance_mode': {
            title: 'Modo Manutenção',
            content: 'Quando ativo, apenas administradores podem acessar o sistema.<br><strong>Cuidado:</strong> Usuários normais serão bloqueados.'
        },
        'allow_registration': {
            title: 'Permitir Registro',
            content: 'Permite que novos usuários se registrem no sistema.<br><strong>Segurança:</strong> Desative se não quiser registros públicos.'
        },
        'require_email_verification': {
            title: 'Verificação de Email',
            content: 'Exige que usuários verifiquem o email antes de ativar a conta.<br><strong>Recomendado:</strong> Para maior segurança.'
        },

        // Configurações de LDAP
        'server': {
            title: 'Servidor LDAP',
            content: 'Endereço do servidor LDAP/Active Directory.<br><strong>Formato:</strong> ldap.empresa.com ou IP'
        },
        'base_dn': {
            title: 'Base DN',
            content: 'Distinguished Name base para busca de usuários.<br><strong>Exemplo:</strong> dc=empresa,dc=com'
        },
        'bind_dn': {
            title: 'Bind DN',
            content: 'DN do usuário para autenticação no LDAP.<br><strong>Exemplo:</strong> cn=admin,dc=empresa,dc=com'
        },

        // Configurações de Banco
        'engine': {
            title: 'Engine do Banco',
            content: 'Tipo de banco de dados a ser usado.<br><strong>Suportados:</strong><br>• PostgreSQL (recomendado)<br>• MySQL<br>• SQLite<br>• Oracle'
        },
        'conn_max_age': {
            title: 'Tempo de Conexão',
            content: 'Tempo máximo (em segundos) que uma conexão fica aberta.<br><strong>0:</strong> Nova conexão a cada requisição<br><strong>600:</strong> 10 minutos (recomendado)'
        },

        // Variáveis de Ambiente
        'is_sensitive': {
            title: 'Variável Sensível',
            content: 'Marca a variável como sensível (senhas, chaves).<br><strong>Efeito:</strong> Valor será mascarado na interface.'
        },
        'is_required': {
            title: 'Obrigatória',
            content: 'Indica se a variável é obrigatória para o funcionamento do sistema.'
        }
    };

    // Aplicar tooltips aos campos
    Object.keys(tooltipData).forEach(fieldName => {
        const field = document.querySelector(`[name="${fieldName}"], #id_${fieldName}`);
        if (field) {
            const data = tooltipData[fieldName];
            field.setAttribute('data-bs-toggle', 'tooltip');
            field.setAttribute('data-bs-placement', 'top');
            field.setAttribute('data-bs-html', 'true');
            field.setAttribute('title', `<strong>${data.title}</strong><br>${data.content}`);
            
            // Adicionar ícone de ajuda ao lado do campo
            addHelpIcon(field, data);
        }
    });
}

/**
 * Adicionar ícone de ajuda ao lado do campo
 */
function addHelpIcon(field, data) {
    const helpIcon = document.createElement('i');
    helpIcon.className = 'fas fa-question-circle text-info ms-2';
    helpIcon.style.cursor = 'pointer';
    helpIcon.setAttribute('data-bs-toggle', 'tooltip');
    helpIcon.setAttribute('data-bs-placement', 'right');
    helpIcon.setAttribute('data-bs-html', 'true');
    helpIcon.setAttribute('title', `<strong>${data.title}</strong><br>${data.content}`);
    
    // Inserir após o campo
    if (field.parentNode) {
        field.parentNode.insertBefore(helpIcon, field.nextSibling);
    }
}

/**
 * Sistema de ajuda contextual
 */
function initializeHelpSystem() {
    // Adicionar botão de ajuda geral
    addGeneralHelpButton();
    
    // Adicionar guias de configuração
    addConfigurationGuides();
}

/**
 * Adicionar botão de ajuda geral
 */
function addGeneralHelpButton() {
    const helpButton = document.createElement('button');
    helpButton.type = 'button';
    helpButton.className = 'btn btn-outline-info btn-sm position-fixed';
    helpButton.style.cssText = 'bottom: 20px; right: 20px; z-index: 1050; border-radius: 50%; width: 50px; height: 50px;';
    helpButton.innerHTML = '<i class="fas fa-question"></i>';
    helpButton.setAttribute('data-bs-toggle', 'modal');
    helpButton.setAttribute('data-bs-target', '#helpModal');
    helpButton.title = 'Ajuda do Sistema';
    
    document.body.appendChild(helpButton);
    
    // Criar modal de ajuda
    createHelpModal();
}

/**
 * Criar modal de ajuda
 */
function createHelpModal() {
    const modalHTML = `
        <div class="modal fade" id="helpModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-question-circle text-info me-2"></i>
                            Ajuda do Sistema de Configurações
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6><i class="fas fa-cog me-2"></i>Configurações Gerais</h6>
                                <ul class="list-unstyled">
                                    <li><strong>Sistema:</strong> Configurações básicas do site</li>
                                    <li><strong>Apps:</strong> Gerenciar módulos do sistema</li>
                                    <li><strong>Usuários:</strong> Administração de usuários</li>
                                </ul>
                                
                                <h6><i class="fas fa-envelope me-2"></i>Email</h6>
                                <ul class="list-unstyled">
                                    <li><strong>SMTP:</strong> Configurar servidor de email</li>
                                    <li><strong>Console:</strong> Modo desenvolvimento</li>
                                    <li><strong>Teste:</strong> Verificar configurações</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6><i class="fas fa-shield-alt me-2"></i>Autenticação</h6>
                                <ul class="list-unstyled">
                                    <li><strong>LDAP:</strong> Integração com Active Directory</li>
                                    <li><strong>Social:</strong> Login com Google, GitHub, etc.</li>
                                </ul>
                                
                                <h6><i class="fas fa-database me-2"></i>Banco de Dados</h6>
                                <ul class="list-unstyled">
                                    <li><strong>Conexões:</strong> Configurar múltiplos bancos</li>
                                    <li><strong>Variáveis:</strong> Gerenciar configurações</li>
                                </ul>
                            </div>
                        </div>
                        
                        <hr>
                        
                        <div class="alert alert-info">
                            <i class="fas fa-lightbulb me-2"></i>
                            <strong>Dica:</strong> Passe o mouse sobre os campos para ver explicações detalhadas.
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

/**
 * Adicionar guias de configuração
 */
function addConfigurationGuides() {
    // Adicionar links de guia em seções específicas
    const sections = {
        'email-config': {
            title: 'Guia de Configuração de Email',
            url: '/config/email/guide/',
            icon: 'fas fa-envelope'
        },
        'ldap-config': {
            title: 'Guia de Configuração LDAP',
            url: '/config/ldap/guide/',
            icon: 'fas fa-users'
        }
    };
    
    Object.keys(sections).forEach(sectionId => {
        const section = document.getElementById(sectionId);
        if (section) {
            const guide = sections[sectionId];
            const guideLink = document.createElement('a');
            guideLink.href = guide.url;
            guideLink.className = 'btn btn-outline-info btn-sm float-end';
            guideLink.innerHTML = `<i class="${guide.icon} me-1"></i>${guide.title}`;
            
            const header = section.querySelector('h3, h4, h5');
            if (header) {
                header.appendChild(guideLink);
            }
        }
    });
}

/**
 * Validação de formulário em tempo real
 */
function initializeFormValidation() {
    // Validação de email
    const emailFields = document.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        field.addEventListener('blur', validateEmail);
    });
    
    // Validação de porta
    const portFields = document.querySelectorAll('input[name*="port"]');
    portFields.forEach(field => {
        field.addEventListener('blur', validatePort);
    });
    
    // Validação de URL
    const urlFields = document.querySelectorAll('input[name*="url"], input[name*="host"]');
    urlFields.forEach(field => {
        field.addEventListener('blur', validateUrl);
    });
}

/**
 * Validar email
 */
function validateEmail(event) {
    const field = event.target;
    const value = field.value.trim();
    
    if (value && !isValidEmail(value)) {
        showFieldError(field, 'Email inválido');
    } else {
        clearFieldError(field);
    }
}

/**
 * Validar porta
 */
function validatePort(event) {
    const field = event.target;
    const value = parseInt(field.value);
    
    if (field.value && (isNaN(value) || value < 1 || value > 65535)) {
        showFieldError(field, 'Porta deve ser um número entre 1 e 65535');
    } else {
        clearFieldError(field);
    }
}

/**
 * Validar URL
 */
function validateUrl(event) {
    const field = event.target;
    const value = field.value.trim();
    
    if (value && !isValidUrl(value)) {
        showFieldError(field, 'URL ou hostname inválido');
    } else {
        clearFieldError(field);
    }
}

/**
 * Mostrar erro no campo
 */
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

/**
 * Limpar erro do campo
 */
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

/**
 * Validar formato de email
 */
function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * Validar URL/hostname
 */
function isValidUrl(url) {
    // Aceitar tanto URLs quanto hostnames
    const urlRegex = /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/;
    const hostnameRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$/;
    
    return urlRegex.test(url) || hostnameRegex.test(url) || url === 'localhost';
}
