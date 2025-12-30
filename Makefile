.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT
BROWSER := uv run python -c "$$BROWSER_PYSCRIPT"

help:
	@uv run python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts


clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm tests/fixtures/*.zip || true

dependency-graph.png:
	dot -Tpng dependency-graph.dot -o dependency-graph.png

dot: dependency-graph.png

lint: ## check style with ruff
	uv run ruff check partridge tests
	uv run ruff format --check partridge tests

format: ## format code with ruff
	uv run ruff check --fix partridge tests
	uv run ruff format partridge tests

type-check:
	uv run mypy partridge --ignore-missing-imports

## run tests quickly with the default Python
test: lint type-check
	uv run pytest

coverage: ## check code coverage quickly with the default Python
	uv run coverage run --source partridge -m pytest
	uv run coverage report -m
	uv run coverage html
	$(BROWSER) htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/partridge.rst
	rm -f docs/modules.rst
	uv run sphinx-apidoc -o docs/ partridge
	$(MAKE) -C docs clean SPHINXBUILD="uv run sphinx-build"
	$(MAKE) -C docs html SPHINXBUILD="uv run sphinx-build"
	$(BROWSER) docs/_build/html/index.html

servedocs: docs ## compile the docs watching for changes
	uv run watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html SPHINXBUILD="uv run sphinx-build"' -R -D .

release: dist ## package and upload a release
	uv run twine upload dist/*

dist: clean ## builds source and wheel package
	uv build
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	uv pip install .
