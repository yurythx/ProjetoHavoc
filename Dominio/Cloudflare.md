Guia Completo: Cloudflare Tunnel com Ubuntu Server Headless
Este passo a passo detalhado irá consolidar todas as configurações para expor seus serviços no Ubuntu Server de forma segura, sem a necessidade de abrir portas no seu roteador.

Passo 1: Configurar Nameservers na Cloudflare
Acesse o painel da Hostinger, vá para Domínios > Gerenciar Nameservers e altere os nameservers atuais para os da Cloudflare.

archer.ns.cloudflare.com
aspen.ns.cloudflare.com
Atenção: Aguarde a propagação do DNS, que pode levar de 30 minutos a algumas horas. Após esse processo, a Cloudflare passará a gerenciar seus registros DNS.

Passo 2: Instalar o cloudflared no Ubuntu Server
Como você está no Ubuntu 24.04, o repositório oficial ainda não tem suporte. Usaremos a instalação via pacote .deb.

Bash

# Baixar o pacote mais recente
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Instalar o pacote
sudo dpkg -i cloudflared-linux-amd64.deb

# Corrigir dependências, se necessário
sudo apt --fix-broken install -y

# Verificar se a instalação está correta
cloudflared --version
Passo 3: Autenticar no Cloudflare (Modo Headless)
Execute o comando de login no terminal. Ele irá gerar um link de autenticação que você deve abrir no seu computador.

Bash

cloudflared tunnel login
Copie a URL longa que aparecer, cole no navegador do seu PC ou celular, e faça login na sua conta Cloudflare. Selecione o domínio projetohavoc.shop. O certificado cert.pem será baixado automaticamente para o seu servidor.

Passo 4: Criar o Túnel Cloudflare
Crie o túnel com o nome meu-tunel. Isso irá gerar um arquivo de credenciais e o UUID do túnel, que você já obteve e usaremos a seguir.

Bash

cloudflared tunnel create meu-tunel
Passo 5: Criar o Arquivo de Configuração (config.yml)
Este é o passo mais importante. Crie o diretório de configuração e, em seguida, o arquivo config.yml.

Bash

sudo mkdir -p /etc/cloudflared
sudo nano /etc/cloudflared/config.yml
Cole o conteúdo abaixo. Esta é a configuração final, com todas as portas e caminhos que verificamos juntos.

YAML

tunnel: 8a015814-22be-49e0-97f3-248417962798
credentials-file: /root/.cloudflared/8a015814-22be-49e0-97f3-248417962798.json
ingress:
  - hostname: n8n.projetohavoc.shop
    service: http://localhost:5678

  - hostname: evolution.projetohavoc.shop
    service: http://localhost:8083
    path: /manager

  - hostname: chatwoot.projetohavoc.shop
    service: http://localhost:3000

  - hostname: aapanel.projetohavoc.shop
    service: http://localhost:8888

  - hostname: minio.projetohavoc.shop
    service: http://localhost:9001

  - service: http_status:404
Salve e feche o arquivo (CTRL + O, ENTER, CTRL + X).

Passo 6: Criar Registros DNS
Este comando irá criar automaticamente os registros CNAME no painel DNS da Cloudflare, apontando cada subdomínio para o seu túnel.

Bash

cloudflared tunnel route dns meu-tunel n8n.projetohavoc.shop
cloudflared tunnel route dns meu-tunel evolution.projetohavoc.shop
cloudflared tunnel route dns meu-tunel chatwoot.projetohavoc.shop
cloudflared tunnel route dns meu-tunel aapanel.projetohavoc.shop
cloudflared tunnel route dns meu-tunel minio.projetohavoc.shop
Passo 7: Rodar cloudflared como um Serviço
Instale o túnel como um serviço systemd para que ele inicie automaticamente no boot.

Bash

# Instala o serviço
sudo cloudflared service install

# Habilita o início automático
sudo systemctl enable cloudflared

# Inicia o serviço agora
sudo systemctl start cloudflared

# Verifica o status
systemctl status cloudflared
A saída do status deve mostrar active (running).

Passo 8: Testar o Acesso
Finalmente, abra seu navegador e teste cada um dos seus subdomínios. Todos devem estar funcionando perfeitamente com HTTPS, sem precisar de configurações de porta no seu roteador.

https://n8n.projetohavoc.shop

https://evolution.projetohavoc.shop/manager

https://chatwoot.projetohavoc.shop

https://aapanel.projetohavoc.shop

https://minio.projetohavoc.shop