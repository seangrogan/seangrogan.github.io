#!/bin/sh
# Runs inside the newsfeed container on the home server (see scripts/compose.yaml).
#
# Every INTERVAL_HOURS it gets the latest copy of the site from GitHub, fetches
# the newsletter feeds, and pushes _data/posts.yml back if the posts changed.
# That push makes GitHub rebuild and publish the site.
set -u

cd /repo
git config user.name  "camp-grogie newsfeed"
git config user.email "newsfeed@camp-grogie.local"
# Set the address every start, so a new token takes effect on restart.
git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${REPO}.git"

while true; do
  echo "$(date '+%Y-%m-%d %H:%M') checking the feeds"
  if git fetch -q origin "$BRANCH" && git reset -q --hard FETCH_HEAD; then
    python scripts/fetch_posts.py
    if [ -n "$(git status --porcelain _data/posts.yml)" ]; then
      git add _data/posts.yml
      git commit -q -m "Update newsletter posts"
      if git push -q origin "HEAD:$BRANCH"; then
        echo "pushed the new posts to $BRANCH"
      else
        echo "could not push to GitHub (has the token expired?)"
      fi
    else
      echo "no new posts"
    fi
  else
    echo "could not reach GitHub (has the token expired?)"
  fi
  echo "next check in ${INTERVAL_HOURS} hours"
  sleep $((INTERVAL_HOURS * 3600))
done
