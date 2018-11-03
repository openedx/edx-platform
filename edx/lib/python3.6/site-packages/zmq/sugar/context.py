# coding: utf-8
"""Python bindings for 0MQ."""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import atexit
from threading import Lock

from zmq.backend import Context as ContextBase
from . import constants
from .attrsettr import AttributeSetter
from .constants import ENOTSUP, ctx_opt_names
from .socket import Socket
from zmq.error import ZMQError

# notice when exiting, to avoid triggering term on exit
_exiting = False
def _notice_atexit():
    global _exiting
    _exiting = True
atexit.register(_notice_atexit)

class Context(ContextBase, AttributeSetter):
    """Create a zmq Context
    
    A zmq Context creates sockets via its ``ctx.socket`` method.
    """
    sockopts = None
    _instance = None
    _instance_lock = Lock()
    _shadow = False
    
    def __init__(self, io_threads=1, **kwargs):
        super(Context, self).__init__(io_threads=io_threads, **kwargs)
        if kwargs.get('shadow', False):
            self._shadow = True
        else:
            self._shadow = False
        self.sockopts = {}
        
    
    def __del__(self):
        """deleting a Context should terminate it, without trying non-threadsafe destroy"""
        if not self._shadow and not _exiting:
            self.term()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args, **kwargs):
        self.term()
    
    def __copy__(self, memo=None):
        """Copying a Context creates a shadow copy"""
        return self.__class__.shadow(self.underlying)
    
    __deepcopy__ = __copy__
    
    @classmethod
    def shadow(cls, address):
        """Shadow an existing libzmq context
        
        address is the integer address of the libzmq context
        or an FFI pointer to it.
        
        .. versionadded:: 14.1
        """
        from zmq.utils.interop import cast_int_addr
        address = cast_int_addr(address)
        return cls(shadow=address)
    
    @classmethod
    def shadow_pyczmq(cls, ctx):
        """Shadow an existing pyczmq context
        
        ctx is the FFI `zctx_t *` pointer
        
        .. versionadded:: 14.1
        """
        from pyczmq import zctx
        from zmq.utils.interop import cast_int_addr
        
        underlying = zctx.underlying(ctx)
        address = cast_int_addr(underlying)
        return cls(shadow=address)

    # static method copied from tornado IOLoop.instance
    @classmethod
    def instance(cls, io_threads=1):
        """Returns a global Context instance.

        Most single-threaded applications have a single, global Context.
        Use this method instead of passing around Context instances
        throughout your code.

        A common pattern for classes that depend on Contexts is to use
        a default argument to enable programs with multiple Contexts
        but not require the argument for simpler applications:

            class MyClass(object):
                def __init__(self, context=None):
                    self.context = context or Context.instance()
        """
        if cls._instance is None or cls._instance.closed:
            with cls._instance_lock:
                if cls._instance is None or cls._instance.closed:
                    cls._instance = cls(io_threads=io_threads)
        return cls._instance
    
    #-------------------------------------------------------------------------
    # Hooks for ctxopt completion
    #-------------------------------------------------------------------------
    
    def __dir__(self):
        keys = dir(self.__class__)

        for collection in (
            ctx_opt_names,
        ):
            keys.extend(collection)
        return keys

    #-------------------------------------------------------------------------
    # Creating Sockets
    #-------------------------------------------------------------------------

    @property
    def _socket_class(self):
        return Socket
    
    def socket(self, socket_type, **kwargs):
        """Create a Socket associated with this Context.

        Parameters
        ----------
        socket_type : int
            The socket type, which can be any of the 0MQ socket types:
            REQ, REP, PUB, SUB, PAIR, DEALER, ROUTER, PULL, PUSH, etc.

        kwargs:
            will be passed to the __init__ method of the socket class.
        """
        if self.closed:
            raise ZMQError(ENOTSUP)
        s = self._socket_class(self, socket_type, **kwargs)
        for opt, value in self.sockopts.items():
            try:
                s.setsockopt(opt, value)
            except ZMQError:
                # ignore ZMQErrors, which are likely for socket options
                # that do not apply to a particular socket type, e.g.
                # SUBSCRIBE for non-SUB sockets.
                pass
        return s
    
    def setsockopt(self, opt, value):
        """set default socket options for new sockets created by this Context
        
        .. versionadded:: 13.0
        """
        self.sockopts[opt] = value
    
    def getsockopt(self, opt):
        """get default socket options for new sockets created by this Context
        
        .. versionadded:: 13.0
        """
        return self.sockopts[opt]
    
    def _set_attr_opt(self, name, opt, value):
        """set default sockopts as attributes"""
        if name in constants.ctx_opt_names:
            return self.set(opt, value)
        else:
            self.sockopts[opt] = value
    
    def _get_attr_opt(self, name, opt):
        """get default sockopts as attributes"""
        if name in constants.ctx_opt_names:
            return self.get(opt)
        else:
            if opt not in self.sockopts:
                raise AttributeError(name)
            else:
                return self.sockopts[opt]
    
    def __delattr__(self, key):
        """delete default sockopts as attributes"""
        key = key.upper()
        try:
            opt = getattr(constants, key)
        except AttributeError:
            raise AttributeError("no such socket option: %s" % key)
        else:
            if opt not in self.sockopts:
                raise AttributeError(key)
            else:
                del self.sockopts[opt]

__all__ = ['Context']
