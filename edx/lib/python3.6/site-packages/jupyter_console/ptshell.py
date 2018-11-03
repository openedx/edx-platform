"""IPython terminal interface using prompt_toolkit in place of readline"""
from __future__ import print_function

import base64
import errno
from getpass import getpass
from io import BytesIO
import os
import signal
import subprocess
import sys
import time
from warnings import warn

try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

from zmq import ZMQError
from IPython.core import page
from IPython.utils.py3compat import cast_unicode_py2, input
from ipython_genutils.tempdir import NamedFileInTemporaryDirectory
from traitlets import (Bool, Integer, Float, Unicode, List, Dict, Enum,
                       Instance, Any)
from traitlets.config import SingletonConfigurable

from .completer import ZMQCompleter
from .zmqhistory import ZMQHistoryManager
from . import __version__

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.filters import (Condition, has_focus, has_selection,
                                    vi_insert_mode, emacs_insert_mode, is_done)
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts.prompt import PromptSession
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.layout.processors import (ConditionalProcessor,
                                              HighlightMatchingBracketProcessor)
from prompt_toolkit.styles import merge_styles
from prompt_toolkit.styles.pygments import (style_from_pygments_cls,
                                            style_from_pygments_dict)
from prompt_toolkit.formatted_text import PygmentsTokens
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.utils import suspend_to_background_supported

from pygments.styles import get_style_by_name
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from pygments.token import Token


def ask_yes_no(prompt, default=None, interrupt=None):
    """Asks a question and returns a boolean (y/n) answer.

    If default is given (one of 'y','n'), it is used if the user input is
    empty. If interrupt is given (one of 'y','n'), it is used if the user
    presses Ctrl-C. Otherwise the question is repeated until an answer is
    given.

    An EOF is treated as the default answer.  If there is no default, an
    exception is raised to prevent infinite loops.

    Valid answers are: y/yes/n/no (match is not case sensitive)."""

    answers = {'y': True, 'n': False, 'yes': True, 'no': False}
    ans = None
    while ans not in answers.keys():
        try:
            ans = input(prompt + ' ').lower()
            if not ans:  # response was an empty string
                ans = default
        except KeyboardInterrupt:
            if interrupt:
                ans = interrupt
        except EOFError:
            if default in answers.keys():
                ans = default
                print()
            else:
                raise

    return answers[ans]


def get_pygments_lexer(name):
    name = name.lower()
    if name == 'ipython2':
        from IPython.lib.lexers import IPythonLexer
        return IPythonLexer
    elif name == 'ipython3':
        from IPython.lib.lexers import IPython3Lexer
        return IPython3Lexer
    else:
        try:
            return get_lexer_by_name(name).__class__
        except ClassNotFound:
            warn("No lexer found for language %r. Treating as plain text." % name)
            from pygments.lexers.special import TextLexer
            return TextLexer


class JupyterPTCompleter(Completer):
    """Adaptor to provide kernel completions to prompt_toolkit"""
    def __init__(self, jup_completer):
        self.jup_completer = jup_completer

    def get_completions(self, document, complete_event):
        if not document.current_line.strip():
            return

        content = self.jup_completer.complete_request(
            code=document.text,
            cursor_pos=document.cursor_position
        )
        start_pos = content['cursor_start'] - document.cursor_position
        for m in content['matches']:
            yield Completion(m, start_position=start_pos)


