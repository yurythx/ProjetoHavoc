#!/usr/bin/env python
"""
Dashboard de Monitoramento de Segurança - Projeto Havoc
Interface web simples para visualizar status de segurança em tempo real
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify
import threading
import time

app = Flask(__name__)

# Template HTML do dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ Dashboard de Segurança - Projeto Havoc</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .stat-label {
            color: #666;
            font-size: 1.1em;
        }
        
        .status-good { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-danger { color: #dc3545; }
        
        .alerts-section {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        
        .alert-item {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        .alert-critical {
            background: #f8d7da;
            border-color: #dc3545;
        }
        
        .alert-high {
            background: #fff3cd;
            border-color: #ffc107;
        }
        
        .alert-medium {
            background: #d1ecf1;
            border-color: #17a2b8;
        }
        
        .alert-timestamp {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        
        .alert-message {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .alert-details {
            font-size: 0.9em;
            color: #555;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 50px;
            padding: 15px 25px;
            font-size: 1.1em;
            cursor: pointer;
            box-shadow: 0 5px 15px rgba(0,123,255,0.3);
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: #0056b3;
            transform: scale(1.05);
        }
        
        .last-update {
            text-align: center;
            color: white;
            margin-top: 20px;
            opacity: 0.8;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .loading {
            animation: pulse 1.5s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Dashboard de Segurança</h1>
            <p>Sistema de Monitoramento Projeto Havoc</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">🚨</div>
                <div class="stat-value status-danger" id="alerts-count">-</div>
                <div class="stat-label">Alertas Ativos</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon">🔍</div>
                <div class="stat-value status-warning" id="events-24h">-</div>
                <div class="stat-label">Eventos (24h)</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon">🌐</div>
                <div class="stat-value status-good" id="requests-count">-</div>
                <div class="stat-label">Requests Monitorados</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon">⚡</div>
                <div class="stat-value status-good" id="uptime">-</div>
                <div class="stat-label">Uptime (horas)</div>
            </div>
        </div>
        
        <div class="alerts-section">
            <h2 class="section-title">🚨 Alertas Recentes</h2>
            <div id="alerts-list">
                <div class="loading">Carregando alertas...</div>
            </div>
        </div>
        
        <div class="alerts-section">
            <h2 class="section-title">📊 Eventos por Tipo (24h)</h2>
            <div id="events-chart">
                <div class="loading">Carregando estatísticas...</div>
            </div>
        </div>
        
        <div class="alerts-section">
            <h2 class="section-title">🌍 Top IPs Suspeitos</h2>
            <div id="suspicious-ips">
                <div class="loading">Carregando dados...</div>
            </div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshData()">🔄 Atualizar</button>
    
    <div class="last-update">
        Última atualização: <span id="last-update">-</span>
    </div>
    
    <script>
        function refreshData() {
            document.getElementById('last-update').textContent = new Date().toLocaleString('pt-BR');
            
            // Buscar estatísticas
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('alerts-count').textContent = data.unresolved_alerts || 0;
                    document.getElementById('events-24h').textContent = Object.values(data.events_by_type_24h || {}).reduce((a, b) => a + b, 0);
                    document.getElementById('requests-count').textContent = data.events_processed || 0;
                    document.getElementById('uptime').textContent = Math.round((data.uptime || 0) / 3600);
                })
                .catch(error => console.error('Erro ao buscar stats:', error));
            
            // Buscar alertas
            fetch('/api/alerts')
                .then(response => response.json())
                .then(data => {
                    const alertsList = document.getElementById('alerts-list');
                    if (data.length === 0) {
                        alertsList.innerHTML = '<p style="text-align: center; color: #28a745;">✅ Nenhum alerta ativo</p>';
                    } else {
                        alertsList.innerHTML = data.map(alert => `
                            <div class="alert-item alert-${alert.severity.toLowerCase()}">
                                <div class="alert-timestamp">${new Date(alert.timestamp).toLocaleString('pt-BR')}</div>
                                <div class="alert-message">${alert.message}</div>
                                <div class="alert-details">${alert.details || ''}</div>
                            </div>
                        `).join('');
                    }
                })
                .catch(error => console.error('Erro ao buscar alertas:', error));
            
            // Buscar eventos por tipo
            fetch('/api/events-by-type')
                .then(response => response.json())
                .then(data => {
                    const eventsChart = document.getElementById('events-chart');
                    if (Object.keys(data).length === 0) {
                        eventsChart.innerHTML = '<p style="text-align: center; color: #28a745;">✅ Nenhum evento suspeito nas últimas 24h</p>';
                    } else {
                        eventsChart.innerHTML = Object.entries(data).map(([type, count]) => `
                            <div style="display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #eee;">
                                <span>${type}</span>
                                <strong>${count}</strong>
                            </div>
                        `).join('');
                    }
                })
                .catch(error => console.error('Erro ao buscar eventos:', error));
            
            // Buscar IPs suspeitos
            fetch('/api/suspicious-ips')
                .then(response => response.json())
                .then(data => {
                    const suspiciousIps = document.getElementById('suspicious-ips');
                    if (data.length === 0) {
                        suspiciousIps.innerHTML = '<p style="text-align: center; color: #28a745;">✅ Nenhum IP suspeito detectado</p>';
                    } else {
                        suspiciousIps.innerHTML = data.map(([ip, count]) => `
                            <div style="display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #eee;">
                                <span>${ip}</span>
                                <strong>${count} eventos</strong>
                            </div>
                        `).join('');
                    }
                })
                .catch(error => console.error('Erro ao buscar IPs:', error));
        }
        
        // Atualizar dados a cada 30 segundos
        setInterval(refreshData, 30000);
        
        // Carregar dados iniciais
        refreshData();
    </script>
</body>
</html>
"""

