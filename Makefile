# Makefile
SHELL := /bin/bash

DOCKER_SERVICES := postgres pgadmin redis redisinsight

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf `find . -type d -name '*.egg-info' `
	rm -rf `find . -type d -name 'pip-wheel-metadata' `
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build


.PHONY: setup-frontend
setup-frontend: 
	cd frontend && \
	npm install

.PHONY: setup-app
setup-app: 
	sudo echo ""
	python3 -m venv ./venv
	source ./venv/bin/activate && \
	pip install --upgrade pip  && \
	(cat requirements_app.txt && cat requirements_flower.txt && cat requirements_worker.txt && cat requirements_api.txt) | xargs -n 1 pip install
	make setup-frontend
	sudo chmod -R ugo=rwx ./data

.PHONY: setup
setup: 
	make setup-app
	make docker-build


.PHONY: start-app-supervizor
start-app-supervizor: 
	exec > >(trap "" INT TERM; sed 's/^/SUPERV: /') &&\
	source ./venv/bin/activate && DEV_PORT=7010 uvicorn astra.supervizor:app --host 0.0.0.0 --port 8000 --workers 1 --reload --reload-dir ./astra/supervizor

.PHONY: start-app-sync
start-app-sync: 
	exec > >(trap "" INT TERM; sed 's/^/SYNC: /') &&\
	source ./venv/bin/activate && DEV_PORT=7020 python3 -m astra.sync 
	
.PHONY: start-app-worker
start-app-worker: 
	exec > >(trap "" INT TERM; sed 's/^/WORKER: /') &&\
	source ./venv/bin/activate && celery -A astra.worker:app worker -P gevent -c 1 -l info 

.PHONY: start-app-ngrok
start-app-ngrok: 
	exec > >(trap "" INT TERM; sed 's/^/NGROK: /') &&\
	ngrok http 8080 > /dev/null &

.PHONY: start-app-api
start-app-api: 
	exec > >(trap "" INT TERM; sed 's/^/API: /') &&\
	source ./venv/bin/activate && DEV_PORT=7040 uvicorn astra.api:app --host 0.0.0.0 --port 8080 --workers 1 --reload --reload-dir ./astra/api

.PHONY: start-app-flower
start-app-flower: 
	exec > >(trap "" INT TERM; sed 's/^/FLOWER: /') &&\
	source ./venv/bin/activate && celery -A astra.flower:app flower --host 0.0.0.0 --port=8010 --persistent=True --db=data/flower.db

.PHONY: start-app
start-app: start-app-worker start-app-supervizor start-app-sync start-app-flower start-app-api

.PHONY: start-frontend
start-frontend: 
	cd frontend && \
	npm run dev



.PHONY: start
start: 
	make start-app-ngrok
	make docker-start
	make -j 5 start-app



.PHONY: docker-build
docker-build:
	docker compose build $(DOCKER_SERVICES)

.PHONY: docker-start
docker-start:
	exec > >(trap "" INT TERM; sed 's/^/DOCKER: /') &&\
	docker compose up $(DOCKER_SERVICES) -d

.PHONY: docker-stop
docker-stop:
	docker compose stop $(DOCKER_SERVICES)

.PHONY: docker-down
docker-down:
	docker compose down $(DOCKER_SERVICES)

.PHONY: docker-status
docker-status:
	docker compose ps


.PHONY: db-drop
db-drop:
	sudo echo ""
	make docker-stop
	sudo rm -frd ./data/postgres
	sudo rm -frd ./data/redis
	sudo rm -frd ./data/flower.db
	sudo rm -frd ./data/bot
	sudo rm -frd ./data/media