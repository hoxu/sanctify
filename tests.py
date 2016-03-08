import io
import os
from unittest.mock import patch

from nose.tools import eq_

import sanctify

def test_parser():
    from sanctify import parser
    args = parser.parse_args(['run', 'job.sh'])
    eq_('job.sh', args.job)

    args = parser.parse_args(['run', 'job.sh', '--', '--custom', 'parameters'])
    eq_(['--custom', 'parameters'], args.arguments)

    args = parser.parse_args(['wrapper', 'workspace', '--', '--project'])
    eq_('workspace', args.name)
    eq_(['--project'], args.arguments)

def test_read_wrappers_from_stream():
    f = io.StringIO('#!/bin/sh\n# <sanctify>\n# trigger --success=another_build\n# workspace --project\n# noparams\n# </sanctify>\n')

    expected = [
        ['trigger', '--success=another_build'],
        ['workspace', '--project'],
        ['noparams'],
    ]
    wrappers = sanctify.read_wrappers_from_stream(f)
    eq_(expected, wrappers)

@patch('subprocess.check_call')
def test_run(check_call):
    with patch.dict(os.environ, {}, True):
        sanctify.run('/dev/null', ['foo', 'bar'])

    check_call.assert_called_with(['/dev/null', 'foo', 'bar'], env={'PROJECT': '/dev', 'PROJECT_NAME': 'dev', 'JOB': '/dev/null', 'JOB_NAME': 'null'})

    sanctify.run('testdata/wrapper', [])
    eq_(['wrapper', 'workspace', '--project', '--'], check_call.call_args[0][0][1:5])

def test_sniff_process_output():
    output = sanctify.sniff_process_output(['testdata/interleaved_output'])
    eq_('1\n2\n3\n4\n', output.decode('ascii'))

def test_unwrap_job():
    expected = 'sanctify wrapper trigger --success=next.sh -- sanctify wrapper workspace --project -- job.sh'.split()
    unwrapped = sanctify.unwrap_job('sanctify', 'job.sh', [['trigger', '--success=next.sh'], ['workspace', '--project']])
    eq_(expected, unwrapped)

@patch('os.makedirs')
@patch('subprocess.check_call')
def test_wrapper_workspace(check_call, makedirs):
    with patch.dict(os.environ, {'PROJECT_NAME': 'unittestproject', 'JOB_NAME': 'unittestjob'}):
        sanctify.wrapper_workspace(['--project', '--', 'job.sh'])

    workspace = os.path.expanduser('~/.sanctify/workspace/project/unittestproject')
    eq_(workspace, makedirs.call_args[0][0])
    eq_(['job.sh'], check_call.call_args[0][0])
    eq_(workspace, check_call.call_args[1]['cwd'])

    with patch.dict(os.environ, {'PROJECT_NAME': 'unittestproject', 'JOB_NAME': 'unittestjob'}):
        sanctify.wrapper_workspace(['--job', '--', 'job.sh'])

    eq_(os.path.expanduser('~/.sanctify/workspace/job/unittestproject/unittestjob'), makedirs.call_args[0][0])
    eq_(['job.sh'], check_call.call_args[0][0])
