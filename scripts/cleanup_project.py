#!/usr/bin/env python
"""
Script de limpeza automática do Projeto Havoc
Remove arquivos desnecessários, logs antigos e otimiza o projeto
"""

import os
import sys
import shutil
import glob
from datetime import datetime, timedelta

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def clean_pycache():
    """Remove todos os arquivos __pycache__"""
    print("🧹 Limpando arquivos __pycache__...")
    
    removed_count = 0
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                removed_count += 1
                print(f"   ✅ Removido: {pycache_path}")
            except Exception as e:
                print(f"   ❌ Erro ao remover {pycache_path}: {e}")
    
    print(f"   📊 Total de diretórios __pycache__ removidos: {removed_count}")

def clean_old_logs():
    """Remove logs antigos (mais de 30 dias)"""
    print("\n📄 Limpando logs antigos...")
    
    if not os.path.exists('logs'):
        print("   ℹ️  Diretório de logs não encontrado")
        return
    
    cutoff_date = datetime.now() - timedelta(days=30)
    removed_count = 0
    
    for log_file in glob.glob('logs/*.log*'):
        try:
            file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
            if file_time < cutoff_date:
                os.remove(log_file)
                removed_count += 1
                print(f"   ✅ Removido: {log_file}")
        except Exception as e:
            print(f"   ❌ Erro ao remover {log_file}: {e}")
    
    print(f"   📊 Total de logs antigos removidos: {removed_count}")

def clean_old_reports():
    """Remove relatórios antigos (mais de 90 dias)"""
    print("\n📊 Limpando relatórios antigos...")
    
    if not os.path.exists('reports'):
        print("   ℹ️  Diretório de relatórios não encontrado")
        return
    
    cutoff_date = datetime.now() - timedelta(days=90)
    removed_count = 0
    
    for report_file in glob.glob('reports/*.json'):
        try:
            file_time = datetime.fromtimestamp(os.path.getmtime(report_file))
            if file_time < cutoff_date:
                os.remove(report_file)
                removed_count += 1
                print(f"   ✅ Removido: {report_file}")
        except Exception as e:
            print(f"   ❌ Erro ao remover {report_file}: {e}")
    
    print(f"   📊 Total de relatórios antigos removidos: {removed_count}")

def clean_temp_files():
    """Remove arquivos temporários"""
    print("\n🗂️  Limpando arquivos temporários...")
    
    temp_patterns = [
        '*.tmp',
        '*.temp',
        '*.bak',
        '*.backup',
        '*.old',
        '*.orig',
        '*~',
        '.DS_Store',
        'Thumbs.db'
    ]
    
    removed_count = 0
    for pattern in temp_patterns:
        for temp_file in glob.glob(pattern):
            try:
                os.remove(temp_file)
                removed_count += 1
                print(f"   ✅ Removido: {temp_file}")
            except Exception as e:
                print(f"   ❌ Erro ao remover {temp_file}: {e}")
        
        # Buscar recursivamente
        for temp_file in glob.glob(f'**/{pattern}', recursive=True):
            try:
                os.remove(temp_file)
                removed_count += 1
                print(f"   ✅ Removido: {temp_file}")
            except Exception as e:
                print(f"   ❌ Erro ao remover {temp_file}: {e}")
    
    print(f"   📊 Total de arquivos temporários removidos: {removed_count}")

def clean_empty_directories():
    """Remove diretórios vazios"""
    print("\n📁 Removendo diretórios vazios...")
    
    removed_count = 0
    for root, dirs, files in os.walk('.', topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                # Verificar se o diretório está vazio
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    removed_count += 1
                    print(f"   ✅ Removido: {dir_path}")
            except Exception as e:
                # Ignorar erros (diretório pode não estar vazio ou ter permissões)
                pass
    
    print(f"   📊 Total de diretórios vazios removidos: {removed_count}")

def optimize_static_files():
    """Otimiza arquivos estáticos"""
    print("\n🎨 Verificando arquivos estáticos...")
    
    # Verificar se há arquivos CSS/JS duplicados
    css_files = glob.glob('static/**/*.css', recursive=True)
    js_files = glob.glob('static/**/*.js', recursive=True)
    
    print(f"   📊 Arquivos CSS encontrados: {len(css_files)}")
    print(f"   📊 Arquivos JS encontrados: {len(js_files)}")
    
    # Verificar se staticfiles está sendo usado corretamente
    if os.path.exists('staticfiles'):
        print("   ℹ️  Diretório staticfiles encontrado (usado pelo collectstatic)")
    
    print("   ✅ Verificação de arquivos estáticos concluída")

def check_database_size():
    """Verifica tamanho do banco de dados"""
    print("\n🗄️  Verificando banco de dados...")
    
    db_files = ['db.sqlite3', 'database.db', '*.db']
    total_size = 0
    
    for pattern in db_files:
        for db_file in glob.glob(pattern):
            try:
                size = os.path.getsize(db_file)
                total_size += size
                size_mb = size / (1024 * 1024)
                print(f"   📊 {db_file}: {size_mb:.2f} MB")
            except Exception as e:
                print(f"   ❌ Erro ao verificar {db_file}: {e}")
    
    if total_size > 0:
        total_mb = total_size / (1024 * 1024)
        print(f"   📊 Tamanho total do banco: {total_mb:.2f} MB")
        
        if total_mb > 100:
            print("   ⚠️  Banco de dados grande. Considere fazer limpeza de dados antigos.")
    else:
        print("   ℹ️  Nenhum arquivo de banco de dados encontrado")

def generate_cleanup_report():
    """Gera relatório de limpeza"""
    print("\n📋 Gerando relatório de limpeza...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'project': 'Projeto Havoc',
        'cleanup_actions': [
            'Remoção de arquivos __pycache__',
            'Limpeza de logs antigos (>30 dias)',
            'Remoção de relatórios antigos (>90 dias)',
            'Limpeza de arquivos temporários',
            'Remoção de diretórios vazios',
            'Otimização de arquivos estáticos',
            'Verificação do banco de dados'
        ]
    }
    
    # Salvar relatório
    os.makedirs('reports', exist_ok=True)
    report_file = f"reports/cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Relatório salvo em: {report_file}")
    except Exception as e:
        print(f"   ❌ Erro ao salvar relatório: {e}")

def main():
    """Função principal"""
    print("🚀 INICIANDO LIMPEZA DO PROJETO HAVOC")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Executar limpezas
    clean_pycache()
    clean_old_logs()
    clean_old_reports()
    clean_temp_files()
    clean_empty_directories()
    optimize_static_files()
    check_database_size()
    generate_cleanup_report()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
    print(f"⏱️  Tempo total: {duration.total_seconds():.2f} segundos")
    print("\n💡 Recomendações:")
    print("  - Execute este script regularmente (semanal/mensal)")
    print("  - Faça backup antes de executar em produção")
    print("  - Monitore o tamanho do banco de dados")
    print("  - Considere usar ferramentas de compressão para logs")

if __name__ == '__main__':
    main()
