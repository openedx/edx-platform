# coding: utf-8
"""Mixin for mapping set/getattr to self.set/get"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


from . import constants

class AttributeSetter(object):
    
    def __setattr__(self, key, value):
        """set zmq options by attribute"""
        
        # regular setattr only allowed for class-defined attributes
        for obj in [self] + self.__class__.mro():
            if key in obj.__dict__:
                object.__setattr__(self, key, value)
                return
        
        upper_key = key.upper()
        try:
            opt = getattr(constants, upper_key)
        except AttributeError:
            raise AttributeError("%s has no such option: %s" % (
                self.__class__.__name__, upper_key)
            )
        else:
            self._set_attr_opt(upper_key, opt, value)
    
    def _set_attr_opt(self, name, opt, value):
        """override if setattr should do something other than call self.set"""
        self.set(opt, value)
    
    def __getattr__(self, key):
        """get zmq options by attribute"""
        upper_key = key.upper()
        try:
            opt = getattr(constants, upper_key)
        except AttributeError:
            raise AttributeError("%s has no such option: %s" % (
                self.__class__.__name__, upper_key)
            )
        else:
            return self._get_attr_opt(upper_key, opt)

    def _get_attr_opt(self, name, opt):
        """override if getattr should do something other than call self.get"""
        return self.get(opt)
    

__all__ = ['AttributeSetter']
