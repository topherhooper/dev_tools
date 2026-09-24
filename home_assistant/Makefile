VENV := .venv
BIN := $(VENV)/bin
HA_IMAGE ?= ghcr.io/home-assistant/home-assistant:stable

.PHONY: install test lint format check-config deploy pull

$(BIN)/hactl: pyproject.toml
	python3 -m venv $(VENV)
	$(BIN)/pip install -q -e '.[dev]'

install: $(BIN)/hactl

test: install
	$(BIN)/pytest -q

lint: install
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .
	$(BIN)/yamllint -s .

format: install
	$(BIN)/ruff check --fix .
	$(BIN)/ruff format .

# Full HA validation of config/ using the official image (same as CI).
# Uses secrets.example.yaml unless you have a local secrets.yaml.
check-config:
	@test -f config/secrets.yaml || cp config/secrets.example.yaml config/secrets.yaml
	docker run --rm -v "$(CURDIR)/config:/config" $(HA_IMAGE) \
		python -m homeassistant --script check_config --config /config

deploy: install
	$(BIN)/hactl deploy

pull: install
	$(BIN)/hactl pull
