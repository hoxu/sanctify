#!/bin/sh -e
[ -f env/bin/activate ] || pyvenv env
. env/bin/activate
which nosetests > /dev/null || pip install -r requirements.txt
nosetests
