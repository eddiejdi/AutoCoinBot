#!/usr/bin/env bash
# Helper to create venv, install deps, activate and run tests
set -euo pipefail

VENV_DIR=venv
PYTHON=${PYTHON:-python3}

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtualenv in $VENV_DIR..."
  $PYTHON -m venv "$VENV_DIR"
fi

echo "Activating virtualenv..."
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

echo "Installing dependencies (requirements.txt)..."
pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt || true
fi
pip install pytest python-dotenv selenium || true

APP_ENV=${APP_ENV:-dev}
RUN_SELENIUM=0

# support: --selenium flag or env RUN_SELENIUM=1
for arg in "$@"; do
  if [ "$arg" = "--selenium" ]; then
    RUN_SELENIUM=1
  else
    # collect args to forward to pytest (except --selenium)
    TEST_ARGS+=("$arg")
  fi
done

if [ "${RUN_SELENIUM:-0}" != "0" ] || [ "${RUN_SELENIUM_ENV:-0}" = "1" ] || [ "${RUN_SELENIUM}" = "1" ]; then
  echo "Running full suite including Selenium visual tests (APP_ENV=$APP_ENV)"
  APP_ENV="$APP_ENV" pytest "${TEST_ARGS[@]}"
else
  echo "Running tests (excluding heavy Selenium visual tests) with APP_ENV=$APP_ENV"
    # first run a compile-time import check to catch SyntaxError/IndentationError
    echo "Running python compile check (compileall) to catch import-time errors..."
    python -m compileall -q .

    # run all tests but skip visual validation marker/file unless user requested it
    APP_ENV="$APP_ENV" pytest -k "not visual_validation" "${TEST_ARGS[@]}"
fi

deactivate || true

echo "Tests finished."
