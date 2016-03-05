from nose.tools import eq_

from sanctify import parser

def test_parser():
    args = parser.parse_args(['run', 'job.sh'])
    eq_('job.sh', args.job)

    args = parser.parse_args(['run', 'job.sh', '--', '--custom', 'parameters'])
    eq_(['--custom', 'parameters'], args.arguments)

    args = parser.parse_args(['wrapper', 'workspace', '--', '--project'])
    eq_('workspace', args.name)
    eq_(['--project'], args.arguments)
