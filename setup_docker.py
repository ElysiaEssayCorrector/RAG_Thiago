#!/usr/bin/env python
"""
Script para configurar e iniciar o ambiente Docker do sistema Elysia
"""
import os
import subprocess
import time
import sys

def print_colored(message, color='green'):
    """Imprime mensagem colorida no console"""
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'purple': '\033[95m',
        'end': '\033[0m'
    }
    
    print(f"{colors.get(color, '')}{message}{colors['end']}")

def run_command(command, cwd=None):
    """Executa um comando shell e retorna o resultado"""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, 
                               capture_output=True, cwd=cwd)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_docker_installed():
    """Verifica se o Docker está instalado"""
    success, output = run_command("docker --version")
    if not success:
        print_colored("Docker não encontrado. Por favor instale o Docker Desktop primeiro.", 'red')
        return False
    
    print_colored(f"Docker encontrado: {output.strip()}")
    return True

def check_docker_compose_installed():
    """Verifica se o Docker Compose está instalado"""
    success, output = run_command("docker-compose --version")
    if not success:
        print_colored("Docker Compose não encontrado. Verifique sua instalação do Docker.", 'red')
        return False
    
    print_colored(f"Docker Compose encontrado: {output.strip()}")
    return True

def check_env_file():
    """Verifica se o arquivo .env existe e atualiza a chave de API OpenAI se necessário"""
    if not os.path.exists(".env"):
        print_colored("Arquivo .env não encontrado. Criando...", 'yellow')
        with open(".env.example", "r") as example:
            with open(".env", "w") as env:
                env.write(example.read())
    
    # Verificar se a chave OpenAI está configurada
    with open(".env", "r") as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if line.startswith("OPENAI_API_KEY=") and "sua-chave-openai" in line:
            api_key = input("\nDigite sua chave de API OpenAI (comece com 'sk-'): ")
            if api_key and api_key.startswith("sk-"):
                lines[i] = f"OPENAI_API_KEY={api_key}\n"
                with open(".env", "w") as f:
                    f.writelines(lines)
                print_colored("Chave de API OpenAI atualizada com sucesso!", 'green')
            else:
                print_colored("Chave de API inválida. A chave deve começar com 'sk-'", 'yellow')
                print_colored("Você pode atualizar a chave manualmente no arquivo .env mais tarde.", 'yellow')
            break

def build_docker_containers():
    """Constrói os containers Docker"""
    print_colored("\n=== Construindo containers... ===", 'blue')
    success, output = run_command("docker-compose build")
    if not success:
        print_colored(f"Erro ao construir containers: {output}", 'red')
        return False
    
    print_colored("Containers construídos com sucesso!", 'green')
    return True

def start_docker_containers():
    """Inicia os containers Docker"""
    print_colored("\n=== Iniciando containers... ===", 'blue')
    success, output = run_command("docker-compose up -d")
    if not success:
        print_colored(f"Erro ao iniciar containers: {output}", 'red')
        return False
    
    print_colored("Containers iniciados com sucesso!", 'green')
    return True

def initialize_database():
    """Inicializa o banco de dados MongoDB"""
    print_colored("\n=== Aguardando inicialização do MongoDB... ===", 'blue')
    # Esperar MongoDB iniciar
    time.sleep(5)
    
    print_colored("Executando script de inicialização do MongoDB...", 'purple')
    
    # Verificar se existe um script para inicializar o MongoDB
    if os.path.exists("scripts/init_mongodb.py"):
        success, output = run_command("docker-compose exec -T api python scripts/init_mongodb.py")
        if not success:
            print_colored(f"Aviso: Não foi possível inicializar o banco de dados: {output}", 'yellow')
            print_colored("Você pode inicializar o banco manualmente depois.", 'yellow')
        else:
            print_colored("Banco de dados inicializado com sucesso!", 'green')
    else:
        print_colored("Script de inicialização do MongoDB não encontrado. O banco será inicializado automaticamente.", 'yellow')

def main():
    """Função principal para configurar o ambiente Docker"""
    print_colored("\n====================================================", 'blue')
    print_colored("      Configuração do Ambiente Elysia RAG", 'purple')
    print_colored("====================================================\n", 'blue')
    
    # Verificar pré-requisitos
    if not check_docker_installed() or not check_docker_compose_installed():
        sys.exit(1)
    
    # Verificar arquivo .env
    check_env_file()
    
    # Construir containers
    if not build_docker_containers():
        sys.exit(1)
    
    # Iniciar containers
    if not start_docker_containers():
        sys.exit(1)
    
    # Inicializar banco de dados
    initialize_database()
    
    print_colored("\n====================================================", 'blue')
    print_colored("      Sistema Elysia RAG inicializado!", 'purple')
    print_colored("====================================================", 'blue')
    print_colored("\nServiços disponíveis:", 'green')
    print_colored("  - API: http://localhost:8000", 'blue')
    print_colored("  - MongoDB Express: http://localhost:8081", 'blue')
    print_colored("  - MinIO Console: http://localhost:9001", 'blue')
    
    print_colored("\nPara interromper os serviços: docker-compose down", 'yellow')
    print_colored("Para ver os logs: docker-compose logs -f\n", 'yellow')

if __name__ == "__main__":
    main()
