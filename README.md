# 🚀 Projeto Havoc - Sistema de Gerenciamento Modular

Sistema de gerenciamento modular e inteligente desenvolvido em Django, com interface moderna e funcionalidades avançadas.

## ✨ Características

- 🎨 **Interface Moderna**: Design responsivo com Bootstrap 5
- 👥 **Gestão de Usuários**: Sistema completo de autenticação e autorização
- 🔐 **Autenticação Social**: Login com Google, GitHub e LDAP
- ⚙️ **Sistema Modular**: Configuração flexível de módulos e plugins
- 📊 **Dashboard Intuitivo**: Painel de controle com estatísticas
- 🛡️ **Segurança Avançada**: Proteção contra ataques comuns
- 🌐 **Multilíngue**: Suporte a português brasileiro

## 🛠️ Tecnologias

- **Backend**: Django 5.2.1
- **Frontend**: Bootstrap 5, Font Awesome, JavaScript
- **Banco de Dados**: SQLite (padrão), PostgreSQL, MySQL
- **Autenticação**: Django Allauth
- **Formulários**: Django Crispy Forms
- **Segurança**: CSRF, HSTS, XSS Protection

## 📋 Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)
- Git

## 🚀 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/projeto-havoc.git
cd projeto-havoc
```

### 2. Crie um ambiente virtual
```bash
python -m venv env
```

### 3. Ative o ambiente virtual
```bash
# Windows
env\Scripts\activate

# Linux/Mac
source env/bin/activate
```

### 4. Instale as dependências
```bash
pip install -r requirements.txt
```

### 5. Configure as variáveis de ambiente
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env com suas configurações
```

### 6. Execute as migrações
```bash
python manage.py migrate
```

### 7. Crie um superusuário
```bash
python manage.py createsuperuser
```

### 8. Colete os arquivos estáticos
```bash
python manage.py collectstatic
```

### 9. Execute o servidor
```bash
python manage.py runserver
```

Acesse: http://localhost:8000

## ⚙️ Configuração

### Variáveis de Ambiente

Edite o arquivo `.env` com suas configurações:

```env
# Configurações básicas
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de dados
DATABASE_URL=sqlite:///db.sqlite3

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
EMAIL_USE_TLS=True
```

### Autenticação Social (Opcional)

Para habilitar login social, configure:

1. **Google OAuth**:
   - Acesse [Google Cloud Console](https://console.cloud.google.com/)
   - Crie um projeto e configure OAuth 2.0
   - Adicione as credenciais no arquivo `.env`

2. **GitHub OAuth**:
   - Acesse [GitHub Developer Settings](https://github.com/settings/developers)
   - Crie uma nova OAuth App
   - Adicione as credenciais no arquivo `.env`

### LDAP (Opcional)

Para autenticação LDAP corporativa, configure:

```env
LDAP_SERVER=ldap.seudominio.com
LDAP_PORT=389
LDAP_BIND_DN=cn=admin,dc=seudominio,dc=com
LDAP_BIND_PASSWORD=sua-senha-ldap
```

## 📁 Estrutura do Projeto

```
projeto-havoc/
├── apps/                   # Aplicações Django
│   ├── accounts/          # Gestão de usuários
│   ├── articles/          # Sistema de artigos
│   ├── config/            # Configurações do sistema
│   └── pages/             # Páginas estáticas
├── core/                  # Configurações principais
├── static/                # Arquivos estáticos
├── templates/             # Templates base
├── media/                 # Uploads de usuários
├── requirements.txt       # Dependências Python
├── manage.py             # Script de gerenciamento Django
└── .env.example          # Exemplo de configuração
```

## 🔧 Comandos Úteis

```bash
# Executar testes
python manage.py test

# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic

# Verificar configuração
python manage.py check

# Verificar configuração para produção
python manage.py check --deploy
```

## 🛡️ Segurança

O sistema inclui várias medidas de segurança:

- Proteção CSRF
- Validação de entrada
- Sanitização de dados
- Headers de segurança
- Criptografia de senhas
- Controle de sessão

Para produção, certifique-se de:

1. Definir `DEBUG=False`
2. Configurar `SECRET_KEY` única
3. Configurar `ALLOWED_HOSTS`
4. Habilitar HTTPS
5. Configurar headers de segurança

## 📚 Documentação

- [Django Documentation](https://docs.djangoproject.com/)
- [Bootstrap Documentation](https://getbootstrap.com/docs/)
- [Django Allauth](https://django-allauth.readthedocs.io/)

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte e dúvidas:

- 📧 Email: suporte@projetohavoc.com
- 🐛 Issues: [GitHub Issues](https://github.com/seu-usuario/projeto-havoc/issues)
- 📖 Wiki: [GitHub Wiki](https://github.com/seu-usuario/projeto-havoc/wiki)

---

Desenvolvido com ❤️ pela equipe Projeto Havoc
