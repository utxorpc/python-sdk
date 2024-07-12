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

run-examples api_key:
  source .venv/bin/activate && DMTR_API_KEY={{api_key}} poetry run python examples/sync.py
  source .venv/bin/activate && DMTR_API_KEY={{api_key}} poetry run python examples/async.py

clean:
  rm -rf .mypy_cache
  rm -rf .ruff_cache
  rm -rf .venv
