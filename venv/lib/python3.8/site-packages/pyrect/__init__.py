import doctest
import collections

# TODO - finish doc tests

# TODO - unit tests needed for get/set and Box named tuple

__version__ = "0.2.0"


# Constants for rectangle attributes:
TOP = "top"
BOTTOM = "bottom"
LEFT = "left"
RIGHT = "right"
TOPLEFT = "topleft"
TOPRIGHT = "topright"
BOTTOMLEFT = "bottomleft"
BOTTOMRIGHT = "bottomright"
MIDTOP = "midtop"
MIDRIGHT = "midright"
MIDLEFT = "midleft"
MIDBOTTOM = "midbottom"
CENTER = "center"
CENTERX = "centerx"
CENTERY = "centery"
WIDTH = "width"
HEIGHT = "height"
SIZE = "size"
BOX = "box"
AREA = "area"
PERIMETER = "perimeter"

Box = collections.namedtuple("Box", "left top width height")
Point = collections.namedtuple("Point", "x y")
Size = collections.namedtuple("Size", "width height")


class PyRectException(Exception):
    """
    This class exists for PyRect exceptions. If the PyRect module raises any
    non-PyRectException exceptions, this indicates there's a bug in PyRect.
    """

    pass


def _checkForIntOrFloat(arg):
    """Raises an exception if arg is not an int or float. Always returns None."""
    if not isinstance(arg, (int, float)):
        raise PyRectException(
            "argument must be int or float, not %s" % (arg.__class__.__name__)
        )


def _checkForInt(arg):
    """Raises an exception if arg is not an int. Always returns None."""
    if not isinstance(arg, int):
        raise PyRectException(
            "argument must be int or float, not %s" % (arg.__class__.__name__)
        )


def _checkForTwoIntOrFloatTuple(arg):
    try:
        if not isinstance(arg[0], (int, float)) or not isinstance(arg[1], (int, float)):
            raise PyRectException(
                "argument must be a two-item tuple containing int or float values"
            )
    except:
        raise PyRectException(
            "argument must be a two-item tuple containing int or float values"
        )


def _checkForFourIntOrFloatTuple(arg):
    try:
        if (
            not isinstance(arg[0], (int, float))
            or not isinstance(arg[1], (int, float))
            or not isinstance(arg[2], (int, float))
            or not isinstance(arg[3], (int, float))
        ):
            raise PyRectException(
                "argument must be a four-item tuple containing int or float values"
            )
    except:
        raise PyRectException(
            "argument must be a four-item tuple containing int or float values"
        )


def _collides(rectOrPoint1, rectOrPoint2):
    """Returns True if rectOrPoint1 and rectOrPoint2 collide with each other."""


def _getRectsAndPoints(rectsOrPoints):
    points = []
    rects = []
    for rectOrPoint in rectsOrPoints:
        try:
            _checkForTwoIntOrFloatTuple(rectOrPoint)
            points.append(rectOrPoint)
        except PyRectException:
            try:
                _checkForFourIntOrFloatTuple(rectOrPoint)
            except:
                raise PyRectException("argument is not a point or a rect tuple")
            rects.append(rectOrPoint)
    return (rects, points)


'''
def collideAnyBetween(rectsOrPoints):
    """Returns True if any of the (x, y) or (left, top, width, height) tuples
    in rectsOrPoints collides with any other point or box tuple in rectsOrPoints.

    >>> p1 = (50, 50)
    >>> p2 = (100, 100)
    >>> p3 = (50, 200)
    >>> r1 = (-50, -50, 20, 20)
    >>> r2 = (25, 25, 50, 50)
    >>> collideAnyBetween([p1, p2, p3, r1, r2]) # p1 and r2 collide
    True
    >>> collideAnyBetween([p1, p2, p3, r1])
    False
    """
    # TODO - needs to be complete

    # split up
    rects, points = _getRectsAndPoints(rectsOrPoints)

    # compare points with each other
    if len(points) > 1:
        for point in points:
            if point != points[0]:
                return False

    # TODO finish
'''


'''
def collideAllBetween(rectsOrPoints):
    """Returns True if any of the (x, y) or (left, top, width, height) tuples
    in rectsOrPoints collides with any other point or box tuple in rectsOrPoints.

    >>> p1 = (50, 50)
    >>> p2 = (100, 100)
    >>> p3 = (50, 200)
    >>> r1 = (-50, -50, 20, 20)
    >>> r2 = (25, 25, 50, 50)
    >>> collideAllBetween([p1, p2, p3, r1, r2])
    False
    >>> collideAllBetween([p1, p2, p3, r1])
    False
    >>> collideAllBetween([p1, r2]) # Everything in the list collides with each other.
    True
    """

    # Check for valid arguments
    try:
        for rectOrPoint in rectsOrPoints:
            if len(rectOrPoint) == 2:
                _checkForTwoIntOrFloatTuple(rectOrPoint)
            elif len(rectOrPoint) == 4:
                _checkForFourIntOrFloatTuple(rectOrPoint)
            else:
                raise PyRectException()
    except:
        raise PyRectException('Arguments in rectsOrPoints must be 2- or 4-integer/float tuples.')

    raise NotImplementedError # return a list of all rects or points that collide with any other in the argument
'''


