#!/usr/bin/env python
"""
Sistema de Monitoramento de Segurança em Tempo Real - Projeto Havoc
Monitora logs, detecta ameaças e envia alertas
"""

import os
import sys
import time
import json
import smtplib
import logging
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path
import re
import threading
from collections import defaultdict, deque
import sqlite3

class SecurityMonitor:
    def __init__(self, config_file='security_monitor_config.json'):
        self.config = self.load_config(config_file)
        self.threat_patterns = self.load_threat_patterns()
        self.alert_queue = deque(maxlen=1000)
        self.stats = defaultdict(int)
        self.ip_tracker = defaultdict(lambda: {'requests': 0, 'last_seen': datetime.now()})
        self.running = False
        
        # Configurar banco de dados para histórico
        self.setup_database()
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/security_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_file):
        """Carrega configurações do monitor"""
        default_config = {
            'log_files': [
                'logs/security.log',
                'logs/django.log'
            ],
            'alert_thresholds': {
                'failed_logins_per_minute': 10,
                'requests_per_minute_per_ip': 100,
                'suspicious_requests_per_hour': 50,
                'error_rate_threshold': 0.1
            },
            'email_alerts': {
                'enabled': False,
                'smtp_server': 'localhost',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_email': 'security@projetohavoc.com',
                'to_emails': ['admin@projetohavoc.com']
            },
            'webhook_alerts': {
                'enabled': False,
                'url': '',
                'headers': {}
            },
            'monitoring_interval': 30,  # segundos
            'retention_days': 30
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # Merge com configurações padrão
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                return config
            else:
                # Criar arquivo de configuração padrão
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {e}")
            return default_config
    
    def load_threat_patterns(self):
        """Carrega padrões de ameaças conhecidas"""
        return {
            'sql_injection': [
                r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
                r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%23)|(#))",
                r"w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
                r"((\%27)|(\'))union",
                r"exec(\s|\+)+(s|x)p\w+"
            ],
            'xss': [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>"
            ],
            'directory_traversal': [
                r"\.\.[\\/]",
                r"\.\.%2f",
                r"\.\.%5c",
                r"%2e%2e%2f",
                r"%2e%2e%5c"
            ],
            'command_injection': [
                r"[;&|`]",
                r"\$\(",
                r"`.*`",
                r"\|\s*\w+",
                r";\s*\w+"
            ],
            'suspicious_user_agents': [
                r"sqlmap",
                r"nikto",
                r"nmap",
                r"masscan",
                r"burp",
                r"owasp",
                r"dirbuster",
                r"gobuster",
                r"wfuzz",
                r"hydra"
            ]
        }
    
    def setup_database(self):
        """Configura banco de dados para histórico"""
        self.db_path = 'logs/security_monitor.db'
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    source_ip TEXT,
                    user_agent TEXT,
                    url TEXT,
                    details TEXT,
                    raw_log TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON security_events(timestamp)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
                ON alerts(timestamp)
            ''')
    
    def parse_log_line(self, line, log_file):
        """Analisa uma linha de log"""
        try:
            # Tentar parsear como JSON (logs estruturados)
            if line.strip().startswith('{'):
                log_data = json.loads(line.strip())
                return self.analyze_structured_log(log_data, log_file)
            else:
                # Parsear log de texto simples
                return self.analyze_text_log(line, log_file)
        except Exception as e:
            self.logger.debug(f"Erro ao parsear linha: {e}")
            return None
    
    def analyze_structured_log(self, log_data, log_file):
        """Analisa log estruturado (JSON)"""
        events = []
        
        # Extrair informações básicas
        timestamp = log_data.get('time', datetime.now().isoformat())
        level = log_data.get('level', 'INFO')
        message = log_data.get('message', '')
        
        # Detectar padrões de ameaças
        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    events.append({
                        'timestamp': timestamp,
                        'event_type': threat_type,
                        'severity': 'HIGH',
                        'source_ip': log_data.get('ip', 'unknown'),
                        'user_agent': log_data.get('user_agent', ''),
                        'url': log_data.get('url', ''),
                        'details': f'Padrão detectado: {pattern}',
                        'raw_log': json.dumps(log_data)
                    })
                    break
        
        # Detectar tentativas de login falhadas
        if 'login' in message.lower() and any(word in message.lower() for word in ['failed', 'invalid', 'error']):
            events.append({
                'timestamp': timestamp,
                'event_type': 'failed_login',
                'severity': 'MEDIUM',
                'source_ip': log_data.get('ip', 'unknown'),
                'user_agent': log_data.get('user_agent', ''),
                'url': log_data.get('url', ''),
                'details': 'Tentativa de login falhada',
                'raw_log': json.dumps(log_data)
            })
        
        return events
    
    def analyze_text_log(self, line, log_file):
        """Analisa log de texto simples"""
        events = []
        
        # Extrair timestamp (formato Django)
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().isoformat()
        
        # Extrair IP
        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
        source_ip = ip_match.group(1) if ip_match else 'unknown'
        
        # Detectar padrões de ameaças
        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    events.append({
                        'timestamp': timestamp,
                        'event_type': threat_type,
                        'severity': 'HIGH',
                        'source_ip': source_ip,
                        'user_agent': '',
                        'url': '',
                        'details': f'Padrão detectado: {pattern}',
                        'raw_log': line.strip()
                    })
                    break
        
        # Detectar erros HTTP
        if re.search(r'HTTP/1\.[01]"\s+[45]\d{2}', line):
            events.append({
                'timestamp': timestamp,
                'event_type': 'http_error',
                'severity': 'LOW',
                'source_ip': source_ip,
                'user_agent': '',
                'url': '',
                'details': 'Erro HTTP detectado',
                'raw_log': line.strip()
            })
        
        return events
    
    def store_events(self, events):
        """Armazena eventos no banco de dados"""
        if not events:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            for event in events:
                conn.execute('''
                    INSERT INTO security_events 
                    (timestamp, event_type, severity, source_ip, user_agent, url, details, raw_log)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event['timestamp'],
                    event['event_type'],
                    event['severity'],
                    event['source_ip'],
                    event['user_agent'],
                    event['url'],
                    event['details'],
                    event['raw_log']
                ))
    
    def check_thresholds(self):
        """Verifica se algum threshold foi ultrapassado"""
        now = datetime.now()
        alerts = []
        
        # Verificar eventos recentes
        with sqlite3.connect(self.db_path) as conn:
            # Failed logins por minuto
            cursor = conn.execute('''
                SELECT COUNT(*) FROM security_events 
                WHERE event_type = 'failed_login' 
                AND datetime(timestamp) > datetime(?, '-1 minute')
            ''', (now.isoformat(),))
            
            failed_logins = cursor.fetchone()[0]
            if failed_logins > self.config['alert_thresholds']['failed_logins_per_minute']:
                alerts.append({
                    'type': 'threshold_exceeded',
                    'severity': 'HIGH',
                    'message': f'Muitas tentativas de login falhadas: {failed_logins}/min',
                    'details': {'count': failed_logins, 'threshold': self.config['alert_thresholds']['failed_logins_per_minute']}
                })
            
            # Requests suspeitos por hora
            cursor = conn.execute('''
                SELECT COUNT(*) FROM security_events 
                WHERE event_type IN ('sql_injection', 'xss', 'directory_traversal', 'command_injection')
                AND datetime(timestamp) > datetime(?, '-1 hour')
            ''', (now.isoformat(),))
            
            suspicious_requests = cursor.fetchone()[0]
            if suspicious_requests > self.config['alert_thresholds']['suspicious_requests_per_hour']:
                alerts.append({
                    'type': 'threshold_exceeded',
                    'severity': 'CRITICAL',
                    'message': f'Muitos requests suspeitos: {suspicious_requests}/hora',
                    'details': {'count': suspicious_requests, 'threshold': self.config['alert_thresholds']['suspicious_requests_per_hour']}
                })
        
        return alerts
    
    def send_alert(self, alert):
        """Envia alerta via email ou webhook"""
        # Armazenar alerta no banco
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO alerts (timestamp, alert_type, severity, message, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                alert['type'],
                alert['severity'],
                alert['message'],
                json.dumps(alert.get('details', {}))
            ))
        
        # Enviar por email se configurado
        if self.config['email_alerts']['enabled']:
            self.send_email_alert(alert)
        
        # Enviar por webhook se configurado
        if self.config['webhook_alerts']['enabled']:
            self.send_webhook_alert(alert)
        
        # Log do alerta
        severity_emoji = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }.get(alert['severity'], '⚪')
        
        self.logger.warning(f"{severity_emoji} ALERTA {alert['severity']}: {alert['message']}")
    
    def send_email_alert(self, alert):
        """Envia alerta por email"""
        try:
            config = self.config['email_alerts']
            
            msg = MimeMultipart()
            msg['From'] = config['from_email']
            msg['To'] = ', '.join(config['to_emails'])
            msg['Subject'] = f"[PROJETO HAVOC SECURITY] Alerta {alert['severity']}"

            body = f"""
            ALERTA DE SEGURANÇA - SISTEMA PROJETO HAVOC
            
            Severidade: {alert['severity']}
            Tipo: {alert['type']}
            Mensagem: {alert['message']}
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Detalhes:
            {json.dumps(alert.get('details', {}), indent=2)}
            
            ---
            Sistema de Monitoramento de Segurança Projeto Havoc
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            if config['username']:
                server.starttls()
                server.login(config['username'], config['password'])
            
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email: {e}")
    
    def send_webhook_alert(self, alert):
        """Envia alerta via webhook"""
        try:
            import requests
            
            config = self.config['webhook_alerts']
            
            payload = {
                'timestamp': datetime.now().isoformat(),
                'system': 'projeto-havoc',
                'alert': alert
            }
            
            response = requests.post(
                config['url'],
                json=payload,
                headers=config.get('headers', {}),
                timeout=10
            )
            
            response.raise_for_status()
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar webhook: {e}")
    
    def monitor_logs(self):
        """Monitora arquivos de log em tempo real"""
        self.logger.info("Iniciando monitoramento de logs...")
        
        # Posições dos arquivos
        file_positions = {}
        
        while self.running:
            try:
                for log_file in self.config['log_files']:
                    if not os.path.exists(log_file):
                        continue
                    
                    # Verificar se arquivo foi rotacionado
                    current_size = os.path.getsize(log_file)
                    if log_file in file_positions and current_size < file_positions[log_file]:
                        file_positions[log_file] = 0
                    
                    # Ler novas linhas
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        if log_file in file_positions:
                            f.seek(file_positions[log_file])
                        
                        new_lines = f.readlines()
                        file_positions[log_file] = f.tell()
                        
                        # Processar novas linhas
                        for line in new_lines:
                            events = self.parse_log_line(line, log_file)
                            if events:
                                self.store_events(events)
                                self.stats['events_processed'] += len(events)
                
                # Verificar thresholds
                alerts = self.check_thresholds()
                for alert in alerts:
                    self.send_alert(alert)
                
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"Erro no monitoramento: {e}")
                time.sleep(5)
    
    def cleanup_old_data(self):
        """Remove dados antigos"""
        cutoff_date = datetime.now() - timedelta(days=self.config['retention_days'])
        
        with sqlite3.connect(self.db_path) as conn:
            # Remover eventos antigos
            cursor = conn.execute('''
                DELETE FROM security_events 
                WHERE datetime(timestamp) < datetime(?)
            ''', (cutoff_date.isoformat(),))
            
            events_deleted = cursor.rowcount
            
            # Remover alertas antigos resolvidos
            cursor = conn.execute('''
                DELETE FROM alerts 
                WHERE datetime(timestamp) < datetime(?) AND resolved = TRUE
            ''', (cutoff_date.isoformat(),))
            
            alerts_deleted = cursor.rowcount
            
            if events_deleted > 0 or alerts_deleted > 0:
                self.logger.info(f"Limpeza: {events_deleted} eventos e {alerts_deleted} alertas removidos")
    
    def start(self):
        """Inicia o monitoramento"""
        self.running = True
        
        # Thread para monitoramento de logs
        monitor_thread = threading.Thread(target=self.monitor_logs)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Thread para limpeza periódica
        def cleanup_worker():
            while self.running:
                time.sleep(3600)  # A cada hora
                self.cleanup_old_data()
        
        cleanup_thread = threading.Thread(target=cleanup_worker)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
        self.logger.info("Monitor de segurança iniciado")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Para o monitoramento"""
        self.running = False
        self.logger.info("Monitor de segurança parado")
    
    def get_stats(self):
        """Retorna estatísticas do monitor"""
        with sqlite3.connect(self.db_path) as conn:
            # Eventos por tipo nas últimas 24h
            cursor = conn.execute('''
                SELECT event_type, COUNT(*) 
                FROM security_events 
                WHERE datetime(timestamp) > datetime('now', '-1 day')
                GROUP BY event_type
            ''')
            events_by_type = dict(cursor.fetchall())
            
            # Alertas não resolvidos
            cursor = conn.execute('''
                SELECT COUNT(*) FROM alerts WHERE resolved = FALSE
            ''')
            unresolved_alerts = cursor.fetchone()[0]
            
            # Top IPs suspeitos
            cursor = conn.execute('''
                SELECT source_ip, COUNT(*) as count
                FROM security_events 
                WHERE datetime(timestamp) > datetime('now', '-1 day')
                AND event_type IN ('sql_injection', 'xss', 'directory_traversal', 'command_injection')
                GROUP BY source_ip
                ORDER BY count DESC
                LIMIT 10
            ''')
            top_suspicious_ips = cursor.fetchall()
        
        return {
            'events_processed': self.stats['events_processed'],
            'events_by_type_24h': events_by_type,
            'unresolved_alerts': unresolved_alerts,
            'top_suspicious_ips': top_suspicious_ips,
            'uptime': time.time() - getattr(self, 'start_time', time.time())
        }

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor de Segurança Projeto Havoc')
    parser.add_argument('--config', default='security_monitor_config.json', help='Arquivo de configuração')
    parser.add_argument('--stats', action='store_true', help='Mostrar estatísticas')
    
    args = parser.parse_args()
    
    monitor = SecurityMonitor(args.config)
    
    if args.stats:
        stats = monitor.get_stats()
        print(json.dumps(stats, indent=2))
    else:
        monitor.start_time = time.time()
        monitor.start()

if __name__ == '__main__':
    main()
