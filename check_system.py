#!/usr/bin/env python3
"""
Script de diagnóstico do sistema RAG Instagram.
Verifica status de todos os componentes e dependências.
"""

import sys
import subprocess
from pathlib import Path
import json


def check_mark(condition):
    """Retorna check mark ou X baseado na condição."""
    return "✅" if condition else "❌"


def print_section(title):
    """Imprime título de seção."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def check_python():
    """Verifica versão do Python."""
    print_section("Python")
    version = sys.version.split()[0]
    major, minor = map(int, version.split('.')[:2])
    is_ok = major == 3 and minor >= 12
    print(f"{check_mark(is_ok)} Python {version}")
    if not is_ok:
        print("   ⚠️  Recomendado: Python 3.12+")
    return is_ok


def check_command(cmd, name):
    """Verifica se comando está disponível."""
    try:
        result = subprocess.run(
            [cmd, '--version'], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        version = result.stdout.split('\n')[0] if result.returncode == 0 else "unknown"
        print(f"✅ {name}: {version}")
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"❌ {name}: não encontrado")
        return False


def check_ollama_service():
    """Verifica se Ollama está rodando."""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/version', timeout=2)
        if response.status_code == 200:
            print("✅ Serviço Ollama: rodando")
            return True
    except:
        pass
    print("❌ Serviço Ollama: não está rodando")
    print("   Execute: ollama serve")
    return False


def check_ollama_models():
    """Verifica modelos instalados no Ollama."""
    print_section("Modelos Ollama")
    
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("❌ Não foi possível listar modelos")
            return False
        
        models = result.stdout.strip().split('\n')[1:]  # Pula header
        
        required_models = {
            'mxbai-embed-large': False,
            'qwen2.5': False
        }
        
        for model_line in models:
            if not model_line.strip():
                continue
            model_name = model_line.split()[0].lower()
            for req_model in required_models:
                if req_model in model_name:
                    required_models[req_model] = True
                    print(f"✅ {model_line.split()[0]}")
        
        # Verifica modelos necessários
        all_ok = True
        if not required_models['mxbai-embed-large']:
            print("❌ mxbai-embed-large: não instalado")
            print("   Execute: ollama pull mxbai-embed-large")
            all_ok = False
        
        if not required_models['qwen2.5']:
            print("⚠️  qwen2.5: nenhuma versão encontrada")
            print("   Execute: ollama pull qwen2.5:3b")
        
        return all_ok
        
    except Exception as e:
        print(f"❌ Erro ao verificar modelos: {e}")
        return False


def check_python_packages():
    """Verifica pacotes Python necessários."""
    print_section("Pacotes Python")
    
    required = [
        'gradio',
        'chromadb', 
        'langchain',
        'ollama',
        'emoji'
    ]
    
    all_ok = True
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}: não instalado")
            all_ok = False
    
    if not all_ok:
        print("\n   Execute: uv sync")
    
    return all_ok


def check_data_files():
    """Verifica arquivos de dados."""
    print_section("Arquivos de Dados")
    
    data_dir = Path('data')
    
    if not data_dir.exists():
        print("❌ Pasta 'data/' não encontrada")
        return False
    
    json_files = list(data_dir.glob('*.json'))
    
    if not json_files:
        print("⚠️  Nenhum arquivo JSON em data/")
        return False
    
    print(f"✅ Encontrados {len(json_files)} arquivo(s) JSON:")
    
    total_posts = 0
    for json_file in json_files:
        try:
            with open(json_file) as f:
                posts = json.load(f)
                count = len(posts)
                total_posts += count
                print(f"   • {json_file.name}: {count} posts")
        except Exception as e:
            print(f"   ❌ {json_file.name}: erro ao ler ({e})")
    
    print(f"\n   Total: {total_posts} posts")
    return True


def check_chroma_db():
    """Verifica banco vetorial."""
    print_section("Banco Vetorial ChromaDB")
    
    chroma_dir = Path('chroma_db')
    
    if not chroma_dir.exists():
        print("⚠️  Banco não inicializado")
        print("   Será criado na primeira execução")
        return True
    
    # Tenta contar documentos
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(chroma_dir))
        collections = client.list_collections()
        
        if not collections:
            print("⚠️  Nenhuma coleção encontrada")
            return True
        
        for collection in collections:
            count = collection.count()
            print(f"✅ Coleção '{collection.name}': {count} documentos")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Não foi possível acessar banco: {e}")
        return True


def check_ports():
    """Verifica portas disponíveis."""
    print_section("Portas de Rede")
    
    import socket
    
    ports = {
        7860: "Gradio (padrão)",
        11434: "Ollama API"
    }
    
    all_ok = True
    for port, description in ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if port == 11434:
            # Ollama deve estar rodando
            if result == 0:
                print(f"✅ Porta {port} ({description}): em uso")
            else:
                print(f"❌ Porta {port} ({description}): livre (Ollama não está rodando)")
                all_ok = False
        else:
            # Gradio não deve estar rodando
            if result == 0:
                print(f"⚠️  Porta {port} ({description}): em uso")
            else:
                print(f"✅ Porta {port} ({description}): disponível")
    
    return all_ok


def print_summary(checks):
    """Imprime resumo dos checks."""
    print_section("Resumo")
    
    passed = sum(checks.values())
    total = len(checks)
    
    print(f"\nChecks aprovados: {passed}/{total}")
    print()
    
    if passed == total:
        print("🎉 Sistema pronto para uso!")
        print("\nPara iniciar:")
        print("  ./start.sh")
        print("  ou")
        print("  uv run python app.py")
    else:
        print("⚠️  Alguns componentes precisam de atenção")
        print("\nVerifique os itens marcados com ❌ acima")
        print("\nPara configuração completa, execute:")
        print("  ./setup.sh")


def main():
    """Função principal."""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   Instagram RAG - Verificação do Sistema                ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    checks = {
        'Python': check_python(),
        'UV': check_command('uv', 'uv'),
        'Ollama': check_command('ollama', 'Ollama'),
        'Ollama Service': check_ollama_service(),
        'Ollama Models': check_ollama_models(),
        'Python Packages': check_python_packages(),
        'Data Files': check_data_files(),
        'ChromaDB': check_chroma_db(),
        'Network Ports': check_ports()
    }
    
    print_summary(checks)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nVerificação cancelada.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro durante verificação: {e}")
        sys.exit(1)
