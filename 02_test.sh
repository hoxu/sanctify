#!/bin/sh -ux
# <sanctify>
# workspace --project
# </sanctify>

# Make sure we are in WORKSPACE
[ "$WORKSPACE" = $(pwd) ] || exit 1

# Due to "workspace --project" trigger, this script will be run in ~/.sanctify/workspace/project/sanctify/
# And when there, it will clone the git repository where the job is running from, by using $PROJECT
[ -d .git ] || git clone "$PROJECT" .

git pull

# Run the actual tests
./test.sh
