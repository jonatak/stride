# Colors
_CYAN=\033[0;36m
_END=\033[0m

.check-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo >&2 "❌ 'uv' is not installed. Please install it from https://github.com/astral-sh/uv"; \
		exit 1; \
	}

welcome: venv sync-dev		## setup the project for dev
	@echo "You are now ready to go, run source ./.venv/bin/activate"

venv: .check-uv  		## initialise venv
	@uv venv --clear

sync-dev: .check-uv 	## install dependencies dev included
	@uv sync

check:					## check for code issues
	@uv run ruff check

fmt:					## format code
	@uv run ruff format

test:					## run test
	@uv run pytest -v -s --cov=stargazer

help:					## display this help screen
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(_CYAN)%-30s$(_END) %s\n", $$1, $$2}'
