#!/bin/bash

trap exit INT
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_BASE_PATH="$(dirname "$(dirname "$SCRIPT_DIR")")"
WEB_APP_PATH="$PROJECT_BASE_PATH/web-app"

clean_webapp() {
    rm -rf "$WEB_APP_PATH/dist"*
}

install_webapp() {
    cd "$WEB_APP_PATH"
    npm install && npm run build
}


clean_webapp
install_webapp