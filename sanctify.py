#!/usr/bin/env python3
# Copyright (c) 2016 Heikki Hokkanen <hoxu at users.sf.net>

import argparse
import os
import subprocess

def read_wrappers_from_stream(f):
    inside = False
    result = []
    for line in f:
        stripped = line.lstrip('# ').rstrip('\n')
        if not inside and stripped == '<sanctify>':
            inside = True
            continue
        elif inside and stripped == '</sanctify>':
            break
        if inside:
            result.append(stripped.split())
    return result

def unwrap_job(sanctify_binary, jobpath, wrappers):
    result = []
    for wrapper in wrappers:
        result.extend([sanctify_binary, 'wrapper'])
        result.extend(wrapper)
        result.append('--')

    result.append(jobpath)
    return result

def run(job, arguments):
    import inspect
    sanctify_binary = os.path.abspath(inspect.getfile(inspect.currentframe()))

    with open(job) as f:
        wrappers = read_wrappers_from_stream(f)

    jobpath = os.path.abspath(job)
    unwrapped = unwrap_job(sanctify_binary, jobpath, wrappers)
    params = list(unwrapped)
    params.extend(arguments)

    project = os.path.dirname(jobpath)
    project_name = os.path.basename(project)
    job_name = os.path.basename(jobpath)

    subprocess.check_call(params, env=dict(os.environ, PROJECT=project, PROJECT_NAME=project_name, JOB=jobpath, JOB_NAME=job_name))

def command_run(args):
    run(args.job, args.arguments)

def wrapper_workspace(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', action='store_const', const='project', dest='workspace')
    parser.add_argument('--job', action='store_const', const='job', dest='workspace')
    parser.add_argument('arguments', nargs=argparse.REMAINDER)

    parsed = parser.parse_args(args)

    # create requested workspace
    workspace_components = ['~/.sanctify', 'workspace']
    if parsed.workspace == 'job':
        workspace_components.extend(['job', os.environ['PROJECT_NAME'], os.environ['JOB_NAME']])
    else:
        workspace_components.extend(['project', os.environ['PROJECT_NAME']])

    workspace = os.path.expanduser(os.path.join(*workspace_components))
    os.makedirs(workspace, exist_ok=True)
    os.environ['WORKSPACE'] = workspace

    # run next step
    separator = parsed.arguments[0]
    rest = parsed.arguments[1:]
    assert separator == '--'

    subprocess.check_call(rest, cwd=workspace)

def command_wrapper(parsed):
    if parsed.name == 'workspace':
        wrapper_workspace(args.arguments)
    else:
        raise RuntimeError('Unsupported wrapper: %s' % parsed)

# top level parser
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='sub-command help')

# run parser
parser_run = subparsers.add_parser('run', help='Run a job')
parser_run.add_argument('job', help='Path to job script')
parser_run.add_argument('arguments', nargs=argparse.REMAINDER, help='job arguments')
parser_run.set_defaults(func=command_run)

# wrapper parser
parser_wrapper = subparsers.add_parser('wrapper', help='Run a wrapper')
parser_wrapper.add_argument('name', help='Wrapper name')
parser_wrapper.add_argument('arguments', nargs=argparse.REMAINDER, help='wrapper arguments')
parser_wrapper.set_defaults(func=command_wrapper)

if __name__ == '__main__':
    args = parser.parse_args()
    args.func(args)
