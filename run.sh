#!/usr/bin/env bash
# تشغيل SUT — البائع السوري من مجلد المشروع.
set -euo pipefail
cd "$(dirname "$0")"
exec python3 -m sut "$@"
