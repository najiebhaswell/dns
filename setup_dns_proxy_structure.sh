#!/bin/bash
set -e

# Root project dir (current path)
ROOT_DIR="$(pwd)"

# Helper to create folder+__init__.py
create_py_folder() {
  mkdir -p "$1"
  touch "$1/__init__.py"
}

# 1. Main package and subfolders
create_py_folder "$ROOT_DIR/dns_proxy"
create_py_folder "$ROOT_DIR/dns_proxy/server"
create_py_folder "$ROOT_DIR/dns_proxy/blacklist_updater"
create_py_folder "$ROOT_DIR/dns_proxy/log_parser"

# 2. Touch all module .py files
touch "$ROOT_DIR/dns_proxy/server/config.py"
touch "$ROOT_DIR/dns_proxy/server/acl.py"
touch "$ROOT_DIR/dns_proxy/server/resolver.py"
touch "$ROOT_DIR/dns_proxy/server/handler.py"
touch "$ROOT_DIR/dns_proxy/server/main.py"

touch "$ROOT_DIR/dns_proxy/blacklist_updater/config.py"
touch "$ROOT_DIR/dns_proxy/blacklist_updater/database.py"
touch "$ROOT_DIR/dns_proxy/blacklist_updater/fetcher.py"
touch "$ROOT_DIR/dns_proxy/blacklist_updater/validator.py"
touch "$ROOT_DIR/dns_proxy/blacklist_updater/updater.py"

touch "$ROOT_DIR/dns_proxy/log_parser/config.py"
touch "$ROOT_DIR/dns_proxy/log_parser/regex_patterns.py"
touch "$ROOT_DIR/dns_proxy/log_parser/metrics.py"
touch "$ROOT_DIR/dns_proxy/log_parser/parser.py"
touch "$ROOT_DIR/dns_proxy/log_parser/api_server.py"
touch "$ROOT_DIR/dns_proxy/log_parser/main.py"

# 3. Root level scripts & docs
touch "$ROOT_DIR/main.py"
touch "$ROOT_DIR/update_blacklist_db.py"
touch "$ROOT_DIR/parse_dns_log.py"
touch "$ROOT_DIR/requirements.txt"
touch "$ROOT_DIR/README.md"

echo "DNS Proxy Suite structure created."
echo "Silakan salin/isi file .py sesuai template."
