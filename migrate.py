import csv
import os
import subprocess
import yaml
import pathlib
import pygit2
import jinja2
from jinja2 import Template


cfg = {}


def read_yaml(path):
    with open(path, 'r') as yaml_file:
        obj = yaml.load(yaml_file)
        return obj


def render_template(tpl_path, context):
    with open(tpl_path, 'r') as tpl_file:
        tpl = tpl_file.read()
    template = Template(tpl)
    out = template.render(context)
    return out


def write_template(tpl_path, dest_path, context):
    out = render_template(tpl_path, context)
    with open(dest_path, 'w') as dest_file:
        dest_file.write(out)


def read_config():
    new_cfg = read_yaml('./config.yaml')
    cfg.update(new_cfg)


def exec(cmd, cwd='.'):
    print('executing:', cmd, 'in:', cwd)
    subprocess.check_call(cmd, cwd=cwd)


def get_active_branches():
    branches = set()
    pipelines = read_yaml(cfg['pipelines_file_path'])
    for pipeline in pipelines:
        p = pipeline['pipeline']
        if p.get('name', None) in ['check', 'gate']:
            for event in p['trigger'].get('gerrit', []):
                for branch in event.get('branch', []):
                    branches.add(branch[1:-1])
    return list(branches)


def extract_reponames():
    fname = cfg['repos_csv_file_path']
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


def clone_repos(repos):
    gitdir = './git'
    old = cfg['old_hostname']
    new = cfg['new_hostname']
    old_url = 'https://' + old
    new_url = 'https://' + new
    old_dir = gitdir + '/' + old
    new_dir = gitdir + '/' + new
    os.makedirs(old_dir, exist_ok=True)
    for repo in repos:
        repo_path = get_old_repo_path(repo[0])
        repo_path = pathlib.Path(repo_path)
        os.makedirs(str(repo_path.parent), exist_ok=True)
        try:
            exec(['git', '-C', str(repo_path), 'fetch', '--all'])
            exec(['git', '-C', str(repo_path), 'pull'])
        except subprocess.CalledProcessError:
            exec(['git', 'clone', old_url + '/' + repo[0], repo[0]], old_dir)


def get_old_repo_path(repo):
    gitdir = pathlib.Path(cfg['gitdir'])
    old = cfg['old_hostname']
    new = cfg['new_hostname']
    old_dir = gitdir / old
    new_dir = gitdir / new
    repo_path = old_dir / repo
    return str(repo_path)


def branch_in_repo(repo, branch):
    path = get_old_repo_path(repo)
    print(path)
    r = pygit2.Repository(path)
    refs = list(r.references)
    result = 'refs/remotes/origin/' + branch in r.references
    return result


def squash(repo, branch):
    cmd = [os.getcwd() + '/squash.sh', branch]
    exec(cmd, get_old_repo_path(repo))


def is_branch_migrated(repo, branch):
    skipped = branch in cfg['skip_branches'].get(repo, [])
    inrepo = branch_in_repo(repo, branch)
    return inrepo and not skipped


def squash_all(repos, branches):
    for old_repo, new_repo in repos:
        for branch in branches:
            if is_branch_migrated(old_repo, branch):
                squash(old_repo, branch)
            else:
                print('branch', branch, 'not in repo', old_repo)


def sed_dir(pattern_from, pattern_to, path):
    cmd = ['bash', '-c', 'find . -not -path \'*/\.git*\' -type f -print0 | xargs -0 -n1 sed -i -s \'s:{}:{}:g\''.format(pattern_from, pattern_to)]
    print(cmd)
    exec(cmd, cwd=path)


def patch(repo, branch, repos):
    repo_path = get_old_repo_path(repo)
    patch_path = os.getcwd() + '/patches/' + repo.split('/')[-1] + '.patch'
    print(patch_path)
    if os.path.exists(patch_path):
        print('Applying patch:', patch_path)
        exec(['git', 'apply', patch_path], repo_path)
    for old, new in repos:
        sed_dir(old, new, repo_path)
    pass


def push():
    pass


def main():
    read_config()
    repos, github_repos = extract_reponames()
    print(repos)
    print(github_repos)
    active_branches = get_active_branches()
    print(active_branches)
    if cfg['clone']:
        clone_repos(repos)
    clone_repos([('Juniper/contrail-project-config', '')])
    #squash_all(repos, active_branches)
    repos_fqdn = [(cfg['old_hostname'] + '/' + r[0], cfg['new_hostname'] + '/' + r[1]) for r in repos]
    github_repos_fqdn = [('github.com/' + r[0], cfg['new_hostname'] + '/' + r[1]) for r in github_repos]
    sr = sorted(repos + github_repos + repos_fqdn + github_repos_fqdn, key=lambda x: len(x[0]), reverse=True)
    print(sr)
    patch('Juniper/contrail-project-config', 'master', sr)


if __name__ == '__main__':
    main()