class ZMQTerminalInteractiveShell(SingletonConfigurable):
    readline_use = False

    pt_cli = None

    _executing = False
    _execution_state = Unicode('')
    _pending_clearoutput = False
    _eventloop = None
    own_kernel = False  # Changed by ZMQTerminalIPythonApp

    editing_mode = Unicode('emacs', config=True,
        help="Shortcut style to use at the prompt. 'vi' or 'emacs'.",
    )

    highlighting_style = Unicode('', config=True,
        help="The name of a Pygments style to use for syntax highlighting"
    )

    highlighting_style_overrides = Dict(config=True,
        help="Override highlighting format for specific tokens"
    )

    true_color = Bool(False, config=True,
        help=("Use 24bit colors instead of 256 colors in prompt highlighting. "
              "If your terminal supports true color, the following command "
              "should print 'TRUECOLOR' in orange: "
              "printf \"\\x1b[38;2;255;100;0mTRUECOLOR\\x1b[0m\\n\"")
    )

    history_load_length = Integer(1000, config=True,
        help="How many history items to load into memory"
    )

    banner = Unicode('Jupyter console {version}\n\n{kernel_banner}', config=True,
        help=("Text to display before the first prompt. Will be formatted with "
              "variables {version} and {kernel_banner}.")
    )

    kernel_timeout = Float(60, config=True,
        help="""Timeout for giving up on a kernel (in seconds).

        On first connect and restart, the console tests whether the
        kernel is running and responsive by sending kernel_info_requests.
        This sets the timeout in seconds for how long the kernel can take
        before being presumed dead.
        """
    )

    image_handler = Enum(('PIL', 'stream', 'tempfile', 'callable'),
                         'PIL', config=True, allow_none=True, help=
        """
        Handler for image type output.  This is useful, for example,
        when connecting to the kernel in which pylab inline backend is
        activated.  There are four handlers defined.  'PIL': Use
        Python Imaging Library to popup image; 'stream': Use an
        external program to show the image.  Image will be fed into
        the STDIN of the program.  You will need to configure
        `stream_image_handler`; 'tempfile': Use an external program to
        show the image.  Image will be saved in a temporally file and
        the program is called with the temporally file.  You will need
        to configure `tempfile_image_handler`; 'callable': You can set
        any Python callable which is called with the image data.  You
        will need to configure `callable_image_handler`.
        """
    )

    stream_image_handler = List(config=True, help=
        """
        Command to invoke an image viewer program when you are using
        'stream' image handler.  This option is a list of string where
        the first element is the command itself and reminders are the
        options for the command.  Raw image data is given as STDIN to
        the program.
        """
    )

    tempfile_image_handler = List(config=True, help=
        """
        Command to invoke an image viewer program when you are using
        'tempfile' image handler.  This option is a list of string
        where the first element is the command itself and reminders
        are the options for the command.  You can use {file} and
        {format} in the string to represent the location of the
        generated image file and image format.
        """
    )

    callable_image_handler = Any(config=True, help=
        """
        Callable object called via 'callable' image handler with one
        argument, `data`, which is `msg["content"]["data"]` where
        `msg` is the message from iopub channel.  For example, you can
        find base64 encoded PNG data as `data['image/png']`. If your function
        can't handle the data supplied, it should return `False` to indicate
        this.
        """
    )

    mime_preference = List(
        default_value=['image/png', 'image/jpeg', 'image/svg+xml'],
        config=True, help=
        """
        Preferred object representation MIME type in order.  First
        matched MIME type will be used.
        """
    )

    use_kernel_is_complete = Bool(True, config=True,
        help="""Whether to use the kernel's is_complete message
        handling. If False, then the frontend will use its
        own is_complete handler.
        """
    )
    kernel_is_complete_timeout = Float(1, config=True,
        help="""Timeout (in seconds) for giving up on a kernel's is_complete
        response.

        If the kernel does not respond at any point within this time,
        the kernel will no longer be asked if code is complete, and the
        console will default to the built-in is_complete test.
        """
    )

    # This is configurable on JupyterConsoleApp; this copy is not configurable
    # to avoid a duplicate config option.
    confirm_exit = Bool(True,
        help="""Set to display confirmation dialog on exit.
        You can always use 'exit' or 'quit', to force a
        direct exit without any confirmation.
        """
    )

    highlight_matching_brackets = Bool(True,
        help="Highlight matching brackets.",
    ).tag(config=True)

    manager = Instance('jupyter_client.KernelManager', allow_none=True)
    client = Instance('jupyter_client.KernelClient', allow_none=True)

    def _client_changed(self, name, old, new):
        self.session_id = new.session.session
    session_id = Unicode()

    def _banner1_default(self):
        return "Jupyter Console {version}\n".format(version=__version__)

    simple_prompt = Bool(False,
         help="""Use simple fallback prompt. Features may be limited."""
    ).tag(config=True)

    def __init__(self, **kwargs):
        # This is where traits with a config_key argument are updated
        # from the values on config.
        super(ZMQTerminalInteractiveShell, self).__init__(**kwargs)
        self.configurables = [self]

        self.init_history()
        self.init_completer()
        self.init_io()

        self.init_kernel_info()
        self.init_prompt_toolkit_cli()
        self.keep_running = True
        self.execution_count = 1

    def init_completer(self):
        """Initialize the completion machinery.

        This creates completion machinery that can be used by client code,
        either interactively in-process (typically triggered by the readline
        library), programmatically (such as in test suites) or out-of-process
        (typically over the network by remote frontends).
        """
        self.Completer = ZMQCompleter(self, self.client, config=self.config)

    def init_history(self):
        """Sets up the command history. """
        self.history_manager = ZMQHistoryManager(client=self.client)
        self.configurables.append(self.history_manager)

    def get_prompt_tokens(self):
        return [
            (Token.Prompt, 'In ['),
            (Token.PromptNum, str(self.execution_count)),
            (Token.Prompt, ']: '),
        ]

    def get_continuation_tokens(self, width):
        return [
            (Token.Prompt, (' ' * (width - 2)) + ': '),
        ]

    def get_out_prompt_tokens(self):
        return [
            (Token.OutPrompt, 'Out['),
            (Token.OutPromptNum, str(self.execution_count)),
            (Token.OutPrompt, ']: ')
        ]

    def print_out_prompt(self):
        tokens = self.get_out_prompt_tokens()
        print_formatted_text(PygmentsTokens(tokens), end='',
                             style = self.pt_cli.app.style)

    kernel_info = {}

    def init_kernel_info(self):
        """Wait for a kernel to be ready, and store kernel info"""
        timeout = self.kernel_timeout
        tic = time.time()
        self.client.hb_channel.unpause()
        msg_id = self.client.kernel_info()
        while True:
            try:
                reply = self.client.get_shell_msg(timeout=1)
            except Empty:
                if (time.time() - tic) > timeout:
                    raise RuntimeError("Kernel didn't respond to kernel_info_request")
            else:
                if reply['parent_header'].get('msg_id') == msg_id:
                    self.kernel_info = reply['content']
                    return

    def show_banner(self):
        print(self.banner.format(version=__version__,
                         kernel_banner=self.kernel_info.get('banner', '')))

    def init_prompt_toolkit_cli(self):
        if self.simple_prompt or ('JUPYTER_CONSOLE_TEST' in os.environ):
            # Simple restricted interface for tests so we can find prompts with
            # pexpect. Multi-line input not supported.
            def prompt():
                return cast_unicode_py2(input('In [%d]: ' % self.execution_count))
            self.prompt_for_code = prompt
            self.print_out_prompt = \
                lambda: print('Out[%d]: ' % self.execution_count, end='')
            return

        kb = KeyBindings()
        insert_mode = vi_insert_mode | emacs_insert_mode

        @kb.add("enter", filter=(has_focus(DEFAULT_BUFFER)
                                 & ~has_selection
                                 & insert_mode
                                 ))
        def _(event):
            b = event.current_buffer
            d = b.document
            if not (d.on_last_line or d.cursor_position_row >= d.line_count
                                           - d.empty_line_count_at_the_end()):
                b.newline()
                return

            # Pressing enter flushes any pending display. This also ensures
            # the displayed execution_count is correct.
            self.handle_iopub()

            more, indent = self.check_complete(d.text)

            if (not more) and b.accept_handler:
                b.validate_and_handle()
            else:
                b.insert_text('\n' + indent)

        @kb.add("c-c", filter=has_focus(DEFAULT_BUFFER))
        def _(event):
            event.current_buffer.reset()

        @kb.add("c-\\", filter=has_focus(DEFAULT_BUFFER))
        def _(event):
            raise EOFError

        @kb.add("c-z", filter=Condition(lambda: suspend_to_background_supported()))
        def _(event):
            event.cli.suspend_to_background()

        # Pre-populate history from IPython's history database
        history = InMemoryHistory()
        last_cell = u""
        for _, _, cell in self.history_manager.get_tail(self.history_load_length,
                                                        include_latest=True):
            # Ignore blank lines and consecutive duplicates
            cell = cast_unicode_py2(cell.rstrip())
            if cell and (cell != last_cell):
                history.append_string(cell)

        style_overrides = {
            Token.Prompt: '#009900',
            Token.PromptNum: '#00ff00 bold',
            Token.OutPrompt: '#ff2200',
            Token.OutPromptNum: '#ff0000 bold',
        }
        if self.highlighting_style:
            style_cls = get_style_by_name(self.highlighting_style)
        else:
            style_cls = get_style_by_name('default')
            # The default theme needs to be visible on both a dark background
            # and a light background, because we can't tell what the terminal
            # looks like. These tweaks to the default theme help with that.
            style_overrides.update({
                Token.Number: '#007700',
                Token.Operator: 'noinherit',
                Token.String: '#BB6622',
                Token.Name.Function: '#2080D0',
                Token.Name.Class: 'bold #2080D0',
                Token.Name.Namespace: 'bold #2080D0',
            })
        style_overrides.update(self.highlighting_style_overrides)
        style = merge_styles([
            style_from_pygments_cls(style_cls),
            style_from_pygments_dict(style_overrides),
        ])

        editing_mode = getattr(EditingMode, self.editing_mode.upper())
        langinfo = self.kernel_info.get('language_info', {})
        lexer = langinfo.get('pygments_lexer', langinfo.get('name', 'text'))

        # If enabled in the settings, highlight matching brackets
        # when the DEFAULT_BUFFER has the focus
        input_processors = [ConditionalProcessor(
            processor=HighlightMatchingBracketProcessor(chars='[](){}'),
            filter=has_focus(DEFAULT_BUFFER) & ~is_done &
            Condition(lambda: self.highlight_matching_brackets))
        ]

        self.pt_cli = PromptSession(
            message=(lambda: PygmentsTokens(self.get_prompt_tokens())),
            multiline=True,
            editing_mode=editing_mode,
            lexer=PygmentsLexer(get_pygments_lexer(lexer)),
            prompt_continuation=(
                lambda width, lineno, is_soft_wrap:
                PygmentsTokens(self.get_continuation_tokens(width))
            ),
            key_bindings=kb,
            history=history,
            completer=JupyterPTCompleter(self.Completer),
            enable_history_search=True,
            style=style,
            input_processors=input_processors,
            color_depth=(ColorDepth.TRUE_COLOR if self.true_color else None),

        )

    def prompt_for_code(self):
        if self.next_input:
            default = self.next_input
            self.next_input = None
        else:
            default = ''

        with patch_stdout(raw=True):
            text = self.pt_cli.prompt(
                default=default,
#                pre_run=self.pre_prompt,# reset_current_buffer=True,
            )
        return text

    def init_io(self):
        if sys.platform not in {'win32', 'cli'}:
            return

        import colorama
        colorama.init()

    def check_complete(self, code):
        if self.use_kernel_is_complete:
            msg_id = self.client.is_complete(code)
            try:
                return self.handle_is_complete_reply(msg_id,
                                                     timeout=self.kernel_is_complete_timeout)
            except SyntaxError:
                return False, ""
        else:
            lines = code.splitlines()
            if len(lines):
                more = (lines[-1] != "")
                return more, ""
            else:
                return False, ""

    def ask_exit(self):
        self.keep_running = False

    # This is set from payloads in handle_execute_reply
    next_input = None

    def pre_prompt(self):
        if self.next_input:
            # We can't set the buffer here, because it will be reset just after
            # this. Adding a callable to pre_run_callables does what we need
            # after the buffer is reset.
            s = cast_unicode_py2(self.next_input)

            def set_doc():
                self.pt_cli.app.buffer.document = Document(s)
            if hasattr(self.pt_cli, 'pre_run_callables'):
                self.pt_cli.app.pre_run_callables.append(set_doc)
            else:
                # Older version of prompt_toolkit; it's OK to set the document
                # directly here.
                set_doc()
            self.next_input = None

    def interact(self, display_banner=None):
        while self.keep_running:
            print('\n', end='')

            try:
                code = self.prompt_for_code()
            except EOFError:
                if (not self.confirm_exit) or \
                        ask_yes_no('Do you really want to exit ([y]/n)?', 'y', 'n'):
                    self.ask_exit()

            else:
                if code:
                    self.run_cell(code, store_history=True)

    def mainloop(self):
        self.keepkernel = not self.own_kernel
        # An extra layer of protection in case someone mashing Ctrl-C breaks
        # out of our internal code.
        while True:
            try:
                self.interact()
                break
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt escaped interact()\n")

        if self._eventloop:
            self._eventloop.close()
        if self.keepkernel and not self.own_kernel:
            print('keeping kernel alive')
        elif self.keepkernel and self.own_kernel:
            print("owning kernel, cannot keep it alive")
            self.client.shutdown()
        else:
            print("Shutting down kernel")
            self.client.shutdown()

    def run_cell(self, cell, store_history=True):
        """Run a complete IPython cell.

        Parameters
        ----------
        cell : str
          The code (including IPython code such as %magic functions) to run.
        store_history : bool
          If True, the raw and translated cell will be stored in IPython's
          history. For user code calling back into IPython's machinery, this
          should be set to False.
        """
        if (not cell) or cell.isspace():
            # pressing enter flushes any pending display
            self.handle_iopub()
            return

        # flush stale replies, which could have been ignored, due to missed heartbeats
        while self.client.shell_channel.msg_ready():
            self.client.shell_channel.get_msg()
        # execute takes 'hidden', which is the inverse of store_hist
        msg_id = self.client.execute(cell, not store_history)

        # first thing is wait for any side effects (output, stdin, etc.)
        self._executing = True
        self._execution_state = "busy"
        while self._execution_state != 'idle' and self.client.is_alive():
            try:
                self.handle_input_request(msg_id, timeout=0.05)
            except Empty:
                # display intermediate print statements, etc.
                self.handle_iopub(msg_id)
            except ZMQError as e:
                # Carry on if polling was interrupted by a signal
                if e.errno != errno.EINTR:
                    raise

        # after all of that is done, wait for the execute reply
        while self.client.is_alive():
            try:
                self.handle_execute_reply(msg_id, timeout=0.05)
            except Empty:
                pass
            else:
                break
        self._executing = False

    #-----------------
    # message handlers
    #-----------------

    def handle_execute_reply(self, msg_id, timeout=None):
        msg = self.client.shell_channel.get_msg(block=False, timeout=timeout)
        if msg["parent_header"].get("msg_id", None) == msg_id:

            self.handle_iopub(msg_id)

            content = msg["content"]
            status = content['status']

            if status == 'aborted':
                self.write('Aborted\n')
                return
            elif status == 'ok':
                # handle payloads
                for item in content.get("payload", []):
                    source = item['source']
                    if source == 'page':
                        page.page(item['data']['text/plain'])
                    elif source == 'set_next_input':
                        self.next_input = item['text']
                    elif source == 'ask_exit':
                        self.keepkernel = item.get('keepkernel', False)
                        self.ask_exit()

            elif status == 'error':
                pass

            self.execution_count = int(content["execution_count"] + 1)

    def handle_is_complete_reply(self, msg_id, timeout=None):
        """
        Wait for a repsonse from the kernel, and return two values:
            more? - (boolean) should the frontend ask for more input
            indent - an indent string to prefix the input
        Overloaded methods may want to examine the comeplete source. Its is
        in the self._source_lines_buffered list.
        """
        ## Get the is_complete response:
        msg = None
        try:
            msg = self.client.shell_channel.get_msg(block=True, timeout=timeout)
        except Empty:
            warn('The kernel did not respond to an is_complete_request. '
                 'Setting `use_kernel_is_complete` to False.')
            self.use_kernel_is_complete = False
            return False, ""
        ## Handle response:
        if msg["parent_header"].get("msg_id", None) != msg_id:
            warn('The kernel did not respond properly to an is_complete_request: %s.' % str(msg))
            return False, ""
        else:
            status = msg["content"].get("status", None)
            indent = msg["content"].get("indent", "")
        ## Return more? and indent string
        if status == "complete":
            return False, indent
        elif status == "incomplete":
            return True, indent
        elif status == "invalid":
            raise SyntaxError()
        elif status == "unknown":
            return False, indent
        else:
            warn('The kernel sent an invalid is_complete_reply status: "%s".' % status)
            return False, indent

    include_other_output = Bool(False, config=True,
        help="""Whether to include output from clients
        other than this one sharing the same kernel.

        Outputs are not displayed until enter is pressed.
        """
    )
    other_output_prefix = Unicode("[remote] ", config=True,
        help="""Prefix to add to outputs coming from clients other than this one.

        Only relevant if include_other_output is True.
        """
    )

    def from_here(self, msg):
        """Return whether a message is from this session"""
        return msg['parent_header'].get("session", self.session_id) == self.session_id

    def include_output(self, msg):
        """Return whether we should include a given output message"""
        from_here = self.from_here(msg)
        if msg['msg_type'] == 'execute_input':
            # only echo inputs not from here
            return self.include_other_output and not from_here

        if self.include_other_output:
            return True
        else:
            return from_here

    def handle_iopub(self, msg_id=''):
        """Process messages on the IOPub channel

           This method consumes and processes messages on the IOPub channel,
           such as stdout, stderr, execute_result and status.

           It only displays output that is caused by this session.
        """
        while self.client.iopub_channel.msg_ready():
            sub_msg = self.client.iopub_channel.get_msg()
            msg_type = sub_msg['header']['msg_type']
            parent = sub_msg["parent_header"]

            # Update execution_count in case it changed in another session
            if msg_type == "execute_input":
                self.execution_count = int(sub_msg["content"]["execution_count"]) + 1

            if self.include_output(sub_msg):
                if msg_type == 'status':
                    self._execution_state = sub_msg["content"]["execution_state"]
                elif msg_type == 'stream':
                    if sub_msg["content"]["name"] == "stdout":
                        if self._pending_clearoutput:
                            print("\r", end="")
                            self._pending_clearoutput = False
                        print(sub_msg["content"]["text"], end="")
                        sys.stdout.flush()
                    elif sub_msg["content"]["name"] == "stderr":
                        if self._pending_clearoutput:
                            print("\r", file=sys.stderr, end="")
                            self._pending_clearoutput = False
                        print(sub_msg["content"]["text"], file=sys.stderr, end="")
                        sys.stderr.flush()

                elif msg_type == 'execute_result':
                    if self._pending_clearoutput:
                        print("\r", end="")
                        self._pending_clearoutput = False
                    self.execution_count = int(sub_msg["content"]["execution_count"])
                    if not self.from_here(sub_msg):
                        sys.stdout.write(self.other_output_prefix)
                    format_dict = sub_msg["content"]["data"]
                    self.handle_rich_data(format_dict)

                    if 'text/plain' not in format_dict:
                        continue

                    # prompt_toolkit writes the prompt at a slightly lower level,
                    # so flush streams first to ensure correct ordering.
                    sys.stdout.flush()
                    sys.stderr.flush()
                    self.print_out_prompt()
                    text_repr = format_dict['text/plain']
                    if '\n' in text_repr:
                        # For multi-line results, start a new line after prompt
                        print()
                    print(text_repr)

                elif msg_type == 'display_data':
                    data = sub_msg["content"]["data"]
                    handled = self.handle_rich_data(data)
                    if not handled:
                        if not self.from_here(sub_msg):
                            sys.stdout.write(self.other_output_prefix)
                        # if it was an image, we handled it by now
                        if 'text/plain' in data:
                            print(data['text/plain'])

                elif msg_type == 'execute_input':
                    content = sub_msg['content']
                    if not self.from_here(sub_msg):
                        sys.stdout.write(self.other_output_prefix)
                    sys.stdout.write('In [{}]: '.format(content['execution_count']))
                    sys.stdout.write(content['code'] + '\n')

                elif msg_type == 'clear_output':
                    if sub_msg["content"]["wait"]:
                        self._pending_clearoutput = True
                    else:
                        print("\r", end="")

                elif msg_type == 'error':
                    for frame in sub_msg["content"]["traceback"]:
                        print(frame, file=sys.stderr)

    _imagemime = {
        'image/png': 'png',
        'image/jpeg': 'jpeg',
        'image/svg+xml': 'svg',
    }

    def handle_rich_data(self, data):
        for mime in self.mime_preference:
            if mime in data and mime in self._imagemime:
                if self.handle_image(data, mime):
                    return True
        return False

    def handle_image(self, data, mime):
        handler = getattr(
            self, 'handle_image_{0}'.format(self.image_handler), None)
        if handler:
            return handler(data, mime)

    def handle_image_PIL(self, data, mime):
        if mime not in ('image/png', 'image/jpeg'):
            return False
        try:
            from PIL import Image, ImageShow
        except ImportError:
            return False
        raw = base64.decodestring(data[mime].encode('ascii'))
        img = Image.open(BytesIO(raw))
        return ImageShow.show(img)

    def handle_image_stream(self, data, mime):
        raw = base64.decodestring(data[mime].encode('ascii'))
        imageformat = self._imagemime[mime]
        fmt = dict(format=imageformat)
        args = [s.format(**fmt) for s in self.stream_image_handler]
        with open(os.devnull, 'w') as devnull:
            proc = subprocess.Popen(
                args, stdin=subprocess.PIPE,
                stdout=devnull, stderr=devnull)
            proc.communicate(raw)
        return (proc.returncode == 0)

    def handle_image_tempfile(self, data, mime):
        raw = base64.decodestring(data[mime].encode('ascii'))
        imageformat = self._imagemime[mime]
        filename = 'tmp.{0}'.format(imageformat)
        with NamedFileInTemporaryDirectory(filename) as f, \
                open(os.devnull, 'w') as devnull:
            f.write(raw)
            f.flush()
            fmt = dict(file=f.name, format=imageformat)
            args = [s.format(**fmt) for s in self.tempfile_image_handler]
            rc = subprocess.call(args, stdout=devnull, stderr=devnull)
        return (rc == 0)

    def handle_image_callable(self, data, mime):
        res = self.callable_image_handler(data)
        if res is not False:
            # If handler func returns e.g. None, assume it has handled the data.
            res = True
        return res

    def handle_input_request(self, msg_id, timeout=0.1):
        """ Method to capture raw_input
        """
        req = self.client.stdin_channel.get_msg(timeout=timeout)
        # in case any iopub came while we were waiting:
        self.handle_iopub(msg_id)
        if msg_id == req["parent_header"].get("msg_id"):
            # wrap SIGINT handler
            real_handler = signal.getsignal(signal.SIGINT)

            def double_int(sig, frame):
                # call real handler (forwards sigint to kernel),
                # then raise local interrupt, stopping local raw_input
                real_handler(sig, frame)
                raise KeyboardInterrupt
            signal.signal(signal.SIGINT, double_int)
            content = req['content']
            read = getpass if content.get('password', False) else input
            try:
                raw_data = read(content["prompt"])
            except EOFError:
                # turn EOFError into EOF character
                raw_data = '\x04'
            except KeyboardInterrupt:
                sys.stdout.write('\n')
                return
            finally:
                # restore SIGINT handler
                signal.signal(signal.SIGINT, real_handler)

            # only send stdin reply if there *was not* another request
            # or execution finished while we were reading.
            if not (self.client.stdin_channel.msg_ready() or
                    self.client.shell_channel.msg_ready()):
                self.client.input(raw_data)
