#!/usr/bin/env python3
# Copyright (c) 2016 Heikki Hokkanen <hoxu at users.sf.net>

import argparse
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
    import os
    sanctify_binary = os.path.abspath(inspect.getfile(inspect.currentframe()))

    with open(job) as f:
        wrappers = read_wrappers_from_stream(f)

    jobpath = os.path.abspath(job)
    unwrapped = unwrap_job(sanctify_binary, jobpath, wrappers)
    params = list(unwrapped)
    params.extend(arguments)
    subprocess.check_call(params)

def command_run(args):
    run(args.job, args.arguments)

def wrapper(args):
    print(args)

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
parser_wrapper.set_defaults(func=wrapper)

if __name__ == '__main__':
    args = parser.parse_args()
    args.func(args)
