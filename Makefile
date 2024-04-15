test:
	TEST_MODE="1" pytest

format:
	isort --profile black . && black . && flake8

qa:
	isort --check . && black --check . && flake8

mypy:
	mypy . --config-file .mypy.ini --ignore-missing-imports

build:
	docker build -t drm:latest .