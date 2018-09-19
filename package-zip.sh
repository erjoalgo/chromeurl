#!/bin/bash -x

set -euo pipefail

rm chrome-current-url*.zip
ZIP=chrome-current-url-$(date -I).zip
cd chrome
zip -r ${ZIP} *
mv ${ZIP} ..
