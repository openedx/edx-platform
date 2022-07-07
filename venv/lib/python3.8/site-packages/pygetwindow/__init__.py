# PyGetWindow
# A cross-platform module to find information about the windows on the screen.

# Work in progress

# Useful info:
# https://stackoverflow.com/questions/373020/finding-the-current-active-window-in-mac-os-x-using-python
# https://stackoverflow.com/questions/7142342/get-window-position-size-with-python


# win32 api and ctypes on Windows
# cocoa api and pyobjc on Mac
# Xlib on linux


# Possible Future Features:
# get/click menu (win32: GetMenuItemCount, GetMenuItemInfo, GetMenuItemID, GetMenu, GetMenuItemRect)


__version__ = "0.0.9"

import sys, collections, pyrect


class PyGetWindowException(Exception):
    """
    Base class for exceptions raised when PyGetWindow functions
    encounter a problem. If PyGetWindow raises an exception that isn't
    this class, that indicates a bug in the module.
    """
    pass


def pointInRect(x, y, left, top, width, height):
    """Returns ``True`` if the ``(x, y)`` point is within the box described
    by ``(left, top, width, height)``."""
    return left < x < left + width and top < y < top + height


# NOTE: `Rect` is a named tuple for use in Python, while structs.RECT represents
# the win32 RECT struct. PyRect's Rect class is used for handling changing
# geometry of rectangular areas.
Rect = collections.namedtuple("Rect", "left top right bottom")
Point = collections.namedtuple("Point", "x y")
Size = collections.namedtuple("Size", "width height")


