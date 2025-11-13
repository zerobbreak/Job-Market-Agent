#!/bin/sh
set -e

# Replace environment variables in env-config.js
# Explicitly list variables to prevent unintended substitutions
envsubst '${VITE_OAUTH_PROVIDER_URL} ${VITE_JOB_MARKET_API_URL} ${VITE_SESSION_SECRET} ${VITE_MODE}' \
  < /usr/share/nginx/html/env-config.js \
  > /usr/share/nginx/html/env-config.generated.js

# Rename to replace the template
mv /usr/share/nginx/html/env-config.generated.js /usr/share/nginx/html/env-config.js

echo "Environment configuration loaded:"
cat /usr/share/nginx/html/env-config.js

# Start nginx
exec "$@"
