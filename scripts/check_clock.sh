#!/usr/bin/env bash
# Fail if any code asks the real clock for the time instead of config.now().
#
# Python and notebooks: datetime.now(), datetime.utcnow(), datetime.today(),
# date.today(), pandas Timestamp.now(). SQL: now(), CURRENT_DATE,
# CURRENT_TIMESTAMP, LOCALTIMESTAMP and the *_timestamp() functions; SQL takes
# the clock as a parameter (:'now') instead.
# config.py is the one file allowed to define the clock.
#
# Run from anywhere in the repo: scripts/check_clock.sh
# Checks tracked and new (untracked, not ignored) files.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

status=0

py_hits=$(git grep --untracked -n -E \
  'datetime\.(now|utcnow|today)\(|date\.today\(|Timestamp\.now\(' \
  -- '*.py' '*.ipynb' ':!config.py')
if [ -n "$py_hits" ]; then
  echo "Real clock used in Python (use config.now() instead):"
  echo "$py_hits"
  status=1
fi

sql_hits=$(git grep --untracked -n -i -E \
  '(^|[^a-z_.])now\(\)|current_date|current_timestamp|localtimestamp|(clock|statement|transaction)_timestamp\(' \
  -- '*.sql')
if [ -n "$sql_hits" ]; then
  echo "Real clock used in SQL (pass the clock in, e.g. :'now'):"
  echo "$sql_hits"
  status=1
fi

if [ "$status" -eq 0 ]; then
  echo "clock check passed: only config.py defines the time"
fi
exit "$status"
