#!/bin/bash
mydir=$(dirname "$0")
branch=${1:-master}
git checkout "origin/$branch"
git branch -D "$branch"
git checkout --orphan "$branch"
git add .
git commit -F $mydir/initial-commit-msg.txt
git replace "$branch" "origin/$branch"