class Rect(object):
    def __init__(
        self,
        left=0,
        top=0,
        width=0,
        height=0,
        enableFloat=False,
        readOnly=False,
        onChange=None,
        onRead=None,
    ):
        _checkForIntOrFloat(width)
        _checkForIntOrFloat(height)
        _checkForIntOrFloat(left)
        _checkForIntOrFloat(top)

        self._enableFloat = bool(enableFloat)
        self._readOnly = bool(readOnly)

        if onChange is not None and not callable(onChange):
            raise PyRectException(
                "onChange argument must be None or callable (function, method, etc.)"
            )
        self.onChange = onChange

        if onRead is not None and not callable(onRead):
            raise PyRectException(
                "onRead argument must be None or callable (function, method, etc.)"
            )
        self.onRead = onRead

        if enableFloat:
            self._width = float(width)
            self._height = float(height)
            self._left = float(left)
            self._top = float(top)
        else:
            self._width = int(width)
            self._height = int(height)
            self._left = int(left)
            self._top = int(top)

    # OPERATOR OVERLOADING / DUNDER METHODS
    def __repr__(self):
        """Return a string of the constructor function call to create this Rect object."""
        return "%s(left=%s, top=%s, width=%s, height=%s)" % (
            self.__class__.__name__,
            self._left,
            self._top,
            self._width,
            self._height,
        )

    def __str__(self):
        """Return a string representation of this Rect object."""
        return "(x=%s, y=%s, w=%s, h=%s)" % (
            self._left,
            self._top,
            self._width,
            self._height,
        )

    def callOnChange(self, oldLeft, oldTop, oldWidth, oldHeight):
        # Note: callOnChange() should be called *after* the attribute has been changed.
        # Note: This isn't thread safe; the attributes can change between the calling of this function and the code in the function running.
        if self.onChange is not None:
            self.onChange(
                Box(oldLeft, oldTop, oldWidth, oldHeight),
                Box(self._left, self._top, self._width, self._height),
            )

    @property
    def enableFloat(self):
        """
        A Boolean attribute that determines if this rectangle uses floating point
        numbers for its position and size. False, by default.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.enableFloat
        False
        >>> r.enableFloat = True
        >>> r.top = 3.14
        >>> r
        Rect(left=0.0, top=3.14, width=10.0, height=20.0)
        """
        return self._enableFloat

    @enableFloat.setter
    def enableFloat(self, value):
        if not isinstance(value, bool):
            raise PyRectException("enableFloat must be set to a bool value")
        self._enableFloat = value

        if self._enableFloat:
            self._left = float(self._left)
            self._top = float(self._top)
            self._width = float(self._width)
            self._height = float(self._height)
        else:
            self._left = int(self._left)
            self._top = int(self._top)
            self._width = int(self._width)
            self._height = int(self._height)

    # LEFT SIDE PROPERTY
    @property
    def left(self):
        """
        The x coordinate for the left edge of the rectangle. `x` is an alias for `left`.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.left
        0
        >>> r.left = 50
        >>> r
        Rect(left=50, top=0, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(LEFT)
        return self._left

    @left.setter
    def left(self, newLeft):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForIntOrFloat(newLeft)
        if (
            newLeft != self._left
        ):  # Only run this code if the size/position has changed.
            originalLeft = self._left
            if self._enableFloat:
                self._left = newLeft
            else:
                self._left = int(newLeft)
            self.callOnChange(originalLeft, self._top, self._width, self._height)

    x = left  # x is an alias for left

    # TOP SIDE PROPERTY
    @property
    def top(self):
        """
        The y coordinate for the top edge of the rectangle. `y` is an alias for `top`.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.top
        0
        >>> r.top = 50
        >>> r
        Rect(left=0, top=50, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(TOP)
        return self._top

    @top.setter
    def top(self, newTop):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForIntOrFloat(newTop)
        if newTop != self._top:  # Only run this code if the size/position has changed.
            originalTop = self._top
            if self._enableFloat:
                self._top = newTop
            else:
                self._top = int(newTop)
            self.callOnChange(self._left, originalTop, self._width, self._height)

    y = top  # y is an alias for top

    # RIGHT SIDE PROPERTY
    @property
    def right(self):
        """
        The x coordinate for the right edge of the rectangle.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.right
        10
        >>> r.right = 50
        >>> r
        Rect(left=40, top=0, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(RIGHT)
        return self._left + self._width

    @right.setter
    def right(self, newRight):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForIntOrFloat(newRight)
        if (
            newRight != self._left + self._width
        ):  # Only run this code if the size/position has changed.
            originalLeft = self._left
            if self._enableFloat:
                self._left = newRight - self._width
            else:
                self._left = int(newRight) - self._width
            self.callOnChange(originalLeft, self._top, self._width, self._height)

    # BOTTOM SIDE PROPERTY
    @property
    def bottom(self):
        """The y coordinate for the bottom edge of the rectangle.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.bottom
        20
        >>> r.bottom = 30
        >>> r
        Rect(left=0, top=10, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(BOTTOM)
        return self._top + self._height

    @bottom.setter
    def bottom(self, newBottom):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForIntOrFloat(newBottom)
        if (
            newBottom != self._top + self._height
        ):  # Only run this code if the size/position has changed.
            originalTop = self._top
            if self._enableFloat:
                self._top = newBottom - self._height
            else:
                self._top = int(newBottom) - self._height
            self.callOnChange(self._left, originalTop, self._width, self._height)

    # TOP LEFT CORNER PROPERTY
    @property
    def topleft(self):
        """
        The x and y coordinates for the top right corner of the rectangle, as a tuple.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.topleft
        (0, 0)
        >>> r.topleft = (30, 30)
        >>> r
        Rect(left=30, top=30, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(TOPLEFT)
        return Point(x=self._left, y=self._top)

    @topleft.setter
    def topleft(self, value):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForTwoIntOrFloatTuple(value)
        newLeft, newTop = value
        if (newLeft != self._left) or (
            newTop != self._top
        ):  # Only run this code if the size/position has changed.
            originalLeft = self._left
            originalTop = self._top
            if self._enableFloat:
                self._left = newLeft
                self._top = newTop
            else:
                self._left = int(newLeft)
                self._top = int(newTop)
            self.callOnChange(originalLeft, originalTop, self._width, self._height)

    # BOTTOM LEFT CORNER PROPERTY
    @property
    def bottomleft(self):
        """
        The x and y coordinates for the bottom right corner of the rectangle, as a tuple.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.bottomleft
        (0, 20)
        >>> r.bottomleft = (30, 30)
        >>> r
        Rect(left=30, top=10, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(BOTTOMLEFT)
        return Point(x=self._left, y=self._top + self._height)

    @bottomleft.setter
    def bottomleft(self, value):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForTwoIntOrFloatTuple(value)
        newLeft, newBottom = value
        if (newLeft != self._left) or (
            newBottom != self._top + self._height
        ):  # Only run this code if the size/position has changed.
            originalLeft = self._left
            originalTop = self._top
            if self._enableFloat:
                self._left = newLeft
                self._top = newBottom - self._height
            else:
                self._left = int(newLeft)
                self._top = int(newBottom) - self._height
            self.callOnChange(originalLeft, originalTop, self._width, self._height)

    # TOP RIGHT CORNER PROPERTY
    @property
    def topright(self):
        """
        The x and y coordinates for the top right corner of the rectangle, as a tuple.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.topright
        (10, 0)
        >>> r.topright = (30, 30)
        >>> r
        Rect(left=20, top=30, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(TOPRIGHT)
        return Point(x=self._left + self._width, y=self._top)

    @topright.setter
    def topright(self, value):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForTwoIntOrFloatTuple(value)
        newRight, newTop = value
        if (newRight != self._left + self._width) or (
            newTop != self._top
        ):  # Only run this code if the size/position has changed.
            originalLeft = self._left
            originalTop = self._top
            if self._enableFloat:
                self._left = newRight - self._width
                self._top = newTop
            else:
                self._left = int(newRight) - self._width
                self._top = int(newTop)
            self.callOnChange(originalLeft, originalTop, self._width, self._height)

    # BOTTOM RIGHT CORNER PROPERTY
    @property
    def bottomright(self):
        """
        The x and y coordinates for the bottom right corner of the rectangle, as a tuple.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.bottomright
        (10, 20)
        >>> r.bottomright = (30, 30)
        >>> r
        Rect(left=20, top=10, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(BOTTOMRIGHT)
        return Point(x=self._left + self._width, y=self._top + self._height)

    @bottomright.setter
    def bottomright(self, value):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForTwoIntOrFloatTuple(value)
        newRight, newBottom = value
        if (newBottom != self._top + self._height) or (
            newRight != self._left + self._width
        ):  # Only run this code if the size/position has changed.
            originalLeft = self._left
            originalTop = self._top
            if self._enableFloat:
                self._left = newRight - self._width
                self._top = newBottom - self._height
            else:
                self._left = int(newRight) - self._width
                self._top = int(newBottom) - self._height
            self.callOnChange(originalLeft, originalTop, self._width, self._height)

    # MIDDLE OF TOP SIDE PROPERTY
    @property
    def midtop(self):
        """
        The x and y coordinates for the midpoint of the top edge of the rectangle, as a tuple.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.midtop
        (5, 0)
        >>> r.midtop = (40, 50)
        >>> r
        Rect(left=35, top=50, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(MIDTOP)
        if self._enableFloat:
            return Point(x=self._left + (self._width / 2.0), y=self._top)
        else:
            return Point(x=self._left + (self._width // 2), y=self._top)

    @midtop.setter
    def midtop(self, value):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForTwoIntOrFloatTuple(value)
        newMidTop, newTop = value
        originalLeft = self._left
        originalTop = self._top
        if self._enableFloat:
            if (newMidTop != self._left + self._width / 2.0) or (
                newTop != self._top
            ):  # Only run this code if the size/position has changed.
                self._left = newMidTop - (self._width / 2.0)
                self._top = newTop
                self.callOnChange(originalLeft, originalTop, self._width, self._height)
        else:
            if (newMidTop != self._left + self._width // 2) or (
                newTop != self._top
            ):  # Only run this code if the size/position has changed.
                self._left = int(newMidTop) - (self._width // 2)
                self._top = int(newTop)
                self.callOnChange(originalLeft, originalTop, self._width, self._height)

    # MIDDLE OF BOTTOM SIDE PROPERTY
    @property
    def midbottom(self):
        """
        The x and y coordinates for the midpoint of the bottom edge of the rectangle, as a tuple.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.midbottom
        (5, 20)
        >>> r.midbottom = (40, 50)
        >>> r
        Rect(left=35, top=30, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(MIDBOTTOM)
        if self._enableFloat:
            return Point(x=self._left + (self._width / 2.0), y=self._top + self._height)
        else:
            return Point(x=self._left + (self._width // 2), y=self._top + self._height)

    @midbottom.setter
    def midbottom(self, value):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForTwoIntOrFloatTuple(value)
        newMidBottom, newBottom = value
        originalLeft = self._left
        originalTop = self._top
        if self._enableFloat:
            if (newMidBottom != self._left + self._width / 2.0) or (
                newBottom != self._top + self._height
            ):  # Only run this code if the size/position has changed.
                self._left = newMidBottom - (self._width / 2.0)
                self._top = newBottom - self._height
                self.callOnChange(originalLeft, originalTop, self._width, self._height)
        else:
            if (newMidBottom != self._left + self._width // 2) or (
                newBottom != self._top + self._height
            ):  # Only run this code if the size/position has changed.
                self._left = int(newMidBottom) - (self._width // 2)
                self._top = int(newBottom) - self._height
                self.callOnChange(originalLeft, originalTop, self._width, self._height)

    # MIDDLE OF LEFT SIDE PROPERTY
    @property
    def midleft(self):
        """
        The x and y coordinates for the midpoint of the left edge of the rectangle, as a tuple.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.midleft
        (0, 10)
        >>> r.midleft = (40, 50)
        >>> r
        Rect(left=40, top=40, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(MIDLEFT)
        if self._enableFloat:
            return Point(x=self._left, y=self._top + (self._height / 2.0))
        else:
            return Point(x=self._left, y=self._top + (self._height // 2))

    @midleft.setter
    def midleft(self, value):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForTwoIntOrFloatTuple(value)
        newLeft, newMidLeft = value
        originalLeft = self._left
        originalTop = self._top
        if self._enableFloat:
            if (newLeft != self._left) or (
                newMidLeft != self._top + (self._height / 2.0)
            ):  # Only run this code if the size/position has changed.
                self._left = newLeft
                self._top = newMidLeft - (self._height / 2.0)
                self.callOnChange(originalLeft, originalTop, self._width, self._height)
        else:
            if (newLeft != self._left) or (
                newMidLeft != self._top + (self._height // 2)
            ):  # Only run this code if the size/position has changed.
                self._left = int(newLeft)
                self._top = int(newMidLeft) - (self._height // 2)
                self.callOnChange(originalLeft, originalTop, self._width, self._height)

    # MIDDLE OF RIGHT SIDE PROPERTY
    @property
    def midright(self):
        """
        The x and y coordinates for the midpoint of the right edge of the rectangle, as a tuple.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.midright
        (10, 10)
        >>> r.midright = (40, 50)
        >>> r
        Rect(left=30, top=40, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(MIDRIGHT)
        if self._enableFloat:
            return Point(x=self._left + self._width, y=self._top + (self._height / 2.0))
        else:
            return Point(x=self._left + self._width, y=self._top + (self._height // 2))

    @midright.setter
    def midright(self, value):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForTwoIntOrFloatTuple(value)
        newRight, newMidRight = value
        originalLeft = self._left
        originalTop = self._top
        if self._enableFloat:
            if (newRight != self._left + self._width) or (
                newMidRight != self._top + self._height / 2.0
            ):  # Only run this code if the size/position has changed.
                self._left = newRight - self._width
                self._top = newMidRight - (self._height / 2.0)
                self.callOnChange(originalLeft, originalTop, self._width, self._height)
        else:
            if (newRight != self._left + self._width) or (
                newMidRight != self._top + self._height // 2
            ):  # Only run this code if the size/position has changed.
                self._left = int(newRight) - self._width
                self._top = int(newMidRight) - (self._height // 2)
                self.callOnChange(originalLeft, originalTop, self._width, self._height)

    # CENTER POINT PROPERTY
    @property
    def center(self):
        """
        The x and y coordinates for the center of the rectangle, as a tuple.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.center
        (5, 10)
        >>> r.center = (40, 50)
        >>> r
        Rect(left=35, top=40, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(CENTER)
        if self._enableFloat:
            return Point(
                x=self._left + (self._width / 2.0), y=self._top + (self._height / 2.0)
            )
        else:
            return Point(
                x=self._left + (self._width // 2), y=self._top + (self._height // 2)
            )

    @center.setter
    def center(self, value):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForTwoIntOrFloatTuple(value)
        newCenterx, newCentery = value
        originalLeft = self._left
        originalTop = self._top
        if self._enableFloat:
            if (newCenterx != self._left + self._width / 2.0) or (
                newCentery != self._top + self._height / 2.0
            ):  # Only run this code if the size/position has changed.
                self._left = newCenterx - (self._width / 2.0)
                self._top = newCentery - (self._height / 2.0)
                self.callOnChange(originalLeft, originalTop, self._width, self._height)
        else:
            if (newCenterx != self._left + self._width // 2) or (
                newCentery != self._top + self._height // 2
            ):  # Only run this code if the size/position has changed.
                self._left = int(newCenterx) - (self._width // 2)
                self._top = int(newCentery) - (self._height // 2)
                self.callOnChange(originalLeft, originalTop, self._width, self._height)

    # X COORDINATE OF CENTER POINT PROPERTY
    @property
    def centerx(self):
        """
        The x coordinate for the center of the rectangle, as a tuple.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.centerx
        5
        >>> r.centerx = 50
        >>> r
        Rect(left=45, top=0, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(CENTERX)
        if self._enableFloat:
            return self._left + (self._width / 2.0)
        else:
            return self._left + (self._width // 2)

    @centerx.setter
    def centerx(self, newCenterx):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForIntOrFloat(newCenterx)
        originalLeft = self._left
        if self._enableFloat:
            if (
                newCenterx != self._left + self._width / 2.0
            ):  # Only run this code if the size/position has changed.
                self._left = newCenterx - (self._width / 2.0)
                self.callOnChange(originalLeft, self._top, self._width, self._height)
        else:
            if (
                newCenterx != self._left + self._width // 2
            ):  # Only run this code if the size/position has changed.
                self._left = int(newCenterx) - (self._width // 2)
                self.callOnChange(originalLeft, self._top, self._width, self._height)

    # Y COORDINATE OF CENTER POINT PROPERTY
    @property
    def centery(self):
        """
        The y coordinate for the center of the rectangle, as a tuple.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.centery
        10
        >>> r.centery = 50
        >>> r
        Rect(left=0, top=40, width=10, height=20)
        """
        if self.onRead is not None:
            self.onRead(CENTERY)
        if self._enableFloat:
            return self._top + (self._height / 2.0)
        else:
            return self._top + (self._height // 2)

    @centery.setter
    def centery(self, newCentery):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForIntOrFloat(newCentery)
        originalTop = self._top
        if self._enableFloat:
            if (
                newCentery != self._top + self._height / 2.0
            ):  # Only run this code if the size/position has changed.
                self._top = newCentery - (self._height / 2.0)
                self.callOnChange(self._left, originalTop, self._width, self._height)
        else:
            if (
                newCentery != self._top + self._height // 2
            ):  # Only run this code if the size/position has changed.
                self._top = int(newCentery) - (self._height // 2)
                self.callOnChange(self._left, originalTop, self._width, self._height)

    # SIZE PROPERTY (i.e. (width, height))
    @property
    def size(self):
        """
        The width and height of the rectangle, as a tuple.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.size
        (10, 20)
        >>> r.size = (40, 50)
        >>> r
        Rect(left=0, top=0, width=40, height=50)
        """
        if self.onRead is not None:
            self.onRead(SIZE)
        return Size(width=self._width, height=self._height)

    @size.setter
    def size(self, value):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForTwoIntOrFloatTuple(value)
        newWidth, newHeight = value
        if newWidth != self._width or newHeight != self._height:
            originalWidth = self._width
            originalHeight = self._height
            if self._enableFloat:
                self._width = newWidth
                self._height = newHeight
            else:
                self._width = int(newWidth)
                self._height = int(newHeight)
            self.callOnChange(self._left, self._top, originalWidth, originalHeight)

    # WIDTH PROPERTY
    @property
    def width(self):
        """
        The width of the rectangle. `w` is an alias for `width`.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.width
        10
        >>> r.width = 50
        >>> r
        Rect(left=0, top=0, width=50, height=20)
        """
        if self.onRead is not None:
            self.onRead(WIDTH)
        return self._width

    @width.setter
    def width(self, newWidth):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForIntOrFloat(newWidth)
        if (
            newWidth != self._width
        ):  # Only run this code if the size/position has changed.
            originalWidth = self._width
            if self._enableFloat:
                self._width = newWidth
            else:
                self._width = int(newWidth)
            self.callOnChange(self._left, self._top, originalWidth, self._height)

    w = width

    # HEIGHT PROPERTY
    @property
    def height(self):
        """
        The height of the rectangle. `h` is an alias for `height`

        >>> r = Rect(0, 0, 10, 20)
        >>> r.height
        20
        >>> r.height = 50
        >>> r
        Rect(left=0, top=0, width=10, height=50)
        """
        if self.onRead is not None:
            self.onRead(HEIGHT)
        return self._height

    @height.setter
    def height(self, newHeight):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForIntOrFloat(newHeight)
        if (
            newHeight != self._height
        ):  # Only run this code if the size/position has changed.
            originalHeight = self._height
            if self._enableFloat:
                self._height = newHeight
            else:
                self._height = int(newHeight)
            self.callOnChange(self._left, self._top, self._width, originalHeight)

    h = height

    # AREA PROPERTY
    @property
    def area(self):
        """The area of the `Rect`, which is simply the width times the height.
        This is a read-only attribute.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.area
        200
        """
        if self.onRead is not None:
            self.onRead(AREA)
        return self._width * self._height


    # PERIMETER PROPERTY
    @property
    def perimeter(self):
        """The perimeter of the `Rect`, which is simply the (width + height) * 2.
        This is a read-only attribute.

        >>> r = Rect(0, 0, 10, 20)
        >>> r.area
        200
        """
        if self.onRead is not None:
            self.onRead(AREA)
        return (self._width + self._height) * 2


    # BOX PROPERTY
    @property
    def box(self):
        """A tuple of four integers: (left, top, width, height).

        >>> r = Rect(0, 0, 10, 20)
        >>> r.box
        (0, 0, 10, 20)
        >>> r.box = (5, 15, 100, 200)
        >>> r.box
        (5, 15, 100, 200)"""
        if self.onRead is not None:
            self.onRead(BOX)
        return Box(
            left=self._left, top=self._top, width=self._width, height=self._height
        )

    @box.setter
    def box(self, value):
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForFourIntOrFloatTuple(value)
        newLeft, newTop, newWidth, newHeight = value
        if (
            (newLeft != self._left)
            or (newTop != self._top)
            or (newWidth != self._width)
            or (newHeight != self._height)
        ):
            originalLeft = self._left
            originalTop = self._top
            originalWidth = self._width
            originalHeight = self._height
            if self._enableFloat:
                self._left = float(newLeft)
                self._top = float(newTop)
                self._width = float(newWidth)
                self._height = float(newHeight)
            else:
                self._left = int(newLeft)
                self._top = int(newTop)
                self._width = int(newWidth)
                self._height = int(newHeight)
            self.callOnChange(originalLeft, originalTop, originalWidth, originalHeight)

    def get(self, rectAttrName):
        # Access via the properties so that it triggers onRead().
        if rectAttrName == TOP:
            return self.top
        elif rectAttrName == BOTTOM:
            return self.bottom
        elif rectAttrName == LEFT:
            return self.left
        elif rectAttrName == RIGHT:
            return self.right
        elif rectAttrName == TOPLEFT:
            return self.topleft
        elif rectAttrName == TOPRIGHT:
            return self.topright
        elif rectAttrName == BOTTOMLEFT:
            return self.bottomleft
        elif rectAttrName == BOTTOMRIGHT:
            return self.bottomright
        elif rectAttrName == MIDTOP:
            return self.midtop
        elif rectAttrName == MIDBOTTOM:
            return self.midbottom
        elif rectAttrName == MIDLEFT:
            return self.midleft
        elif rectAttrName == MIDRIGHT:
            return self.midright
        elif rectAttrName == CENTER:
            return self.center
        elif rectAttrName == CENTERX:
            return self.centerx
        elif rectAttrName == CENTERY:
            return self.centery
        elif rectAttrName == WIDTH:
            return self.width
        elif rectAttrName == HEIGHT:
            return self.height
        elif rectAttrName == SIZE:
            return self.size
        elif rectAttrName == AREA:
            return self.area
        elif rectAttrName == BOX:
            return self.box
        else:
            raise PyRectException("'%s' is not a valid attribute name" % (rectAttrName))

    def set(self, rectAttrName, value):
        # Set via the properties so that it triggers onChange().
        if rectAttrName == TOP:
            self.top = value
        elif rectAttrName == BOTTOM:
            self.bottom = value
        elif rectAttrName == LEFT:
            self.left = value
        elif rectAttrName == RIGHT:
            self.right = value
        elif rectAttrName == TOPLEFT:
            self.topleft = value
        elif rectAttrName == TOPRIGHT:
            self.topright = value
        elif rectAttrName == BOTTOMLEFT:
            self.bottomleft = value
        elif rectAttrName == BOTTOMRIGHT:
            self.bottomright = value
        elif rectAttrName == MIDTOP:
            self.midtop = value
        elif rectAttrName == MIDBOTTOM:
            self.midbottom = value
        elif rectAttrName == MIDLEFT:
            self.midleft = value
        elif rectAttrName == MIDRIGHT:
            self.midright = value
        elif rectAttrName == CENTER:
            self.center = value
        elif rectAttrName == CENTERX:
            self.centerx = value
        elif rectAttrName == CENTERY:
            self.centery = value
        elif rectAttrName == WIDTH:
            self.width = value
        elif rectAttrName == HEIGHT:
            self.height = value
        elif rectAttrName == SIZE:
            self.size = value
        elif rectAttrName == AREA:
            raise PyRectException("area is a read-only attribute")
        elif rectAttrName == BOX:
            self.box = value
        else:
            raise PyRectException("'%s' is not a valid attribute name" % (rectAttrName))

    def move(self, xOffset, yOffset):
        """Moves this Rect object by the given offsets. The xOffset and yOffset
        arguments can be any integer value, positive or negative.
        >>> r = Rect(0, 0, 100, 100)
        >>> r.move(10, 20)
        >>> r
        Rect(left=10, top=20, width=100, height=100)
        """
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        _checkForIntOrFloat(xOffset)
        _checkForIntOrFloat(yOffset)
        if self._enableFloat:
            self._left += xOffset
            self._top += yOffset
        else:
            self._left += int(xOffset)
            self._top += int(yOffset)

    def copy(self):
        """Return a copied `Rect` object with the same position and size as this
        `Rect` object.

        >>> r1 = Rect(0, 0, 100, 150)
        >>> r2 = r1.copy()
        >>> r1 == r2
        True
        >>> r2
        Rect(left=0, top=0, width=100, height=150)
        """
        return Rect(
            self._left,
            self._top,
            self._width,
            self._height,
            self._enableFloat,
            self._readOnly,
        )

    def inflate(self, widthChange=0, heightChange=0):
        """Increases the size of this Rect object by the given offsets. The
        rectangle's center doesn't move. Negative values will shrink the
        rectangle.

        >>> r = Rect(0, 0, 100, 150)
        >>> r.inflate(20, 40)
        >>> r
        Rect(left=-10, top=-20, width=120, height=190)
        """
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        originalCenter = self.center
        self.width += widthChange
        self.height += heightChange
        self.center = originalCenter

    def clamp(self, otherRect):
        """Centers this Rect object at the center of otherRect.

        >>> r1 =Rect(0, 0, 100, 100)
        >>> r2 = Rect(-20, -90, 50, 50)
        >>> r2.clamp(r1)
        >>> r2
        Rect(left=25, top=25, width=50, height=50)
        >>> r1.center == r2.center
        True
        """
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        self.center = otherRect.center

    '''
    def intersection(self, otherRect):
        """Returns a new Rect object of the overlapping area between this
        Rect object and otherRect.

        `clip()` is an alias for `intersection()`.
        """
        pass

    clip = intersection
    '''

    def union(self, otherRect):
        """Adjusts the width and height to also cover the area of `otherRect`.

        >>> r1 = Rect(0, 0, 100, 100)
        >>> r2 = Rect(-10, -10, 100, 100)
        >>> r1.union(r2)
        >>> r1
        Rect(left=-10, top=-10, width=110, height=110)
        """

        # TODO - Change otherRect so that it could be a point as well.

        unionLeft = min(self._left, otherRect._left)
        unionTop = min(self._top, otherRect._top)
        unionRight = max(self.right, otherRect.right)
        unionBottom = max(self.bottom, otherRect.bottom)

        self._left = unionLeft
        self._top = unionTop
        self._width = unionRight - unionLeft
        self._height = unionBottom - unionTop

    def unionAll(self, otherRects):
        """Adjusts the width and height to also cover all the `Rect` objects in
        the `otherRects` sequence.

        >>> r = Rect(0, 0, 100, 100)
        >>> r1 = Rect(0, 0, 150, 100)
        >>> r2 = Rect(-10, -10, 100, 100)
        >>> r.unionAll([r1, r2])
        >>> r
        Rect(left=-10, top=-10, width=160, height=110)
        """

        # TODO - Change otherRect so that it could be a point as well.

        otherRects = list(otherRects)
        otherRects.append(self)

        unionLeft = min([r._left for r in otherRects])
        unionTop = min([r._top for r in otherRects])
        unionRight = max([r.right for r in otherRects])
        unionBottom = max([r.bottom for r in otherRects])

        self._left = unionLeft
        self._top = unionTop
        self._width = unionRight - unionLeft
        self._height = unionBottom - unionTop

    """
    def fit(self, other):
        pass # TODO - needs to be complete
    """

    def normalize(self):
        """Rect objects with a negative width or height cover a region where the
        right/bottom edge is to the left/above of the left/top edge, respectively.
        The `normalize()` method sets the `width` and `height` to positive if they
        were negative.

        The Rect stays in the same place, though with the `top` and `left`
        attributes representing the true top and left side.

        >>> r = Rect(0, 0, -10, -20)
        >>> r.normalize()
        >>> r
        Rect(left=-10, top=-20, width=10, height=20)
        """
        if self._readOnly:
            raise PyRectException("Rect object is read-only")

        if self._width < 0:
            self._width = -self._width
            self._left -= self._width
        if self._height < 0:
            self._height = -self._height
            self._top -= self._height
        # Note: No need to intify here, since the four attributes should already be ints and no multiplication was done.

    def __contains__(
        self, value
    ):  # for either points or other Rect objects. For Rects, the *entire* Rect must be in this Rect.
        if isinstance(value, Rect):
            return (
                value.topleft in self
                and value.topright in self
                and value.bottomleft in self
                and value.bottomright in self
            )

        # Check if value is an (x, y) sequence or a (left, top, width, height) sequence.
        try:
            len(value)
        except:
            raise PyRectException(
                "in <Rect> requires an (x, y) tuple, a (left, top, width, height) tuple, or a Rect object as left operand, not %s"
                % (value.__class__.__name__)
            )

        if len(value) == 2:
            # Assume that value is an (x, y) sequence.
            _checkForTwoIntOrFloatTuple(value)
            x, y = value
            return (
                self._left < x < self._left + self._width
                and self._top < y < self._top + self._height
            )

        elif len(value) == 4:
            # Assume that value is an (x, y) sequence.
            _checkForFourIntOrFloatTuple(value)
            left, top, width, height = value
            return (
                (left, top) in self
                and (left + width, top) in self
                and (left, top + height) in self
                and (left + width, top + height) in self
            )
        else:
            raise PyRectException(
                "in <Rect> requires an (x, y) tuple, a (left, top, width, height) tuple, or a Rect object as left operand, not %s"
                % (value.__class__.__name__)
            )

    def collide(self, value):
        """Returns `True` if value collides with this `Rect` object, where value can
        be an (x, y) tuple, a (left, top, width, height) box tuple, or another `Rect`
        object. If value represents a rectangular area, any part of that area
        can collide with this `Rect` object to make `collide()` return `True`.
        Otherwise, returns `False`."""

        # Note: This code is similar to __contains__(), with some minor changes
        # because __contains__() requires the rectangular are to be COMPELTELY
        # within the Rect object.
        if isinstance(value, Rect):
            return (
                value.topleft in self
                or value.topright in self
                or value.bottomleft in self
                or value.bottomright in self
            )

        # Check if value is an (x, y) sequence or a (left, top, width, height) sequence.
        try:
            len(value)
        except:
            raise PyRectException(
                "in <Rect> requires an (x, y) tuple, a (left, top, width, height) tuple, or a Rect object as left operand, not %s"
                % (value.__class__.__name__)
            )

        if len(value) == 2:
            # Assume that value is an (x, y) sequence.
            _checkForTwoIntOrFloatTuple(value)
            x, y = value
            return (
                self._left < x < self._left + self._width
                and self._top < y < self._top + self._height
            )

        elif len(value) == 4:
            # Assume that value is an (x, y) sequence.
            left, top, width, height = value
            return (
                (left, top) in self
                or (left + width, top) in self
                or (left, top + height) in self
                or (left + width, top + height) in self
            )
        else:
            raise PyRectException(
                "in <Rect> requires an (x, y) tuple, a (left, top, width, height) tuple, or a Rect object as left operand, not %s"
                % (value.__class__.__name__)
            )

    '''
    def collideAny(self, rectsOrPoints):
        """Returns True if any of the (x, y) or (left, top, width, height)
        tuples in rectsOrPoints is inside this Rect object.

        >> r = Rect(0, 0, 100, 100)
        >> p1 = (150, 80)
        >> p2 = (100, 100) # This point collides.
        >> r.collideAny([p1, p2])
        True
        >> r1 = Rect(50, 50, 10, 20) # This Rect collides.
        >> r.collideAny([r1])
        True
        >> r.collideAny([p1, p2, r1])
        True
        """
        # TODO - needs to be complete
        pass # returns True or False
        raise NotImplementedError
'''

    '''
    def collideAll(self, rectsOrPoints):
        """Returns True if all of the (x, y) or (left, top, width, height)
        tuples in rectsOrPoints is inside this Rect object.
        """

        pass # return a list of all rects or points that collide with any other in the argument
        raise NotImplementedError
'''

    # TODO - Add overloaded operators for + - * / and others once we can determine actual use cases for them.

    """NOTE: All of the comparison magic methods compare the box tuple of Rect
    objects. This is the behavior of the pygame Rect objects. Originally,
    I thought about having the <, <=, >, and >= operators compare the area
    of Rect objects. But at the same time, I wanted to have == and != compare
    not just area, but all four left, top, width, and height attributes.
    But that's weird to have different comparison operators comparing different
    features of a rectangular area. So I just defaulted to what Pygame does
    and compares the box tuple. This means that the == and != operators are
    the only really useful comparison operators, so I decided to ditch the
    other operators altogether and just have Rect only support == and !=.
    """

    def __eq__(self, other):
        if isinstance(other, Rect):
            return other.box == self.box
        else:
            raise PyRectException(
                "Rect objects can only be compared with other Rect objects"
            )

    def __ne__(self, other):
        if isinstance(other, Rect):
            return other.box != self.box
        else:
            raise PyRectException(
                "Rect objects can only be compared with other Rect objects"
            )


if __name__ == "__main__":
    print(doctest.testmod())
