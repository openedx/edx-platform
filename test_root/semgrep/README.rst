Semgrep linters
###############

Linting rules for use with `semgrep`_ during CI checks on PRs.

Status
******

This is an experimental approach to developing new linting rules. Semgrep provides by-example structural matching that can be easier to write and maintain than procedural code inspecting ASTs. If the approach works out, we can expand our use of Semgrep; if it becomes a problem for some reason, we can switch to adding pylint rules in edx-lint.

Ignoring failures
*****************

If you need to tell semgrep to ignore a block of code, put a ``# nosemgrep`` comment on or before the first matched line.

Documentation for writing new rules:

- https://semgrep.dev/docs/writing-rules/rule-syntax/
- https://semgrep.dev/docs/writing-rules/pattern-syntax/

.. _semgrep: https://github.com/returntocorp/semgrep
