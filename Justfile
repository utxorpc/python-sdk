init python="python3":
  {{ python }} -m venv .venv
  source .venv/bin/activate && pip install poetry
  source .venv/bin/activate && poetry lock
  source .venv/bin/activate && poetry install

format:
  source .venv/bin/activate && poetry run ruff format

lint:
  source .venv/bin/activate && poetry run ruff check
  source .venv/bin/activate && poetry run mypy utxorpc

build:
  source .venv/bin/activate && poetry build

init-examples:
  cd examples && python3 -m venv .venv
  cd examples && source .venv/bin/activate && pip install poetry
  cd examples && source .venv/bin/activate && poetry install

run-examples api_key:
  cd examples && source .venv/bin/activate && DMTR_API_KEY={{api_key}} poetry run python sync.py
  cd examples && source .venv/bin/activate && DMTR_API_KEY={{api_key}} poetry run python query.py
  cd examples && source .venv/bin/activate && DMTR_API_KEY={{api_key}} poetry run python submit.py
  cd examples && source .venv/bin/activate && DMTR_API_KEY={{api_key}} poetry run python watch.py

run-examples-local:
  cd examples && source .venv/bin/activate && poetry run python sync.py --local
  cd examples && source .venv/bin/activate && poetry run python query.py --local
  cd examples && source .venv/bin/activate && poetry run python submit.py
  cd examples && source .venv/bin/activate && poetry run python watch.py --local

clean:
  rm -rf .mypy_cache
  rm -rf .ruff_cache
  rm -rf .venv
  rm -rf __pycache__
  rm -rf utxorpc/__pycache__
  rm -rf utxorpc/generics/__pycache__
  rm -rf utxorpc/generics/clients/__pycache__
  rm -rf dist
