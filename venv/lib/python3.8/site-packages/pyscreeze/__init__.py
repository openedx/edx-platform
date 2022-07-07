# PyScreeze

"""
NOTE:
Apparently Pillow support on Ubuntu 64-bit has several additional steps since it doesn't have JPEG/PNG support out of the box. Description here:

https://stackoverflow.com/questions/7648200/pip-install-pil-e-tickets-1-no-jpeg-png-support
http://ubuntuforums.org/showthread.php?t=1751455
"""

__version__ = '0.1.28'

import collections
import datetime
import functools
import os
import subprocess
import sys
import time
import errno

from contextlib import contextmanager

try:
    from PIL import Image
    from PIL import ImageOps
    from PIL import ImageDraw
    if sys.platform == 'win32': # TODO - Pillow now supports ImageGrab on macOS.
        from PIL import ImageGrab
    _PILLOW_UNAVAILABLE = False
except ImportError:
    # We ignore this because failures due to Pillow not being installed
    # should only happen when the functions that specifically depend on
    # Pillow are called. The main use case is when PyAutoGUI imports
    # PyScreeze, but Pillow isn't installed because the user is running
    # some platform/version of Python that Pillow doesn't support, then
    # importing PyAutoGUI should not automatically fail because it
    # imports PyScreeze.
    # So we have a `pass` statement here since a failure to import
    # Pillow shouldn't crash PyScreeze.
    _PILLOW_UNAVAILABLE = True


try:
    import cv2, numpy
    useOpenCV = True
    RUNNING_CV_2 = cv2.__version__[0] < '3'
except ImportError:
    useOpenCV = False

RUNNING_PYTHON_2 = sys.version_info[0] == 2
if useOpenCV:
    if RUNNING_CV_2:
        LOAD_COLOR = cv2.CV_LOAD_IMAGE_COLOR
        LOAD_GRAYSCALE = cv2.CV_LOAD_IMAGE_GRAYSCALE
    else:
        LOAD_COLOR = cv2.IMREAD_COLOR
        LOAD_GRAYSCALE = cv2.IMREAD_GRAYSCALE

if not RUNNING_PYTHON_2:
    unicode = str # On Python 3, all the isinstance(spam, (str, unicode)) calls will work the same as Python 2.

if sys.platform == 'win32':
    # On Windows, the monitor scaling can be set to something besides normal 100%.
    # PyScreeze and Pillow needs to account for this to make accurate screenshots.
    # TODO - How does macOS and Linux handle monitor scaling?
    import ctypes
    try:
       ctypes.windll.user32.SetProcessDPIAware()
    except AttributeError:
        pass # Windows XP doesn't support monitor scaling, so just do nothing.

    try:
        import pygetwindow
    except ImportError:
        _PYGETWINDOW_UNAVAILABLE = True
    else:
        _PYGETWINDOW_UNAVAILABLE = False
else:
    _PYGETWINDOW_UNAVAILABLE = True


GRAYSCALE_DEFAULT = False

# For version 0.1.19 I changed it so that ImageNotFoundException was raised
# instead of returning None. In hindsight, this change came too late, so I'm
# changing it back to returning None. But I'm also including this option for
# folks who would rather have it raise an exception.
USE_IMAGE_NOT_FOUND_EXCEPTION = False

