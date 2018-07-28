#!/bin/bash

set -euo pipefail

LOG_FILE=/tmp/chrome-urls.log

date >> ${LOG_FILE}
cat >> ${LOG_FILE}

cat <<EOF
{"status": "completed"}
EOF

