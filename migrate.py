import csv
import os
import subprocess

def exec(cmd, cwd='.'):
    subprocess.check_call(cmd, cwd=cwd)


def extract_reponames():
    fname = 'reponames.csv'
    repos = []
    github_repos = []
    with open(fname) as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        next(reader)
        for row in reader:
            old = '{}/{}'.format(row[0], row[1])
            new = '{}/{}'.format(row[2], row[3])
            if row[4].lower() == 'no':
                github_repos.append((old, new))
            else:
                repos.append((old, new))
    return repos, github_repos

gitdir = './git'
old = 'review.opencontrail.org'
new = 'gerrit.tungsten.io'
old_url = 'https://' + old
new_url = 'https://' + new
old_dir = gitdir + '/' + old
new_dir = gitdir + '/' + new

repos, github_repos = extract_reponames()
print(repos)

os.makedirs(old_dir, exist_ok=True)
os.makedirs(new_dir, exist_ok=True)

for repo in repos:
    try:
        exec(['git', '-C', repo[0], 'pull'], old_dir)
    except subprocess.CalledProcessError:
        exec(['git', 'clone', old_url + '/' + repo[0], repo[0]], old_dir)
