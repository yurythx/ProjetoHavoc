/**
 * Sistema de Busca para Configurações
 * Projeto Havoc - Sistema de Configurações Modular
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
    initializeFilters();
    initializeQuickActions();
});

/**
 * Inicializar sistema de busca
 */
function initializeSearch() {
    createSearchBar();
    setupSearchFunctionality();
}

/**
 * Criar barra de busca
 */
function createSearchBar() {
    const searchContainer = document.createElement('div');
    searchContainer.className = 'search-container mb-4';
    searchContainer.innerHTML = `
        <div class="row">
            <div class="col-md-8">
                <div class="input-group">
                    <span class="input-group-text">
                        <i class="fas fa-search"></i>
                    </span>
                    <input type="text" 
                           id="configSearch" 
                           class="form-control" 
                           placeholder="Buscar configurações, módulos, usuários..."
                           autocomplete="off">
                    <button class="btn btn-outline-secondary" type="button" id="clearSearch">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div id="searchSuggestions" class="search-suggestions"></div>
            </div>
            <div class="col-md-4">
                <div class="btn-group w-100" role="group">
                    <button type="button" class="btn btn-outline-primary" id="filterToggle">
                        <i class="fas fa-filter me-1"></i>Filtros
                    </button>
                    <button type="button" class="btn btn-outline-success" id="quickActionsToggle">
                        <i class="fas fa-bolt me-1"></i>Ações
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Filtros -->
        <div id="filtersPanel" class="filters-panel mt-3" style="display: none;">
            <div class="card">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-3">
                            <label class="form-label">Categoria</label>
                            <select class="form-select" id="categoryFilter">
                                <option value="">Todas</option>
                                <option value="system">Sistema</option>
                                <option value="email">Email</option>
                                <option value="auth">Autenticação</option>
                                <option value="database">Banco de Dados</option>
                                <option value="interface">Interface</option>
                                <option value="security">Segurança</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Status</label>
                            <select class="form-select" id="statusFilter">
                                <option value="">Todos</option>
                                <option value="active">Ativo</option>
                                <option value="inactive">Inativo</option>
                                <option value="error">Com Erro</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Tipo</label>
                            <select class="form-select" id="typeFilter">
                                <option value="">Todos</option>
                                <option value="config">Configuração</option>
                                <option value="module">Módulo</option>
                                <option value="user">Usuário</option>
                                <option value="plugin">Plugin</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Ações</label>
                            <div class="btn-group w-100">
                                <button type="button" class="btn btn-sm btn-outline-primary" id="applyFilters">
                                    Aplicar
                                </button>
                                <button type="button" class="btn btn-sm btn-outline-secondary" id="clearFilters">
                                    Limpar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Ações Rápidas -->
        <div id="quickActionsPanel" class="quick-actions-panel mt-3" style="display: none;">
            <div class="card">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-2">
                            <button class="btn btn-outline-primary w-100" onclick="quickAction('backup')">
                                <i class="fas fa-download d-block mb-1"></i>
                                Backup
                            </button>
                        </div>
                        <div class="col-md-2">
                            <button class="btn btn-outline-success w-100" onclick="quickAction('test-email')">
                                <i class="fas fa-envelope d-block mb-1"></i>
                                Teste Email
                            </button>
                        </div>
                        <div class="col-md-2">
                            <button class="btn btn-outline-info w-100" onclick="quickAction('system-info')">
                                <i class="fas fa-info-circle d-block mb-1"></i>
                                Info Sistema
                            </button>
                        </div>
                        <div class="col-md-2">
                            <button class="btn btn-outline-warning w-100" onclick="quickAction('clear-cache')">
                                <i class="fas fa-broom d-block mb-1"></i>
                                Limpar Cache
                            </button>
                        </div>
                        <div class="col-md-2">
                            <button class="btn btn-outline-secondary w-100" onclick="quickAction('export')">
                                <i class="fas fa-file-export d-block mb-1"></i>
                                Exportar
                            </button>
                        </div>
                        <div class="col-md-2">
                            <button class="btn btn-outline-dark w-100" onclick="quickAction('logs')">
                                <i class="fas fa-file-alt d-block mb-1"></i>
                                Logs
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Inserir no início do conteúdo principal
    const mainContent = document.querySelector('.container-fluid, .container, main');
    if (mainContent) {
        mainContent.insertBefore(searchContainer, mainContent.firstChild);
    }
}

/**
 * Configurar funcionalidade de busca
 */
function setupSearchFunctionality() {
    const searchInput = document.getElementById('configSearch');
    const clearButton = document.getElementById('clearSearch');
    const filterToggle = document.getElementById('filterToggle');
    const quickActionsToggle = document.getElementById('quickActionsToggle');
    const filtersPanel = document.getElementById('filtersPanel');
    const quickActionsPanel = document.getElementById('quickActionsPanel');
    
    if (!searchInput) return;
    
    // Busca em tempo real
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performSearch(this.value);
        }, 300);
    });
    
    // Limpar busca
    clearButton.addEventListener('click', function() {
        searchInput.value = '';
        clearSearch();
    });
    
    // Toggle filtros
    filterToggle.addEventListener('click', function() {
        const isVisible = filtersPanel.style.display !== 'none';
        filtersPanel.style.display = isVisible ? 'none' : 'block';
        quickActionsPanel.style.display = 'none';
        
        this.classList.toggle('active', !isVisible);
        quickActionsToggle.classList.remove('active');
    });
    
    // Toggle ações rápidas
    quickActionsToggle.addEventListener('click', function() {
        const isVisible = quickActionsPanel.style.display !== 'none';
        quickActionsPanel.style.display = isVisible ? 'none' : 'block';
        filtersPanel.style.display = 'none';
        
        this.classList.toggle('active', !isVisible);
        filterToggle.classList.remove('active');
    });
    
    // Aplicar filtros
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    document.getElementById('clearFilters').addEventListener('click', clearFilters);
    
    // Sugestões de busca
    setupSearchSuggestions();
}

/**
 * Realizar busca
 */
function performSearch(query) {
    const searchTerm = query.toLowerCase().trim();
    
    if (searchTerm.length < 2) {
        clearSearch();
        return;
    }
    
    // Buscar em cards, tabelas e listas
    const searchableElements = document.querySelectorAll('.card, .list-group-item, tr, .config-item');
    let visibleCount = 0;
    
    searchableElements.forEach(element => {
        const text = element.textContent.toLowerCase();
        const isMatch = text.includes(searchTerm);
        
        if (isMatch) {
            element.style.display = '';
            highlightSearchTerm(element, searchTerm);
            visibleCount++;
        } else {
            element.style.display = 'none';
        }
    });
    
    // Mostrar resultado da busca
    showSearchResults(visibleCount, searchTerm);
    
    // Atualizar sugestões
    updateSearchSuggestions(searchTerm);
}

/**
 * Limpar busca
 */
function clearSearch() {
    // Mostrar todos os elementos
    const searchableElements = document.querySelectorAll('.card, .list-group-item, tr, .config-item');
    searchableElements.forEach(element => {
        element.style.display = '';
        removeHighlight(element);
    });
    
    // Limpar resultados
    const resultsDiv = document.getElementById('searchResults');
    if (resultsDiv) {
        resultsDiv.remove();
    }
    
    // Limpar sugestões
    const suggestionsDiv = document.getElementById('searchSuggestions');
    if (suggestionsDiv) {
        suggestionsDiv.innerHTML = '';
    }
}

/**
 * Destacar termo de busca
 */
function highlightSearchTerm(element, term) {
    // Remover destaques anteriores
    removeHighlight(element);
    
    // Adicionar novo destaque
    const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );
    
    const textNodes = [];
    let node;
    
    while (node = walker.nextNode()) {
        textNodes.push(node);
    }
    
    textNodes.forEach(textNode => {
        const text = textNode.textContent;
        const regex = new RegExp(`(${term})`, 'gi');
        
        if (regex.test(text)) {
            const highlightedText = text.replace(regex, '<mark class="search-highlight">$1</mark>');
            const span = document.createElement('span');
            span.innerHTML = highlightedText;
            textNode.parentNode.replaceChild(span, textNode);
        }
    });
}

/**
 * Remover destaque
 */
function removeHighlight(element) {
    const highlights = element.querySelectorAll('.search-highlight');
    highlights.forEach(highlight => {
        const parent = highlight.parentNode;
        parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
        parent.normalize();
    });
}

/**
 * Mostrar resultados da busca
 */
function showSearchResults(count, term) {
    // Remover resultados anteriores
    const existingResults = document.getElementById('searchResults');
    if (existingResults) {
        existingResults.remove();
    }
    
    // Criar div de resultados
    const resultsDiv = document.createElement('div');
    resultsDiv.id = 'searchResults';
    resultsDiv.className = 'alert alert-info mt-2';
    resultsDiv.innerHTML = `
        <i class="fas fa-search me-2"></i>
        Encontrados <strong>${count}</strong> resultados para "<strong>${term}</strong>"
        ${count === 0 ? '<br><small>Tente termos diferentes ou use os filtros.</small>' : ''}
    `;
    
    // Inserir após a barra de busca
    const searchContainer = document.querySelector('.search-container');
    if (searchContainer) {
        searchContainer.appendChild(resultsDiv);
    }
}

/**
 * Configurar sugestões de busca
 */
function setupSearchSuggestions() {
    const suggestions = [
        'email smtp', 'configuração sistema', 'usuários ativos', 'ldap active directory',
        'banco dados', 'plugins instalados', 'backup configurações', 'logs sistema',
        'variáveis ambiente', 'widgets dashboard', 'menus navegação', 'social login'
    ];
    
    const searchInput = document.getElementById('configSearch');
    const suggestionsDiv = document.getElementById('searchSuggestions');
    
    searchInput.addEventListener('focus', function() {
        if (this.value.length === 0) {
            showSuggestions(suggestions.slice(0, 5));
        }
    });
    
    searchInput.addEventListener('blur', function() {
        // Delay para permitir clique nas sugestões
        setTimeout(() => {
            suggestionsDiv.innerHTML = '';
        }, 200);
    });
}

/**
 * Atualizar sugestões de busca
 */
function updateSearchSuggestions(term) {
    const suggestions = [
        'email smtp', 'configuração sistema', 'usuários ativos', 'ldap active directory',
        'banco dados', 'plugins instalados', 'backup configurações', 'logs sistema',
        'variáveis ambiente', 'widgets dashboard', 'menus navegação', 'social login'
    ];
    
    const filtered = suggestions.filter(s => 
        s.toLowerCase().includes(term.toLowerCase())
    ).slice(0, 3);
    
    showSuggestions(filtered);
}

/**
 * Mostrar sugestões
 */
function showSuggestions(suggestions) {
    const suggestionsDiv = document.getElementById('searchSuggestions');
    
    if (suggestions.length === 0) {
        suggestionsDiv.innerHTML = '';
        return;
    }
    
    const suggestionsHTML = suggestions.map(suggestion => 
        `<div class="suggestion-item" onclick="selectSuggestion('${suggestion}')">
            <i class="fas fa-search me-2"></i>${suggestion}
        </div>`
    ).join('');
    
    suggestionsDiv.innerHTML = `<div class="suggestions-list">${suggestionsHTML}</div>`;
}

/**
 * Selecionar sugestão
 */
function selectSuggestion(suggestion) {
    const searchInput = document.getElementById('configSearch');
    searchInput.value = suggestion;
    performSearch(suggestion);
    
    const suggestionsDiv = document.getElementById('searchSuggestions');
    suggestionsDiv.innerHTML = '';
}

/**
 * Aplicar filtros
 */
function applyFilters() {
    const category = document.getElementById('categoryFilter').value;
    const status = document.getElementById('statusFilter').value;
    const type = document.getElementById('typeFilter').value;
    
    // Implementar lógica de filtros baseada nos valores selecionados
    console.log('Aplicando filtros:', { category, status, type });
    
    // Aqui você implementaria a lógica específica de filtros
    // baseada na estrutura do seu HTML
}

/**
 * Limpar filtros
 */
function clearFilters() {
    document.getElementById('categoryFilter').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('typeFilter').value = '';
    
    // Limpar busca também
    document.getElementById('configSearch').value = '';
    clearSearch();
}

/**
 * Ações rápidas
 */
function quickAction(action) {
    switch (action) {
        case 'backup':
            if (confirm('Criar backup das configurações atuais?')) {
                window.location.href = '/config/backup/create/';
            }
            break;
            
        case 'test-email':
            const email = prompt('Digite o email para teste:');
            if (email) {
                // Implementar teste de email
                console.log('Testando email:', email);
            }
            break;
            
        case 'system-info':
            // Mostrar modal com informações do sistema
            showSystemInfo();
            break;
            
        case 'clear-cache':
            if (confirm('Limpar cache do sistema?')) {
                // Implementar limpeza de cache
                console.log('Limpando cache...');
            }
            break;
            
        case 'export':
            window.location.href = '/config/export/';
            break;
            
        case 'logs':
            window.open('/admin/logs/', '_blank');
            break;
    }
}

/**
 * Mostrar informações do sistema
 */
function showSystemInfo() {
    // Implementar modal com informações do sistema
    alert('Informações do sistema seriam mostradas aqui');
}

/**
 * Inicializar filtros
 */
function initializeFilters() {
    // Implementar filtros específicos baseados na página atual
}

/**
 * Inicializar ações rápidas
 */
function initializeQuickActions() {
    // Implementar ações rápidas específicas
}
