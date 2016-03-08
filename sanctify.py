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

def sniff_process_output(args):
    """Makes an interleaved copy of a process's stdout/stderr, letting them flow to inherited stdout/stderr"""
    pipe_r, pipe_w = os.pipe()

    # run the actual job, inherit stdin, pipe stdout/stderr
    pjob = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # use tees to copy stdout/stderr to a pipe
    # pass as-is to original inherited stdout/stderr
    subprocess.Popen(['tee', '-a', '/dev/fd/%d' % pipe_w], stdin=pjob.stdout, stdout=None, pass_fds=[pipe_w])
    subprocess.Popen(['tee', '-a', '/dev/fd/%d' % pipe_w], stdin=pjob.stderr, stdout=None, pass_fds=[pipe_w])

    # Let pjob get SIGPIPE if tees die early
    pjob.stdout.close()
    pjob.stderr.close()

    # must be closed for the pipe to close after tees close it
    # otherwise the read below will block forever
    os.close(pipe_w)

    with os.fdopen(pipe_r, mode='rb') as f:
        output = f.read()

    return [output, pjob.wait()]

def send_mail(mail_from, mail_to, subject, body):
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(body)
    msg['From'] = mail_from
    msg['To'] = mail_to
    msg['Subject'] = subject

    s = smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()

def wrapper_mail(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--always', action='store_const', const='always', dest='when')
    parser.add_argument('--failure', action='store_const', const='failure', dest='when')
    parser.add_argument('--success', action='store_const', const='success', dest='when')
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    parsed = parser.parse_args(args)

    # run next step
    separator = parsed.arguments[0]
    rest = parsed.arguments[1:]
    assert separator == '--'

    mail_from = 'Sanctify <%s@localhost>' % (os.environ['USER'])
    mail_to = '<%s@localhost>' % (os.environ['USER'])
    subject = 'Sanctify: %s - %s' % (os.environ['PROJECT_NAME'], os.environ['JOB_NAME'])

    output, returncode = sniff_process_output(rest)

    # send mail with content if returncode warrants it
    if (returncode == 0 and parsed.when in ['always', 'success']) or (returncode != 0 and parsed.when in ['always', 'failure']):
        send_mail(mail_from, mail_to, subject, output.decode('utf-8'))

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
    if parsed.name == 'mail':
        wrapper_mail(args.arguments)
    elif parsed.name == 'workspace':
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
