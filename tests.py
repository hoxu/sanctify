import io

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
