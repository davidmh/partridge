.PHONY: clean clean-test clean-pyc clean-build docs help sync-full
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT
OPEN := xdg-open $1 || open $1

# Virtual environment location
VIRTUAL_ENV = $(abspath .venv)
INSTALL_STAMP = $(VIRTUAL_ENV)/.install_stamp
UV := uv

# verbosity
V = 0

SYNC_0 = $(UV) sync --frozen -q
SYNC_1 = $(UV) sync --frozen
SYNC = $(SYNC_$(V))

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

dependency-graph.png: dependency-graph.dot
	dot -Tpng dependency-graph.dot -o dependency-graph.png

dot: dependency-graph.png

lint: $(INSTALL_STAMP) ## check style with ruff
	$(UV) run ruff check partridge tests
	$(UV) run ruff format --check partridge tests

format: $(INSTALL_STAMP) ## format code with ruff
	$(UV) run ruff check --fix partridge tests
	$(UV) run ruff format partridge tests

type-check: $(INSTALL_STAMP)
	$(UV) run mypy partridge --ignore-missing-imports

## run tests quickly with the default Python
test: sync-full lint type-check
	$(UV) run pytest

coverage: $(INSTALL_STAMP) ## check code coverage quickly with the default Python
	$(UV) run coverage run --source partridge -m pytest
	$(UV) run coverage report -m
	$(UV) run coverage html
	$(OPEN) htmlcov/index.html

docs: $(INSTALL_STAMP) ## generate Sphinx HTML documentation, including API docs
	rm -f docs/partridge.rst
	rm -f docs/modules.rst
	$(UV) run sphinx-apidoc -o docs/ partridge
	$(MAKE) -C docs clean SPHINXBUILD="uv run sphinx-build"
	$(MAKE) -C docs html SPHINXBUILD="uv run sphinx-build"
	$(OPEN) docs/_build/html/index.html

servedocs: docs ## compile the docs watching for changes
	$(UV) run watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html SPHINXBUILD="uv run sphinx-build"' -R -D .

release: dist ## package and upload a release
	$(UV) run twine upload dist/*

dist: clean $(INSTALL_STAMP) ## builds source and wheel package
	$(UV) build
	ls -l dist

install: clean $(INSTALL_STAMP) ## install the package to the active Python's site-packages
	$(UV) pip install .

sync-full: $(INSTALL_STAMP) ## install all the packages defined in the extras, useful for tests
	$(SYNC) --all-extras

$(VIRTUAL_ENV):
	$(UV) venv $@

$(INSTALL_STAMP): pyproject.toml uv.lock $(VIRTUAL_ENV)
	$(SYNC)
	touch $@
