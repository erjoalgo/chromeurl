#!/bin/bash -x

set -euo pipefail

ZIP=chrome-current-url.zip

cd chrome
zip -r ${ZIP} *
mv ${ZIP} ..
