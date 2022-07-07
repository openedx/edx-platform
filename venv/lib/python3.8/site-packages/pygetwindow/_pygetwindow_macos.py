import Quartz
import pygetwindow


def getAllTitles():
    """Returns a list of strings of window titles for all visible windows.
    """

    # Source: https://stackoverflow.com/questions/53237278/obtain-list-of-all-window-titles-on-macos-from-a-python-script/53985082#53985082
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    return ['%s %s' % (win[Quartz.kCGWindowOwnerName], win.get(Quartz.kCGWindowName, '')) for win in windows]


def getActiveWindow():
    """Returns a Window object of the currently active Window."""

    # Source: https://stackoverflow.com/questions/5286274/front-most-window-using-cgwindowlistcopywindowinfo
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for win in windows:
        if win['kCGWindowLayer'] == 0:
            return '%s %s' % (win[Quartz.kCGWindowOwnerName], win.get(Quartz.kCGWindowName, '')) # Temporary. For now, we'll just return the title of the active window.
    raise Exception('Could not find an active window.') # Temporary hack.


def getWindowsAt(x, y):
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    matches = []
    for win in windows:
        w = win['kCGWindowBounds']
        if pygetwindow.pointInRect(x, y, w['X'], w['Y'], w['Width'], w['Height']):
            matches.append('%s %s' % (win[Quartz.kCGWindowOwnerName], win.get(Quartz.kCGWindowName, '')))
    return matches



def activate():
    # TEMP - this is not a real api, I'm just using this name to store these notes for now.

    # Source: https://stackoverflow.com/questions/7460092/nswindow-makekeyandorderfront-makes-window-appear-but-not-key-or-front?rq=1
    # Source: https://stackoverflow.com/questions/4905024/is-it-possible-to-bring-window-to-front-without-taking-focus?rq=1
    pass


def getWindowGeometry(title):
    # TEMP - this is not a real api, I'm just using this name to stoe these notes for now.
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for win in windows:
        if title in '%s %s' % (win[Quartz.kCGWindowOwnerName], win.get(Quartz.kCGWindowName, '')):
            w = win['kCGWindowBounds']
            return (w['X'], w['Y'], w['Width'], w['Height'])


def isVisible(title):
    # TEMP - this is not a real api, I'm just using this name to stoe these notes for now.
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for win in windows:
        if title in '%s %s' % (win[Quartz.kCGWindowOwnerName], win.get(Quartz.kCGWindowName, '')):
            return win['kCGWindowAlpha'] != 0.0

def isMinimized():
    # TEMP - this is not a real api, I'm just using this name to stoe these notes for now.
    # Source: https://stackoverflow.com/questions/10258676/how-to-know-whether-a-window-is-minimised-or-not
    # Use the kCGWindowIsOnscreen to check this. Minimized windows are considered to not be on the screen. (But I'm not sure if there are other situations where a window is "off screen".)

    # I'm not sure how kCGWindowListOptionOnScreenOnly interferes with this.
    pass

# TODO: This class doesn't work yet. I've copied the Win32Window class and will make adjustments as needed here.

class MacOSWindow():
    def __init__(self, hWnd):
        self._hWnd = hWnd # TODO fix this, this is a LP_c_long insead of an int.

        def _onRead(attrName):
            r = self._getWindowRect(_hWnd)
            self._rect._left = r.left # Setting _left directly to skip the onRead.
            self._rect._top = r.top # Setting _top directly to skip the onRead.
            self._rect._width = r.right - r.left # Setting _width directly to skip the onRead.
            self._rect._height = r.bottom - r.top # Setting _height directly to skip the onRead.

        def _onChange(oldBox, newBox):
            self.moveTo(newBox.left, newBox.top)
            self.resizeTo(newBox.width, newBox.height)

        r = self._getWindowRect(_hWnd)
        self._rect = pyrect.Rect(r.left, r.top, r.right - r.left, r.bottom - r.top, onChange=_onChange, onRead=_onRead)

    def __str__(self):
        r = self._getWindowRect(_hWnd)
        width = r.right - r.left
        height = r.bottom - r.top
        return '<%s left="%s", top="%s", width="%s", height="%s", title="%s">' % (self.__class__.__name__, r.left, r.top, width, height, self.title)


    def __repr__(self):
        return '%s(hWnd=%s)' % (self.__class__.__name__, self._hWnd)


    def __eq__(self, other):
        return isinstance(other, MacOSWindow) and self._hWnd == other._hWnd


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


