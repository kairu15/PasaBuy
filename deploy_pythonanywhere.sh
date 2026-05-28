#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/PasaBuy/Mysite}"
BRANCH="${BRANCH:-main}"
VENV_DIR="${VENV_DIR:-/home/PasaBuy/.virtualenvs/pasabuy}"
PA_USER="${PA_USER:-PasaBuy}"
PA_DOMAIN="${PA_DOMAIN:-PasaBuy.pythonanywhere.com}"

cd "$APP_DIR"

git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ -n "${API_TOKEN:-}" ]; then
    curl -fsS -X POST \
        -H "Authorization: Token ${API_TOKEN}" \
        "https://www.pythonanywhere.com/api/v0/user/${PA_USER}/webapps/${PA_DOMAIN}/reload/"
else
    echo "API_TOKEN is not available, so reload the web app manually from the PythonAnywhere Web tab."
fi
