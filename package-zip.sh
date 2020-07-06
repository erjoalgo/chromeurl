#!/bin/bash -x

set -euo pipefail

cd "$( dirname "${BASH_SOURCE[0]}" )"

rm -f chrome-current-url*.zip
ZIP=chrome-current-url-$(date -I).zip
cd chrome
zip -r ${ZIP} *
mv ${ZIP} ..
