"""
Provides:
    PassthroughOptionParser:
        A subclass of :class:`optparse.OptionParser` that captures unknown options
        into its ``passthrough_options`` attribute.
    PassthroughTask:
        A subclass of :class:`paver.tasks.Task` that supplies unknown options
        as the `passthrough_options` argument to the decorated function
"""

from optparse import OptionParser, BadOptionError
import paver.tasks
from mock import patch


try:
    from gettext import gettext
except ImportError:
    def gettext(message):
        """Dummy gettext"""
        return message
_ = gettext


class PassthroughOptionParser(OptionParser):
    """
    An :class:`optparse.OptionParser` which captures any unknown options into
    the ``passthrough_options`` attribute. Handles both "--long-options" and
    "-s" short options.
    """
    def __init__(self, *args, **kwargs):
        self.passthrough_options = []

        # N.B. OptionParser is an old-style class, which is why
        # this isn't using super()
        OptionParser.__init__(self, *args, **kwargs)

    def _process_long_opt(self, rargs, values):
        # This is a copy of the OptionParser._process_long_opt method,
        # modified to capture arguments that aren't understood

        arg = rargs.pop(0)

        # Value explicitly attached to arg?  Pretend it's the next
        # argument.

        if "=" in arg:
            (opt, next_arg) = arg.split("=", 1)
            rargs.insert(0, next_arg)
            had_explicit_value = True
        else:
            opt = arg
            had_explicit_value = False

        try:
            opt = self._match_long_opt(opt)
        except BadOptionError:
            self.passthrough_options.append(arg)
            if had_explicit_value:
                rargs.pop(0)
            return

        option = self._long_opt[opt]
        if option.takes_value():
            nargs = option.nargs

            if len(rargs) < nargs:
                if nargs == 1:
                    self.error(_("%s option requires an argument") % opt)
                else:
                    self.error(_("%s option requires %d arguments")
                               % (opt, nargs))
            elif nargs == 1:
                value = rargs.pop(0)
            else:
                value = tuple(rargs[0:nargs])
                del rargs[0:nargs]

        elif had_explicit_value:
            self.error(_("%s option does not take a value") % opt)

        else:
            value = None

        option.process(opt, value, values, self)

    def _process_short_opts(self, rargs, values):
        arg = rargs.pop(0)
        stop = False
        i = 1

        passthrough_opts = []

        for char in arg[1:]:
            opt = "-" + char
            option = self._short_opt.get(opt)
            i += 1                      # we have consumed a character

            if not option:
                passthrough_opts.append(char)
                continue

            if option.takes_value():
                # Any characters left in arg?  Pretend they're the
                # next arg, and stop consuming characters of arg.

                if i < len(arg):
                    rargs.insert(0, arg[i:])
                    stop = True

                nargs = option.nargs
                if len(rargs) < nargs:
                    if nargs == 1:
                        self.error(_("%s option requires an argument") % opt)
                    else:
                        self.error(_("%s option requires %d arguments")
                                   % (opt, nargs))

                elif nargs == 1:
                    value = rargs.pop(0)
                else:
                    value = tuple(rargs[0:nargs])
                    del rargs[0:nargs]

            else:                       # option doesn't take a value
                value = None

            option.process(opt, value, values, self)

            if stop:
                break

        if passthrough_opts:
            self.passthrough_options.append('-{}'.format("".join(passthrough_opts)))


class PassthroughTask(paver.tasks.Task):
    """
    A :class:`paver.tasks.Task` subclass that supplies any options that it doesn't
    understand to the task function as the ``passthrough_options`` argument.
    """

    @property
    def parser(self):
        with patch.object(paver.tasks.optparse, 'OptionParser', PassthroughOptionParser):
            return super(PassthroughTask, self).parser

    def __call__(self, *args, **kwargs):
        paver.tasks.environment.passthrough_options = self._parser.passthrough_options  # pylint: disable=no-member
        try:
            return super(PassthroughTask, self).__call__(*args, **kwargs)
        finally:
            del paver.tasks.environment.passthrough_options
