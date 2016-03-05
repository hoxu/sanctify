# Sanctify

Sanctify is a lightweight Jenkins alternative relying on simple command line
tools. Ability put job descriptions under version control is an inherent design
decision, not an afterthought.

## Design goals

* Job descriptions are simple scripts, written in any language
* Do not reinvent the wheel: leave time-based job triggering to cron for example
* Keep everything as simple as possible

## Wrappers

Jobs can contain wrappers in the header, like this:

```
#!/bin/sh -xu
# <sanctify>
# log --one
# workspace --project
# </sanctify>
```

`sanctify run <job>` then reads the header, and wraps the job in each of the
wrappers, like so:

```
sanctify wrapper log --one -- \
sanctify wrapper workspace --project -- \
<job>
```

A wrapper is simply script that takes optional parameters, and finally a `--`
parameter, followed by the job path and optional parameters.

Wrappers can redirect output, export variables, create workspace directory,
etc.

The wrapper must exit with value of the command after `--`. This is to allow
multiple wrappers to act on the result of the actual job.