class BaseWindow:
    def __init__(self):
        pass

    def _setupRectProperties(self):
        def _onRead(attrName):
            r = self._getWindowRect()
            self._rect._left = r.left  # Setting _left directly to skip the onRead.
            self._rect._top = r.top  # Setting _top directly to skip the onRead.
            self._rect._width = r.right - r.left  # Setting _width directly to skip the onRead.
            self._rect._height = r.bottom - r.top  # Setting _height directly to skip the onRead.

        def _onChange(oldBox, newBox):
            self.moveTo(newBox.left, newBox.top)
            self.resizeTo(newBox.width, newBox.height)

        r = self._getWindowRect()
        self._rect = pyrect.Rect(r.left, r.top, r.right - r.left, r.bottom - r.top, onChange=_onChange, onRead=_onRead)

    def _getWindowRect(self):
        raise NotImplementedError

    def __str__(self):
        r = self._getWindowRect()
        width = r.right - r.left
        height = r.bottom - r.top
        return '<%s left="%s", top="%s", width="%s", height="%s", title="%s">' % (
            self.__class__.__qualname__,
            r.left,
            r.top,
            width,
            height,
            self.title,
        )

    def close(self):
        """Closes this window. This may trigger "Are you sure you want to
        quit?" dialogs or other actions that prevent the window from
        actually closing. This is identical to clicking the X button on the
        window."""
        raise NotImplementedError

    def minimize(self):
        """Minimizes this window."""
        raise NotImplementedError

    def maximize(self):
        """Maximizes this window."""
        raise NotImplementedError

    def restore(self):
        """If maximized or minimized, restores the window to it's normal size."""
        raise NotImplementedError

    def activate(self):
        """Activate this window and make it the foreground window."""
        raise NotImplementedError

    def resizeRel(self, widthOffset, heightOffset):
        """Resizes the window relative to its current size."""
        raise NotImplementedError

    def resizeTo(self, newWidth, newHeight):
        """Resizes the window to a new width and height."""
        raise NotImplementedError

    def moveRel(self, xOffset, yOffset):
        """Moves the window relative to its current position."""
        raise NotImplementedError

    def moveTo(self, newLeft, newTop):
        """Moves the window to new coordinates on the screen."""
        raise NotImplementedError

    @property
    def isMinimized(self):
        """Returns True if the window is currently minimized."""
        raise NotImplementedError

    @property
    def isMaximized(self):
        """Returns True if the window is currently maximized."""
        raise NotImplementedError

    @property
    def isActive(self):
        """Returns True if the window is currently the active, foreground window."""
        raise NotImplementedError

    @property
    def title(self):
        """Returns the window title as a string."""
        raise NotImplementedError

    @property
    def visible(self):
        raise NotImplementedError

    # Wrappers for pyrect.Rect object's properties:
    @property
    def left(self):
        return self._rect.left

    @left.setter
    def left(self, value):
        # import pdb; pdb.set_trace()
        self._rect.left  # Run rect's onRead to update the Rect object.
        self._rect.left = value

    @property
    def right(self):
        return self._rect.right

    @right.setter
    def right(self, value):
        self._rect.right  # Run rect's onRead to update the Rect object.
        self._rect.right = value

    @property
    def top(self):
        return self._rect.top

    @top.setter
    def top(self, value):
        self._rect.top  # Run rect's onRead to update the Rect object.
        self._rect.top = value

    @property
    def bottom(self):
        return self._rect.bottom

    @bottom.setter
    def bottom(self, value):
        self._rect.bottom  # Run rect's onRead to update the Rect object.
        self._rect.bottom = value

    @property
    def topleft(self):
        return self._rect.topleft

    @topleft.setter
    def topleft(self, value):
        self._rect.topleft  # Run rect's onRead to update the Rect object.
        self._rect.topleft = value

    @property
    def topright(self):
        return self._rect.topright

    @topright.setter
    def topright(self, value):
        self._rect.topright  # Run rect's onRead to update the Rect object.
        self._rect.topright = value

    @property
    def bottomleft(self):
        return self._rect.bottomleft

    @bottomleft.setter
    def bottomleft(self, value):
        self._rect.bottomleft  # Run rect's onRead to update the Rect object.
        self._rect.bottomleft = value

    @property
    def bottomright(self):
        return self._rect.bottomright

    @bottomright.setter
    def bottomright(self, value):
        self._rect.bottomright  # Run rect's onRead to update the Rect object.
        self._rect.bottomright = value

    @property
    def midleft(self):
        return self._rect.midleft

    @midleft.setter
    def midleft(self, value):
        self._rect.midleft  # Run rect's onRead to update the Rect object.
        self._rect.midleft = value

    @property
    def midright(self):
        return self._rect.midright

    @midright.setter
    def midright(self, value):
        self._rect.midright  # Run rect's onRead to update the Rect object.
        self._rect.midright = value

    @property
    def midtop(self):
        return self._rect.midtop

    @midtop.setter
    def midtop(self, value):
        self._rect.midtop  # Run rect's onRead to update the Rect object.
        self._rect.midtop = value

    @property
    def midbottom(self):
        return self._rect.midbottom

    @midbottom.setter
    def midbottom(self, value):
        self._rect.midbottom  # Run rect's onRead to update the Rect object.
        self._rect.midbottom = value

    @property
    def center(self):
        return self._rect.center

    @center.setter
    def center(self, value):
        self._rect.center  # Run rect's onRead to update the Rect object.
        self._rect.center = value

    @property
    def centerx(self):
        return self._rect.centerx

    @centerx.setter
    def centerx(self, value):
        self._rect.centerx  # Run rect's onRead to update the Rect object.
        self._rect.centerx = value

    @property
    def centery(self):
        return self._rect.centery

    @centery.setter
    def centery(self, value):
        self._rect.centery  # Run rect's onRead to update the Rect object.
        self._rect.centery = value

    @property
    def width(self):
        return self._rect.width

    @width.setter
    def width(self, value):
        self._rect.width  # Run rect's onRead to update the Rect object.
        self._rect.width = value

    @property
    def height(self):
        return self._rect.height

    @height.setter
    def height(self, value):
        self._rect.height  # Run rect's onRead to update the Rect object.
        self._rect.height = value

    @property
    def size(self):
        return self._rect.size

    @size.setter
    def size(self, value):
        self._rect.size  # Run rect's onRead to update the Rect object.
        self._rect.size = value

    @property
    def area(self):
        return self._rect.area

    @area.setter
    def area(self, value):
        self._rect.area  # Run rect's onRead to update the Rect object.
        self._rect.area = value

    @property
    def box(self):
        return self._rect.box

    @box.setter
    def box(self, value):
        self._rect.box  # Run rect's onRead to update the Rect object.
        self._rect.box = value


if sys.platform == "darwin":
    # raise NotImplementedError('PyGetWindow currently does not support macOS. If you have Appkit/Cocoa knowledge, please contribute! https://github.com/asweigart/pygetwindow') # TODO - implement mac
    from ._pygetwindow_macos import *

    Window = MacOSWindow
elif sys.platform == "win32":
    from ._pygetwindow_win import (
        Win32Window,
        getActiveWindow,
        getActiveWindowTitle,
        getWindowsAt,
        getWindowsWithTitle,
        getAllWindows,
        getAllTitles,
    )

    Window = Win32Window
else:
    raise NotImplementedError(
        "PyGetWindow currently does not support Linux. If you have Xlib knowledge, please contribute! https://github.com/asweigart/pygetwindow"
    )
