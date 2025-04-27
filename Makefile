.PHONY: setup start stop restart logs ps status scale-workers clean rebuild help

# Variáveis
WORKER_COUNT ?= 3

help:
	@echo "Comandos disponíveis:"
	@echo "  make setup        - Configura o ambiente Docker e inicia os contêineres"
	@echo "  make start        - Inicia todos os contêineres"
	@echo "  make stop         - Para todos os contêineres"
	@echo "  make restart      - Reinicia todos os contêineres"
	@echo "  make logs         - Mostra logs de todos os contêineres"
	@echo "  make ps           - Lista contêineres em execução"
	@echo "  make status       - Verifica o status dos serviços"
	@echo "  make scale-workers - Escala o número de workers (ex: make scale-workers WORKER_COUNT=5)"
	@echo "  make clean        - Remove todos os contêineres e volumes"
	@echo "  make rebuild      - Reconstrói e reinicia os contêineres"

setup:
	python scripts/setup_docker.py

start:
	docker-compose up -d

stop:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

ps:
	docker-compose ps

status:
	python scripts/setup_docker.py --check-only

scale-workers:
	docker-compose up -d --scale worker=$(WORKER_COUNT)
	@echo "Workers escalados para $(WORKER_COUNT) instâncias"

clean:
	docker-compose down -v
	@echo "Contêineres e volumes removidos"

rebuild:
	docker-compose down
	docker-compose build
	docker-compose up -d
