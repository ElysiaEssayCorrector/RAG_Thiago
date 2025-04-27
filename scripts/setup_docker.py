#!/usr/bin/env python
import os
import sys
import subprocess
import time
import requests
from pathlib import Path

# Defina o diretório raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent

def print_step(message):
    """Imprime uma mensagem de etapa formatada"""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80 + "\n")

def run_command(command, cwd=ROOT_DIR):
    """Executa um comando shell e imprime a saída"""
    print(f"Executando: {command}")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        cwd=cwd
    )
    
    for line in process.stdout:
        print(line.strip())
    
    process.wait()
    if process.returncode != 0:
        print(f"Erro ao executar o comando: {command}")
        return False
    return True

def check_docker():
    """Verifica se o Docker e Docker Compose estão instalados"""
    print_step("Verificando instalação do Docker")
    
    # Verificar Docker
    if not run_command("docker --version"):
        print("Docker não está instalado. Por favor, instale o Docker e tente novamente.")
        sys.exit(1)
    
    # Verificar Docker Compose
    if not run_command("docker-compose --version"):
        print("Docker Compose não está instalado. Por favor, instale o Docker Compose e tente novamente.")
        sys.exit(1)
    
    print("✅ Docker e Docker Compose estão instalados corretamente.")

def create_directories():
    """Cria diretórios necessários para volumes Docker"""
    print_step("Criando diretórios para volumes")
    
    directories = [
        ROOT_DIR / "data" / "mongodb",
        ROOT_DIR / "data" / "redis",
        ROOT_DIR / "data" / "elasticsearch",
        ROOT_DIR / "data" / "minio",
        ROOT_DIR / "logs"
    ]
    
    for directory in directories:
        if not directory.exists():
            print(f"Criando diretório: {directory}")
            directory.mkdir(parents=True, exist_ok=True)
    
    print("✅ Diretórios criados com sucesso.")

def build_containers():
    """Constrói as imagens Docker"""
    print_step("Construindo imagens Docker")
    
    if not run_command("docker-compose build"):
        print("Erro ao construir as imagens Docker.")
        sys.exit(1)
    
    print("✅ Imagens Docker construídas com sucesso.")

def start_containers():
    """Inicia os contêineres Docker"""
    print_step("Iniciando contêineres Docker")
    
    if not run_command("docker-compose up -d"):
        print("Erro ao iniciar os contêineres Docker.")
        sys.exit(1)
    
    print("✅ Contêineres Docker iniciados com sucesso.")

def check_services():
    """Verifica se os serviços estão funcionando corretamente"""
    print_step("Verificando serviços")
    
    services = {
        "MongoDB": "http://localhost:27017",
        "Redis": "http://localhost:6379",
        "Elasticsearch": "http://localhost:9200",
        "MinIO Console": "http://localhost:9001",
        "API Elysia": "http://localhost:8000"
    }
    
    max_attempts = 30
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        
        all_services_up = True
        
        for service_name, url in services.items():
            try:
                if "mongodb" in url or "redis" in url:
                    # Para MongoDB e Redis, verificamos se o contêiner está em execução
                    service_id = service_name.lower().split()[0]
                    result = subprocess.run(
                        f"docker ps --filter name=rag_thiago_{service_id} --format '{{{{.Status}}}}'",
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    
                    if "Up" in result.stdout:
                        print(f"✅ {service_name} está em execução.")
                    else:
                        print(f"❌ {service_name} não está em execução.")
                        all_services_up = False
                else:
                    # Para outros serviços, verificamos se o endpoint está respondendo
                    response = requests.get(url, timeout=2)
                    if response.status_code < 400:
                        print(f"✅ {service_name} está respondendo em {url}")
                    else:
                        print(f"❌ {service_name} retornou status {response.status_code}")
                        all_services_up = False
            
            except (requests.RequestException, subprocess.SubprocessError) as e:
                print(f"❌ {service_name} não está disponível ainda: {str(e)}")
                all_services_up = False
        
        if all_services_up:
            print("\n✅ Todos os serviços estão funcionando corretamente!")
            return True
        
        print(f"\nAguardando serviços iniciarem... (tentativa {attempts}/{max_attempts})")
        time.sleep(5)
    
    print("\n⚠️ Nem todos os serviços estão funcionando após várias tentativas.")
    print("Verifique os logs com 'docker-compose logs' para mais informações.")
    return False

def initialize_database():
    """Inicializa o banco de dados com dados de exemplo"""
    print_step("Inicializando banco de dados")
    
    # Executar script de inicialização dentro do contêiner da API
    if not run_command("docker-compose exec -T api python scripts/init_mongodb.py"):
        print("⚠️ Erro ao inicializar o banco de dados.")
        print("Isso pode acontecer se a OpenAI API key não estiver configurada corretamente.")
        print("Você pode inicializar manualmente mais tarde com:")
        print("  docker-compose exec api python scripts/init_mongodb.py")
    else:
        print("✅ Banco de dados inicializado com sucesso.")

def main():
    """Função principal"""
    print_step("CONFIGURAÇÃO DO AMBIENTE DOCKER PARA ELYSIA")
    
    check_docker()
    create_directories()
    build_containers()
    start_containers()
    
    if check_services():
        initialize_database()
    
    print_step("CONFIGURAÇÃO CONCLUÍDA")
    print("""
Serviços disponíveis:
- API Elysia: http://localhost:8000
- MongoDB Express (admin): http://localhost:8081
- MinIO Console: http://localhost:9001

Comandos úteis:
- Ver logs: docker-compose logs -f
- Parar serviços: docker-compose down
- Reiniciar serviços: docker-compose restart
- Escalar workers: docker-compose up -d --scale worker=3
    """)

if __name__ == "__main__":
    main()