class SecurityDashboard:
    def __init__(self, db_path='logs/security_monitor.db'):
        self.db_path = db_path
        self.start_time = time.time()
    
    def get_stats(self):
        """Retorna estatísticas do sistema"""
        try:
            if not os.path.exists(self.db_path):
                return {
                    'events_processed': 0,
                    'events_by_type_24h': {},
                    'unresolved_alerts': 0,
                    'top_suspicious_ips': [],
                    'uptime': time.time() - self.start_time
                }
            
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
                
                # Total de eventos processados
                cursor = conn.execute('SELECT COUNT(*) FROM security_events')
                events_processed = cursor.fetchone()[0]
            
            return {
                'events_processed': events_processed,
                'events_by_type_24h': events_by_type,
                'unresolved_alerts': unresolved_alerts,
                'top_suspicious_ips': top_suspicious_ips,
                'uptime': time.time() - self.start_time
            }
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def get_recent_alerts(self, limit=10):
        """Retorna alertas recentes"""
        try:
            if not os.path.exists(self.db_path):
                return []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT timestamp, alert_type, severity, message, details
                    FROM alerts 
                    WHERE resolved = FALSE
                    ORDER BY datetime(timestamp) DESC
                    LIMIT ?
                ''', (limit,))
                
                alerts = []
                for row in cursor.fetchall():
                    alerts.append({
                        'timestamp': row[0],
                        'type': row[1],
                        'severity': row[2],
                        'message': row[3],
                        'details': row[4]
                    })
                
                return alerts
        except Exception as e:
            print(f"Erro ao obter alertas: {e}")
            return []

# Instância global do dashboard
dashboard = SecurityDashboard()

@app.route('/')
def index():
    """Página principal do dashboard"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/stats')
def api_stats():
    """API para estatísticas"""
    return jsonify(dashboard.get_stats())

@app.route('/api/alerts')
def api_alerts():
    """API para alertas"""
    return jsonify(dashboard.get_recent_alerts())

@app.route('/api/events-by-type')
def api_events_by_type():
    """API para eventos por tipo"""
    stats = dashboard.get_stats()
    return jsonify(stats.get('events_by_type_24h', {}))

@app.route('/api/suspicious-ips')
def api_suspicious_ips():
    """API para IPs suspeitos"""
    stats = dashboard.get_stats()
    return jsonify(stats.get('top_suspicious_ips', []))

def run_dashboard(host='127.0.0.1', port=5000, debug=False):
    """Executa o dashboard"""
    print(f"🚀 Iniciando Dashboard de Segurança...")
    print(f"📊 Acesse: http://{host}:{port}")
    print("🔄 Atualizações automáticas a cada 30 segundos")
    print("⏹️  Pressione Ctrl+C para parar")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Dashboard de Segurança Projeto Havoc')
    parser.add_argument('--host', default='127.0.0.1', help='Host do servidor')
    parser.add_argument('--port', type=int, default=5000, help='Porta do servidor')
    parser.add_argument('--debug', action='store_true', help='Modo debug')
    
    args = parser.parse_args()
    
    run_dashboard(args.host, args.port, args.debug)
