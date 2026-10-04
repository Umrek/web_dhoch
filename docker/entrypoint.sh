#!/bin/sh
# Container entrypoint. Schema changes are NOT applied here: run the one-shot release step
#   python manage.py migrate --noinput && python manage.py createcachetable && python manage.py sync_roles
# (the compose "migrate" service does this) so that several app replicas never race on migrations.
set -eu
exec "$@"
