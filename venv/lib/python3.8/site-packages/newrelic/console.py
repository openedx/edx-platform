# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import atexit
import cmd
import code
import functools
import glob
import inspect
import optparse
import os
import shlex
import socket
import sys
import threading
import time
import traceback

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

try:
    import __builtin__
except ImportError:
    import builtins as __builtin__


def _argspec_py2(func):
    return inspect.getargspec(func)


def _argspec_py3(func):
    a = inspect.getfullargspec(func)
    return (a.args, a.varargs, a.varkw, a.defaults)


if hasattr(inspect, "getfullargspec"):
    _argspec = _argspec_py3
else:
    _argspec = _argspec_py2

try:
    from collections import OrderedDict
    from inspect import signature

    def doc_signature(func):
        sig = signature(func)
        sig._parameters = OrderedDict(list(sig._parameters.items())[1:])
        return str(sig)


except ImportError:
    from inspect import formatargspec

    def doc_signature(func):
        args, varargs, keywords, defaults = _argspec(func)
        return formatargspec(args[1:], varargs, keywords, defaults)


from newrelic.api.object_wrapper import ObjectWrapper
from newrelic.api.transaction import Transaction
from newrelic.core.agent import agent_instance
from newrelic.core.config import flatten_settings, global_settings
from newrelic.core.trace_cache import trace_cache

_trace_cache = trace_cache()


def shell_command(wrapped):
    args, varargs, keywords, defaults = _argspec(wrapped)

    parser = optparse.OptionParser()
    for name in args[1:]:
        parser.add_option("--%s" % name, dest=name)

    @functools.wraps(wrapped)
    def wrapper(self, line):
        result = shlex.split(line)

        (options, args) = parser.parse_args(result)

        kwargs = {}
        for key, value in options.__dict__.items():
            if value is not None:
                kwargs[key] = value

        return wrapped(self, *args, **kwargs)

    if wrapper.__name__.startswith("do_"):
        prototype = wrapper.__name__[3:] + " " + doc_signature(wrapped)

        if hasattr(wrapper, "__doc__") and wrapper.__doc__ is not None:
            wrapper.__doc__ = "\n".join((prototype, wrapper.__doc__.lstrip("\n")))

    return wrapper


_consoles = threading.local()


def acquire_console(shell):
    _consoles.active = shell


def release_console():
    del _consoles.active


def setquit():
    """Define new built-ins 'quit' and 'exit'.
    These are simply strings that display a hint on how to exit.

    """
    if os.sep == ":":
        eof = "Cmd-Q"
    elif os.sep == "\\":
        eof = "Ctrl-Z plus Return"
    else:
        eof = "Ctrl-D (i.e. EOF)"

    class Quitter(object):
        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return "Use %s() or %s to exit" % (self.name, eof)

        def __call__(self, code=None):
            # If executed with our interactive console, only raise the
            # SystemExit exception but don't close sys.stdout as we are
            # not the owner of it.

            if hasattr(_consoles, "active"):
                raise SystemExit(code)

            # Shells like IDLE catch the SystemExit, but listen when their
            # stdin wrapper is closed.

            try:
                sys.stdin.close()
            except Exception:
                pass
            raise SystemExit(code)

    __builtin__.quit = Quitter("quit")
    __builtin__.exit = Quitter("exit")


class OutputWrapper(ObjectWrapper):
    def flush(self):
        try:
            shell = _consoles.active
            return shell.stdout.flush()
        except Exception:
            return self._nr_next_object.flush()

    def write(self, data):
        try:
            shell = _consoles.active
            return shell.stdout.write(data)
        except Exception:
            return self._nr_next_object.write(data)

    def writelines(self, data):
        try:
            shell = _consoles.active
            return shell.stdout.writelines(data)
        except Exception:
            return self._nr_next_object.writelines(data)


def intercept_console():
    setquit()

    sys.stdout = OutputWrapper(sys.stdout, None, None)
    sys.stderr = OutputWrapper(sys.stderr, None, None)


class EmbeddedConsole(code.InteractiveConsole):
    def write(self, data):
        self.stdout.write(data)
        self.stdout.flush()

    def raw_input(self, prompt):
        self.stdout.write(prompt)
        self.stdout.flush()
        line = self.stdin.readline()
        line = line.rstrip("\r\n")
        return line


