import io
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
    sanctify.run('/dev/null', ['foo', 'bar'])

    check_call.assert_called_with(['/dev/null', 'foo', 'bar'])

    sanctify.run('testdata/wrapper', [])
    eq_(['wrapper', 'workspace', '--project', '--'], check_call.call_args[0][0][1:5])

def test_unwrap_job():
    expected = 'sanctify wrapper trigger --success=next.sh -- sanctify wrapper workspace --project -- job.sh'.split()
    unwrapped = sanctify.unwrap_job('sanctify', 'job.sh', [['trigger', '--success=next.sh'], ['workspace', '--project']])
    eq_(expected, unwrapped)
