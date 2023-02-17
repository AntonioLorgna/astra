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
	sudo chmod -R ugo=rwx ./data

.PHONY: setup
setup: 
	make setup-app
	make docker-build


.PHONY: start-app-supervizor
start-app-supervizor: 
	source ./venv/bin/activate && DEV_PORT=7010 uvicorn astra.supervizor:app --host 0.0.0.0 --port 8000 --workers 1

.PHONY: start-app-sync
start-app-sync: 
	source ./venv/bin/activate && DEV_PORT=7020 python3 -m astra.sync 
	
.PHONY: start-app-worker
start-app-worker: 
	source ./venv/bin/activate && DEV_PORT=7030 celery -A astra.worker:app worker -P solo -l info 

.PHONY: start-app-ngrok
start-app-ngrok: 
	ngrok http 8080 > /dev/null &

.PHONY: start-app-api
start-app-api: 
	source ./venv/bin/activate && DEV_PORT=7040 uvicorn astra.api:app --host 0.0.0.0 --port 8080 --workers 1

.PHONY: start-app-flower
start-app-flower: 
	source ./venv/bin/activate && DEV=Yes celery -A astra.flower:app flower --host 0.0.0.0 --port=8010 --persistent=True --db=data/flower.db

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
	sudo rm -frd ./data/postgres
	sudo rm -frd ./data/redis
	sudo rm -frd ./data/flower.db