class ConsoleShell(cmd.Cmd):

    use_rawinput = 0

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.do_prompt("on")

    def emptyline(self):
        pass

    def help_help(self):
        print(
            """help (command)
        Output list of commands or help details for named command.""",
            file=self.stdout,
        )

    @shell_command
    def do_prompt(self, flag=None):
        """
        Enable or disable the console prompt."""

        if flag == "on":
            self.prompt = "(newrelic:%d) " % os.getpid()
        elif flag == "off":
            self.prompt = ""

    @shell_command
    def do_exit(self):
        """
        Exit the console."""

        return True

    @shell_command
    def do_process_id(self):
        """
        Displays the process ID of the process."""

        print(os.getpid(), file=self.stdout)

    @shell_command
    def do_sys_prefix(self):
        """
        Displays the value of sys.prefix."""

        print(sys.prefix, file=self.stdout)

    @shell_command
    def do_sys_path(self):
        """
        Displays the value of sys.path."""

        print(sys.path, file=self.stdout)

    @shell_command
    def do_sys_modules(self):
        """
        Displays the list of Python modules loaded."""

        for name, module in sorted(sys.modules.items()):
            if module is not None:
                file = getattr(module, "__file__", None)
                print("%s - %s" % (name, file), file=self.stdout)

    @shell_command
    def do_sys_meta_path(self):
        """
        Displays the value of sys.meta_path."""

        print(sys.meta_path, file=self.stdout)

    @shell_command
    def do_os_environ(self):
        """
        Displays the set of user environment variables."""

        for key, name in os.environ.items():
            print("%s = %r" % (key, name), file=self.stdout)

    @shell_command
    def do_current_time(self):
        """
        Displays the current time."""

        print(time.asctime(), file=self.stdout)

    @shell_command
    def do_config_args(self):
        """
        Displays the configure arguments used to build Python."""

        args = ""

        try:
            # This may fail if using package Python and the
            # developer package for Python isn't also installed.

            import distutils.sysconfig

            args = distutils.sysconfig.get_config_var("CONFIG_ARGS")

        except Exception:
            pass

        print(args, file=self.stdout)

    @shell_command
    def do_dump_config(self, name=None):
        """
        Displays global configuration or that of the named application.
        """

        if name is None:
            config = agent_instance().global_settings()
        else:
            config = agent_instance().application_settings(name)

        if config is not None:
            config = flatten_settings(config)
            keys = sorted(config.keys())
            for key in keys:
                print("%s = %r" % (key, config[key]), file=self.stdout)

    @shell_command
    def do_agent_status(self):
        """
        Displays general status information about the agent, registered
        applications, harvest cycles etc.
        """

        agent_instance().dump(self.stdout)

    @shell_command
    def do_applications(self):
        """
        Displays a list of the applications.
        """

        print(repr(sorted(agent_instance().applications.keys())), file=self.stdout)

    @shell_command
    def do_application_status(self, name=None):
        """
        Displays general status information about an application, last
        harvest cycle, etc.
        """

        if name is not None:
            applications = [agent_instance().application(name)]
        else:
            applications = agent_instance().applications.values()

        for application in applications:
            if application is not None:
                application.dump(self.stdout)
                print(file=self.stdout)

    @shell_command
    def do_import_hooks(self):
        """
        Displays list of registered import hooks, which have fired and
        which encountered errors.
        """

        from newrelic.config import module_import_hook_results

        results = module_import_hook_results()
        for key in sorted(results.keys()):
            result = results[key]
            if result is None:
                if key[0] not in sys.modules:
                    print("%s: PENDING" % (key,), file=self.stdout)
                else:
                    print("%s: IMPORTED" % (key,), file=self.stdout)
            elif not result:
                print("%s: INSTRUMENTED" % (key,), file=self.stdout)
            else:
                print("%s: FAILED" % (key,), file=self.stdout)
                for line in result:
                    print(line, end="", file=self.stdout)

    @shell_command
    def do_transactions(self):
        """ """

        for item in _trace_cache.active_threads():
            transaction, thread_id, thread_type, frame = item
            print("THREAD", item, file=self.stdout)
            if transaction is not None:
                transaction.dump(self.stdout)
            print(file=self.stdout)

    @shell_command
    def do_interpreter(self):
        """
        When enabled in the configuration file, will startup up an embedded
        interactive Python interpreter. Invoke 'exit()' or 'quit()' to
        escape the interpreter session."""

        enabled = False

        _settings = global_settings()

        if not _settings.console.allow_interpreter_cmd:
            print("Sorry, the embedded Python interpreter is disabled.", file=self.stdout)
            return

        locals = {}

        locals["stdin"] = self.stdin
        locals["stdout"] = self.stdout

        console = EmbeddedConsole(locals)

        console.stdin = self.stdin
        console.stdout = self.stdout

        acquire_console(self)

        try:
            console.interact()
        except SystemExit:
            pass
        finally:
            release_console()

    @shell_command
    def do_threads(self):
        """
        Display stack trace dumps for all threads currently executing
        within the Python interpreter.

        Note that if coroutines are being used, such as systems based
        on greenlets, then only the thread stack of the currently
        executing coroutine will be displayed."""

        all = []
        for threadId, stack in sys._current_frames().items():
            block = []
            block.append("# ThreadID: %s" % threadId)
            thr = threading._active.get(threadId)
            if thr:
                block.append("# Type: %s" % type(thr).__name__)
                block.append("# Name: %s" % thr.name)
            for filename, lineno, name, line in traceback.extract_stack(stack):
                block.append("File: '%s', line %d, in %s" % (filename, lineno, name))
                if line:
                    block.append("  %s" % (line.strip()))
            all.append("\n".join(block))

        print("\n\n".join(all), file=self.stdout)


