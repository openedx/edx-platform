# dockerpty.
#
# Copyright 2014 Chris Corbyn <chris@w3style.co.uk>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dockerpty.pty import PseudoTerminal, RunOperation, ExecOperation, exec_create


def start(client, container, interactive=True, stdout=None, stderr=None, stdin=None, logs=None):
    """
    Present the PTY of the container inside the current process.

    This is just a wrapper for PseudoTerminal(client, container).start()
    """

    operation = RunOperation(client, container, interactive=interactive, stdout=stdout,
                             stderr=stderr, stdin=stdin, logs=logs)

    PseudoTerminal(client, operation).start()


def exec_command(
        client, container, command, interactive=True, stdout=None, stderr=None, stdin=None):
    """
    Run provided command via exec API in provided container.

    This is just a wrapper for PseudoTerminal(client, container).exec_command()
    """
    exec_id = exec_create(client, container, command, interactive=interactive)

    operation = ExecOperation(client, exec_id,
                              interactive=interactive, stdout=stdout, stderr=stderr, stdin=stdin)
    PseudoTerminal(client, operation).start()


def start_exec(client, exec_id, interactive=True, stdout=None, stderr=None, stdin=None):
    operation = ExecOperation(client, exec_id,
                              interactive=interactive, stdout=stdout, stderr=stderr, stdin=stdin)
    PseudoTerminal(client, operation).start()