scrotExists = False
try:
    if sys.platform not in ('java', 'darwin', 'win32'):
        whichProc = subprocess.Popen(
            ['which', 'scrot'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        scrotExists = whichProc.wait() == 0
except OSError as ex:
    if ex.errno == errno.ENOENT:
        # if there is no "which" program to find scrot, then assume there
        # is no scrot.
        pass
    else:
        raise


if sys.platform == 'win32':
    from ctypes import windll

    # win32 DC(DeviceContext) Manager
    @contextmanager
    def __win32_openDC(hWnd):
        """
        TODO
        """
        hDC = windll.user32.GetDC(hWnd)
        if hDC == 0: #NULL
            raise WindowsError("windll.user32.GetDC failed : return NULL")
        try:
            yield hDC
        finally:
            windll.user32.ReleaseDC.argtypes = [ctypes.c_ssize_t, ctypes.c_ssize_t]
            if windll.user32.ReleaseDC(hWnd, hDC) == 0:
                raise WindowsError("windll.user32.ReleaseDC failed : return 0")

Box = collections.namedtuple('Box', 'left top width height')
Point = collections.namedtuple('Point', 'x y')
RGB = collections.namedtuple('RGB', 'red green blue')

class PyScreezeException(Exception):
    pass # This is a generic exception class raised when a PyScreeze-related error happens.

class ImageNotFoundException(PyScreezeException):
    pass # This is an exception class raised when the locate functions fail to locate an image.


def requiresPillow(wrappedFunction):
    """
    A decorator that marks a function as requiring Pillow to be installed.
    This raises PyScreezeException if Pillow wasn't imported.
    """
    @functools.wraps(wrappedFunction)
    def wrapper(*args, **kwargs):
        if _PILLOW_UNAVAILABLE:
            raise PyScreezeException('The Pillow package is required to use this function.')
        return wrappedFunction(*args, **kwargs)
    return wrapper

def _load_cv2(img, grayscale=None):
    """
    TODO
    """
    # load images if given filename, or convert as needed to opencv
    # Alpha layer just causes failures at this point, so flatten to RGB.
    # RGBA: load with -1 * cv2.CV_LOAD_IMAGE_COLOR to preserve alpha
    # to matchTemplate, need template and image to be the same wrt having alpha

    if grayscale is None:
        grayscale = GRAYSCALE_DEFAULT
    if isinstance(img, (str, unicode)):
        # The function imread loads an image from the specified file and
        # returns it. If the image cannot be read (because of missing
        # file, improper permissions, unsupported or invalid format),
        # the function returns an empty matrix
        # http://docs.opencv.org/3.0-beta/modules/imgcodecs/doc/reading_and_writing_images.html
        if grayscale:
            img_cv = cv2.imread(img, LOAD_GRAYSCALE)
        else:
            img_cv = cv2.imread(img, LOAD_COLOR)
        if img_cv is None:
            raise IOError("Failed to read %s because file is missing, "
                          "has improper permissions, or is an "
                          "unsupported or invalid format" % img)
    elif isinstance(img, numpy.ndarray):
        # don't try to convert an already-gray image to gray
        if grayscale and len(img.shape) == 3:  # and img.shape[2] == 3:
            img_cv = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            img_cv = img
    elif hasattr(img, 'convert'):
        # assume its a PIL.Image, convert to cv format
        img_array = numpy.array(img.convert('RGB'))
        img_cv = img_array[:, :, ::-1].copy()  # -1 does RGB -> BGR
        if grayscale:
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    else:
        raise TypeError('expected an image filename, OpenCV numpy array, or PIL image')
    return img_cv


def _locateAll_opencv(needleImage, haystackImage, grayscale=None, limit=10000, region=None, step=1,
                      confidence=0.999):
    """
    TODO - rewrite this
        faster but more memory-intensive than pure python
        step 2 skips every other row and column = ~3x faster but prone to miss;
            to compensate, the algorithm automatically reduces the confidence
            threshold by 5% (which helps but will not avoid all misses).
        limitations:
          - OpenCV 3.x & python 3.x not tested
          - RGBA images are treated as RBG (ignores alpha channel)
    """
    if grayscale is None:
        grayscale = GRAYSCALE_DEFAULT

    confidence = float(confidence)

    needleImage = _load_cv2(needleImage, grayscale)
    needleHeight, needleWidth = needleImage.shape[:2]
    haystackImage = _load_cv2(haystackImage, grayscale)

    if region:
        haystackImage = haystackImage[region[1]:region[1]+region[3],
                                      region[0]:region[0]+region[2]]
    else:
        region = (0, 0)  # full image; these values used in the yield statement
    if (haystackImage.shape[0] < needleImage.shape[0] or
        haystackImage.shape[1] < needleImage.shape[1]):
        # avoid semi-cryptic OpenCV error below if bad size
        raise ValueError('needle dimension(s) exceed the haystack image or region dimensions')

    if step == 2:
        confidence *= 0.95
        needleImage = needleImage[::step, ::step]
        haystackImage = haystackImage[::step, ::step]
    else:
        step = 1

    # get all matches at once, credit: https://stackoverflow.com/questions/7670112/finding-a-subimage-inside-a-numpy-image/9253805#9253805
    result = cv2.matchTemplate(haystackImage, needleImage, cv2.TM_CCOEFF_NORMED)
    match_indices = numpy.arange(result.size)[(result > confidence).flatten()]
    matches = numpy.unravel_index(match_indices[:limit], result.shape)

    if len(matches[0]) == 0:
        if USE_IMAGE_NOT_FOUND_EXCEPTION:
            raise ImageNotFoundException('Could not locate the image (highest confidence = %.3f)' % result.max())
        else:
            return

    # use a generator for API consistency:
    matchx = matches[1] * step + region[0]  # vectorized
    matchy = matches[0] * step + region[1]
    for x, y in zip(matchx, matchy):
        yield Box(x, y, needleWidth, needleHeight)


# TODO - We should consider renaming _locateAll_python to _locateAll_pillow, since Pillow is the real dependency.
@requiresPillow
def _locateAll_python(needleImage, haystackImage, grayscale=None, limit=None, region=None, step=1, confidence=None):
    """
    TODO
    """
    if confidence is not None:
        raise NotImplementedError('The confidence keyword argument is only available if OpenCV is installed.')

    # setup all the arguments
    if grayscale is None:
        grayscale = GRAYSCALE_DEFAULT

    needleFileObj = None
    if isinstance(needleImage, (str, unicode)):
        # 'image' is a filename, load the Image object
        needleFileObj = open(needleImage, 'rb')
        needleImage = Image.open(needleFileObj)

    haystackFileObj = None
    if isinstance(haystackImage, (str, unicode)):
        # 'image' is a filename, load the Image object
        haystackFileObj = open(haystackImage, 'rb')
        haystackImage = Image.open(haystackFileObj)

    if region is not None:
        haystackImage = haystackImage.crop((region[0], region[1], region[0] + region[2], region[1] + region[3]))
    else:
        region = (0, 0) # set to 0 because the code always accounts for a region

    if grayscale: # if grayscale mode is on, convert the needle and haystack images to grayscale
        needleImage = ImageOps.grayscale(needleImage)
        haystackImage = ImageOps.grayscale(haystackImage)
    else:
        # if not using grayscale, make sure we are comparing RGB images, not RGBA images.
        if needleImage.mode == 'RGBA':
            needleImage = needleImage.convert('RGB')
        if haystackImage.mode == 'RGBA':
            haystackImage = haystackImage.convert('RGB')

    # setup some constants we'll be using in this function
    needleWidth, needleHeight = needleImage.size
    haystackWidth, haystackHeight = haystackImage.size

    needleImageData = tuple(needleImage.getdata())
    haystackImageData = tuple(haystackImage.getdata())

    needleImageRows = [needleImageData[y * needleWidth:(y+1) * needleWidth] for y in range(needleHeight)] # LEFT OFF - check this
    needleImageFirstRow = needleImageRows[0]

    assert len(needleImageFirstRow) == needleWidth, 'For some reason, the calculated width of first row of the needle image is not the same as the width of the image.'
    assert [len(row) for row in needleImageRows] == [needleWidth] * needleHeight, 'For some reason, the needleImageRows aren\'t the same size as the original image.'

    numMatchesFound = 0

    # NOTE: After running tests/benchmarks.py on the following code, it seem that having a step
    # value greater than 1 does not give *any* significant performance improvements.
    # Since using a step higher than 1 makes for less accurate matches, it will be
    # set to 1.
    step = 1 # hard-code step as 1 until a way to improve it can be figured out.

    if step == 1:
        firstFindFunc = _kmp
    else:
        firstFindFunc = _steppingFind


    for y in range(haystackHeight): # start at the leftmost column
        for matchx in firstFindFunc(needleImageFirstRow, haystackImageData[y * haystackWidth:(y+1) * haystackWidth], step):
            foundMatch = True
            for searchy in range(1, needleHeight, step):
                haystackStart = (searchy + y) * haystackWidth + matchx
                if needleImageData[searchy * needleWidth:(searchy+1) * needleWidth] != haystackImageData[haystackStart:haystackStart + needleWidth]:
                    foundMatch = False
                    break
            if foundMatch:
                # Match found, report the x, y, width, height of where the matching region is in haystack.
                numMatchesFound += 1
                yield Box(matchx + region[0], y + region[1], needleWidth, needleHeight)
                if limit is not None and numMatchesFound >= limit:
                    # Limit has been reached. Close file handles.
                    if needleFileObj is not None:
                        needleFileObj.close()
                    if haystackFileObj is not None:
                        haystackFileObj.close()
                    return


    # There was no limit or the limit wasn't reached, but close the file handles anyway.
    if needleFileObj is not None:
        needleFileObj.close()
    if haystackFileObj is not None:
        haystackFileObj.close()

    if numMatchesFound == 0:
        if USE_IMAGE_NOT_FOUND_EXCEPTION:
            raise ImageNotFoundException('Could not locate the image.')
        else:
            return


def locate(needleImage, haystackImage, **kwargs):
    """
    TODO
    """
    # Note: The gymnastics in this function is because we want to make sure to exhaust the iterator so that the needle and haystack files are closed in locateAll.
    kwargs['limit'] = 1
    points = tuple(locateAll(needleImage, haystackImage, **kwargs))
    if len(points) > 0:
        return points[0]
    else:
        if USE_IMAGE_NOT_FOUND_EXCEPTION:
            raise ImageNotFoundException('Could not locate the image.')
        else:
            return None


def locateOnScreen(image, minSearchTime=0, **kwargs):
    """TODO - rewrite this
    minSearchTime - amount of time in seconds to repeat taking
    screenshots and trying to locate a match.  The default of 0 performs
    a single search.
    """
    start = time.time()
    while True:
        try:
            screenshotIm = screenshot(region=None) # the locateAll() function must handle cropping to return accurate coordinates, so don't pass a region here.
            retVal = locate(image, screenshotIm, **kwargs)
            try:
                screenshotIm.fp.close()
            except AttributeError:
                # Screenshots on Windows won't have an fp since they came from
                # ImageGrab, not a file. Screenshots on Linux will have fp set
                # to None since the file has been unlinked
                pass
            if retVal or time.time() - start > minSearchTime:
                return retVal
        except ImageNotFoundException:
            if time.time() - start > minSearchTime:
                if USE_IMAGE_NOT_FOUND_EXCEPTION:
                    raise
                else:
                    return None


def locateAllOnScreen(image, **kwargs):
    """
    TODO
    """

    # TODO - Should this raise an exception if zero instances of the image can be found on the screen, instead of always returning a generator?
    screenshotIm = screenshot(region=None) # the locateAll() function must handle cropping to return accurate coordinates, so don't pass a region here.
    retVal = locateAll(image, screenshotIm, **kwargs)
    try:
        screenshotIm.fp.close()
    except AttributeError:
        # Screenshots on Windows won't have an fp since they came from
        # ImageGrab, not a file. Screenshots on Linux will have fp set
        # to None since the file has been unlinked
        pass
    return retVal


def locateCenterOnScreen(image, **kwargs):
    """
    TODO
    """
    coords = locateOnScreen(image, **kwargs)
    if coords is None:
        return None
    else:
        return center(coords)

def locateOnWindow(image, title, **kwargs):
    """
    TODO
    """
    if _PYGETWINDOW_UNAVAILABLE:
        raise PyScreezeException('locateOnWindow() failed because PyGetWindow is not installed or is unsupported on this platform.')

    matchingWindows = pygetwindow.getWindowsWithTitle(title)
    if len(matchingWindows) == 0:
        raise PyScreezeException('Could not find a window with %s in the title' % (title))
    elif len(matchingWindows) > 1:
        raise PyScreezeException('Found multiple windows with %s in the title: %s' % (title, [str(win) for win in matchingWindows]))

    win = matchingWindows[0]
    win.activate()
    return locateOnScreen(image, region=(win.left, win.top, win.width, win.height), **kwargs)


@requiresPillow
def showRegionOnScreen(region, outlineColor='red', filename='_showRegionOnScreen.png'):
    """
    TODO
    """
    # TODO - This function is useful! Document it!
    screenshotIm = screenshot()
    draw = ImageDraw.Draw(screenshotIm)
    region = (region[0], region[1], region[2] + region[0], region[3] + region[1]) # convert from (left, top, right, bottom) to (left, top, width, height)
    draw.rectangle(region, outline=outlineColor)
    screenshotIm.save(filename)


@requiresPillow
def _screenshot_win32(imageFilename=None, region=None):
    """
    TODO
    """
    # TODO - Use the winapi to get a screenshot, and compare performance with ImageGrab.grab()
    # https://stackoverflow.com/a/3586280/1893164
    im = ImageGrab.grab()
    if region is not None:
        assert len(region) == 4, 'region argument must be a tuple of four ints'
        region = [int(x) for x in region]
        im = im.crop((region[0], region[1], region[2] + region[0], region[3] + region[1]))
    if imageFilename is not None:
        im.save(imageFilename)
    return im


def _screenshot_osx(imageFilename=None, region=None):
    """
    TODO
    """
    # TODO - use tmp name for this file.
    if imageFilename is None:
        tmpFilename = 'screenshot%s.png' % (datetime.datetime.now().strftime('%Y-%m%d_%H-%M-%S-%f'))
    else:
        tmpFilename = imageFilename
    subprocess.call(['screencapture', '-x', tmpFilename])
    im = Image.open(tmpFilename)

    if region is not None:
        assert len(region) == 4, 'region argument must be a tuple of four ints'
        region = [int(x) for x in region]
        im = im.crop((region[0], region[1], region[2] + region[0], region[3] + region[1]))
        os.unlink(tmpFilename) # delete image of entire screen to save cropped version
        im.save(tmpFilename)
    else:
        # force loading before unlinking, Image.open() is lazy
        im.load()

    if imageFilename is None:
        os.unlink(tmpFilename)
    return im


def _screenshot_linux(imageFilename=None, region=None):
    """
    TODO
    """
    if not scrotExists:
        raise NotImplementedError('"scrot" must be installed to use screenshot functions in Linux. Run: sudo apt-get install scrot')
    if imageFilename is None:
        tmpFilename = '.screenshot%s.png' % (datetime.datetime.now().strftime('%Y-%m%d_%H-%M-%S-%f'))
    else:
        tmpFilename = imageFilename
    if scrotExists:
        subprocess.call(['scrot', '-z', tmpFilename])
        im = Image.open(tmpFilename)

        if region is not None:
            assert len(region) == 4, 'region argument must be a tuple of four ints'
            region = [int(x) for x in region]
            im = im.crop((region[0], region[1], region[2] + region[0], region[3] + region[1]))
            os.unlink(tmpFilename) # delete image of entire screen to save cropped version
            im.save(tmpFilename)
        else:
            # force loading before unlinking, Image.open() is lazy
            im.load()

        if imageFilename is None:
            os.unlink(tmpFilename)
        return im
    else:
        raise Exception('The scrot program must be installed to take a screenshot with PyScreeze on Linux. Run: sudo apt-get install scrot')



def _kmp(needle, haystack, _dummy): # Knuth-Morris-Pratt search algorithm implementation (to be used by screen capture)
    """
    TODO
    """
    # build table of shift amounts
    shifts = [1] * (len(needle) + 1)
    shift = 1
    for pos in range(len(needle)):
        while shift <= pos and needle[pos] != needle[pos-shift]:
            shift += shifts[pos-shift]
        shifts[pos+1] = shift

    # do the actual search
    startPos = 0
    matchLen = 0
    for c in haystack:
        while matchLen == len(needle) or \
              matchLen >= 0 and needle[matchLen] != c:
            startPos += shifts[matchLen]
            matchLen -= shifts[matchLen]
        matchLen += 1
        if matchLen == len(needle):
            yield startPos


def _steppingFind(needle, haystack, step):
    """
    TODO
    """
    for startPos in range(0, len(haystack) - len(needle) + 1):
        foundMatch = True
        for pos in range(0, len(needle), step):
            if haystack[startPos + pos] != needle[pos]:
                foundMatch = False
                break
        if foundMatch:
            yield startPos


def center(coords):
    """
    Returns a `Point` object with the x and y set to an integer determined by the format of `coords`.

    The `coords` argument is a 4-integer tuple of (left, top, width, height).

    For example:

    >>> center((10, 10, 6, 8))
    Point(x=13, y=14)
    >>> center((10, 10, 7, 9))
    Point(x=13, y=14)
    >>> center((10, 10, 8, 10))
    Point(x=14, y=15)
    """

    # TODO - one day, add code to handle a Box namedtuple.
    return Point(coords[0] + int(coords[2] / 2), coords[1] + int(coords[3] / 2))


def pixelMatchesColor(x, y, expectedRGBColor, tolerance=0):
    """
    TODO
    """
    pix = pixel(x, y)
    if len(pix) == 3 or len(expectedRGBColor) == 3: #RGB mode
        r, g, b = pix[:3]
        exR, exG, exB = expectedRGBColor[:3]
        return (abs(r - exR) <= tolerance) and (abs(g - exG) <= tolerance) and (abs(b - exB) <= tolerance)
    elif len(pix) == 4 and len(expectedRGBColor) == 4: #RGBA mode
        r, g, b, a = pix
        exR, exG, exB, exA = expectedRGBColor
        return (abs(r - exR) <= tolerance) and (abs(g - exG) <= tolerance) and (abs(b - exB) <= tolerance) and (abs(a - exA) <= tolerance)
    else:
        assert False, 'Color mode was expected to be length 3 (RGB) or 4 (RGBA), but pixel is length %s and expectedRGBColor is length %s' % (len(pix), len(expectedRGBColor))

def pixel(x, y):
    """
    TODO
    """
    if sys.platform == 'win32':
        # On Windows, calling GetDC() and GetPixel() is twice as fast as using our screenshot() function.
        with __win32_openDC(0) as hdc: # handle will be released automatically
            color = windll.gdi32.GetPixel(hdc, x, y)
            if color < 0:
                raise WindowsError("windll.gdi32.GetPixel failed : return {}".format(color))
            # color is in the format 0xbbggrr https://msdn.microsoft.com/en-us/library/windows/desktop/dd183449(v=vs.85).aspx
            bbggrr = "{:0>6x}".format(color) # bbggrr => 'bbggrr' (hex)
            b, g, r = (int(bbggrr[i:i+2], 16) for i in range(0, 6, 2))
            return (r, g, b)
    else:
        # Need to select only the first three values of the color in
        # case the returned pixel has an alpha channel
        return RGB(*(screenshot().getpixel((x, y))[:3]))


# set the screenshot() function based on the platform running this module
if sys.platform.startswith('java'):
    raise NotImplementedError('Jython is not yet supported by PyScreeze.')
elif sys.platform == 'darwin':
    screenshot = _screenshot_osx
elif sys.platform == 'win32':
    screenshot = _screenshot_win32
else: # TODO - Make this more specific. "Anything else" does not necessarily mean "Linux".
    screenshot = _screenshot_linux

grab = screenshot # for compatibility with Pillow/PIL's ImageGrab module.

# set the locateAll function to use opencv if possible; python 3 needs opencv 3.0+
# TODO - Should this raise an exception if zero instances of the image can be found on the screen, instead of always returning a generator?
if useOpenCV:
    locateAll = _locateAll_opencv
    if not RUNNING_PYTHON_2 and cv2.__version__ < '3':
        locateAll = _locateAll_python
else:
    locateAll = _locateAll_python