class ConnectionManager(object):
    def __init__(self, listener_socket):
        self.__listener_socket = listener_socket
        self.__console_initialized = False

        if not os.path.isabs(self.__listener_socket):
            host, port = self.__listener_socket.split(":")
            port = int(port)
            self.__listener_socket = (host, port)

        self.__thread = threading.Thread(target=self.__thread_run, name="NR-Console-Manager")

        self.__thread.daemon = True
        self.__thread.start()

    def __socket_cleanup(self, path):
        try:
            os.unlink(path)
        except Exception:
            pass

    def __thread_run(self):
        if type(self.__listener_socket) == type(()):
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(self.__listener_socket)
        else:
            try:
                os.unlink(self.__listener_socket)
            except Exception:
                pass

            listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            listener.bind(self.__listener_socket)

            atexit.register(self.__socket_cleanup, self.__listener_socket)
            os.chmod(self.__listener_socket, 0o600)

        listener.listen(5)

        while True:
            client, addr = listener.accept()

            if not self.__console_initialized:
                self.__console_initialized = True
                intercept_console()

            shell = ConsoleShell()

            shell.stdin = client.makefile("r")
            shell.stdout = client.makefile("w")

            while True:
                try:
                    shell.cmdloop()

                except Exception:
                    shell.stdout.flush()
                    print("Unexpected exception.", file=shell.stdout)
                    exc_info = sys.exc_info()
                    traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], file=shell.stdout)
                    exc_info = None

                else:
                    break

            shell.stdin = None
            shell.stdout = None

            del shell

            client.close()


class ClientShell(cmd.Cmd):

    prompt = "(newrelic) "

    def __init__(self, config_file, stdin=None, stdout=None, log=None):
        cmd.Cmd.__init__(self, stdin=stdin, stdout=stdout)

        self.__config_file = config_file
        self.__config_object = ConfigParser.RawConfigParser()
        self.__log_object = log

        if not self.__config_object.read([config_file]):
            raise RuntimeError("Unable to open configuration file %s." % config_file)

        listener_socket = self.__config_object.get("newrelic", "console.listener_socket") % {"pid": "*"}

        if os.path.isabs(listener_socket):
            self.__servers = [(socket.AF_UNIX, path) for path in sorted(glob.glob(listener_socket))]
        else:
            host, port = listener_socket.split(":")
            port = int(port)

            self.__servers = [(socket.AF_INET, (host, port))]

    def emptyline(self):
        pass

    def help_help(self):
        print(
            """help (command)
        Output list of commands or help details for named command.""",
            file=self.stdout,
        )

    def do_exit(self, line):
        """exit
        Exit the client shell."""

        return True

    def do_servers(self, line):
        """servers
        Display a list of the servers which can be connected to."""

        for i in range(len(self.__servers)):
            print("%s: %s" % (i + 1, self.__servers[i]), file=self.stdout)

    def do_connect(self, line):
        """connect [index]
        Connect to the server from the servers lift with given index. If
        there is only one server then the index position does not need to
        be supplied."""

        if len(self.__servers) == 0:
            print("No servers to connect to.", file=self.stdout)
            return

        if not line:
            if len(self.__servers) != 1:
                print("Multiple servers, which should be used?", file=self.stdout)
                return
            else:
                line = "1"

        try:
            selection = int(line)
        except Exception:
            selection = None

        if selection is None:
            print("Server selection not an integer.", file=self.stdout)
            return

        if selection <= 0 or selection > len(self.__servers):
            print("Invalid server selected.", file=self.stdout)
            return

        server = self.__servers[selection - 1]

        client = socket.socket(server[0], socket.SOCK_STREAM)
        client.connect(server[1])

        def write():
            while 1:
                try:
                    c = sys.stdin.read(1)

                    if not c:
                        client.shutdown(socket.SHUT_RD)
                        break

                    if self.__log_object:
                        self.__log_object.write(c)

                    client.sendall(c.encode("utf-8"))
                except Exception:
                    break

        def read():
            while 1:
                try:
                    c = client.recv(1).decode("utf-8")

                    if not c:
                        break

                    if self.__log_object:
                        self.__log_object.write(c)

                    sys.stdout.write(c)
                    sys.stdout.flush()
                except Exception:
                    break

        thread1 = threading.Thread(target=write)
        thread1.daemon = True

        thread2 = threading.Thread(target=read)
        thread2.daemon = True

        thread1.start()
        thread2.start()

        thread2.join()

        return True


def main():
    if len(sys.argv) == 1:
        print("Usage: newrelic-console config_file")
        sys.exit(1)

    shell = ClientShell(sys.argv[1])
    shell.cmdloop()


if __name__ == "__main__":
    main()
