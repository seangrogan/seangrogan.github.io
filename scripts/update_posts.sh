#!/bin/sh
# Runs inside the newsfeed container on the home server (see scripts/compose.yaml).
#
# Every INTERVAL_HOURS it gets the latest copy of the site from GitHub, fetches
# the newsletter feeds, and pushes _data/posts.yml back if the posts changed.
# That push makes GitHub rebuild and publish the site.
#
# If checks keep failing (ALERT_AFTER in a row), it sends one Telegram alert,
# and another when things work again. Each fully successful check is recorded
# for the Docker health check (scripts/healthcheck.sh).
set -u
ALERT_AFTER="${ALERT_AFTER:-2}"
NAME="seangrogan.github.io newsfeed on camp-grogie"

cd /repo
git config user.name  "camp-grogie newsfeed"
git config user.email "newsfeed@camp-grogie.local"
# Set the address every start, so a new token takes effect on restart.
git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${REPO}.git"

fails=0
alerted=0

went_ok() {
  date +%s > /tmp/newsfeed_last_ok
  if [ "$alerted" -eq 1 ]; then
    python scripts/notify.py "✅ $NAME is working again."
  fi
  fails=0
  alerted=0
}

went_wrong() {
  echo "problem: $1"
  fails=$((fails + 1))
  if [ "$fails" -ge "$ALERT_AFTER" ] && [ "$alerted" -eq 0 ]; then
    python scripts/notify.py "⚠️ $NAME: $1 ($fails checks in a row). See the container log in Dockhand."
    alerted=1
  fi
}

while true; do
  echo "$(date '+%Y-%m-%d %H:%M') checking the feeds"
  if git fetch -q origin "$BRANCH" && git reset -q --hard FETCH_HEAD; then
    problem=""
    python scripts/fetch_posts.py
    result=$?
    if [ "$result" -eq 2 ]; then
      problem="some newsletters couldn't be fetched"
    elif [ "$result" -ne 0 ]; then
      problem="the feed script stopped with an error"
    fi
    if [ -n "$(git status --porcelain _data/posts.yml)" ]; then
      git add _data/posts.yml
      git commit -q -m "Update newsletter posts"
      if git push -q origin "HEAD:$BRANCH"; then
        echo "pushed the new posts to $BRANCH"
      else
        problem="could not push to GitHub (has the token been revoked?)"
      fi
    else
      echo "no new posts"
    fi
    if [ -n "$problem" ]; then went_wrong "$problem"; else went_ok; fi
  else
    went_wrong "could not reach GitHub (has the token been revoked?)"
  fi
  echo "next check in ${INTERVAL_HOURS} hours"
  sleep $((INTERVAL_HOURS * 3600))
done
