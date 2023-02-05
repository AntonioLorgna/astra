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



.PHONY: setup-app
setup-app: 
	sudo pip install --upgrade pip 
	python3 -m venv ./venv
	source ./venv/bin/activate && (cat requirements_app.txt && cat requirements_flower.txt && cat requirements_worker.txt) | xargs -n 1 pip install
	sudo chmod -R ugo=rwx ./data

.PHONY: setup
setup: 
	make setup-app
	make docker-build


.PHONY: start-app-supervizor
start-app-supervizor: 
	source ./venv/bin/activate && uvicorn astra.supervizor.supervizor:api.app --host 0.0.0.0 --port 8000
	
.PHONY: start-app-worker
start-app-worker: 
	source ./venv/bin/activate && celery -A astra.celery_worker.celery worker -P solo -l info 

.PHONY: start-app-flower
start-app-flower: 
	source ./venv/bin/activate && DEV=No celery -A astra.celery_worker.celery flower --host 0.0.0.0 --port=8010 --persistent=True --db=data/flower.db

.PHONY: start-app
start-app: start-app-worker start-app-supervizor start-app-flower



.PHONY: start
start: 
	make docker-start
	make -j 3 start-app



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