#!/bin/bash
set -x
mydir=$(dirname "$0")
branch=${1:-master}
# remove replacements from previous runs
git for-each-ref --format='delete %(refname)' refs/replace | git update-ref --stdin
git checkout -f "origin/$branch"
git branch -D "$branch"
git checkout --orphan "$branch"
git add .
git commit -F $mydir/initial-commit-msg.txt
git replace "$branch" "origin/$branch"
