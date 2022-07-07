# MouseInfo by Al Sweigart al@inventwithpython.com

# Note: how to specify where a tkintr window opens:
# https://stackoverflow.com/questions/14910858/how-to-specify-where-a-tkinter-window-opens

"""
Features we should consider adding:
* Register a global hotkey for copying/logging info. (Should this hotkey be configurable?)

Features that have been considered and rejected:

* The Save Log/Save Screenshot buttons should open a file dialog box.
* The Save Log button should append text, instead of overwrite it.
* The log text area should prepopulate itself with the contents of the given filename.
* The button delay should be configurable instead of just set to 3 seconds.
"""

__version__ = '0.1.3'
import pyperclip, sys, os, platform, webbrowser

#from enum import Enum
from ctypes import (
    c_bool, c_int32, c_int64, c_size_t, c_uint16, c_uint32, c_void_p,
    cdll, util,
)

# =========================================================================
# Originally, these functions were pulled in from PyAutoGUI. However, to
# make this module independent of PyAutoGUI, the code for these functions
# has been copy/pasted into the following section:
# NOTE: Any bug fixes for these functions in PyAutoGUI will have to be
# manually merged into MouseInfo.
#from pyautogui import position, screenshot, size
# =========================================================================
# Alternatively, this code makes this application not dependent on PyAutoGUI
# by copying the code for the position() and screenshot() functions into this
# source code file.
import datetime, subprocess

try:
    from PIL import Image
    _PILLOW_INSTALLED = True
except ImportError:
    _PILLOW_INSTALLED = False

if sys.platform == 'win32':
    import ctypes

    if _PILLOW_INSTALLED:
        from PIL import ImageGrab

    # Makes this process aware of monitor scaling so the screenshots are correctly sized:
    try:
       ctypes.windll.user32.SetProcessDPIAware()
    except AttributeError:
        pass # Windows XP doesn't support this, so just do nothing.

    dc = ctypes.windll.user32.GetDC(0)

    class POINT(ctypes.Structure):
        _fields_ = [('x', ctypes.c_long),
                    ('y', ctypes.c_long)]

    def _winPosition():
        cursor = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor))
        return (cursor.x, cursor.y)
    position = _winPosition


    def _winScreenshot(filename=None):
        # TODO - Use the winapi to get a screenshot, and compare performance with ImageGrab.grab()
        # https://stackoverflow.com/a/3586280/1893164
        try:
            im = ImageGrab.grab()
            if filename is not None:
                im.save(filename)
        except NameError:
            raise ImportError('Pillow module must be installed to use screenshot functions on Windows.')
        return im
    screenshot = _winScreenshot

    def _winSize():
        return (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
    size = _winSize

    def _winGetPixel(x, y):
        colorRef = ctypes.windll.gdi32.GetPixel(dc, x, y)  # A COLORREF value as 0x00bbggrr. See https://docs.microsoft.com/en-us/windows/win32/gdi/colorref
        red = colorRef % 256
        colorRef //= 256
        green = colorRef % 256
        colorRef //= 256
        blue = colorRef

        return (red, green, blue)
    getPixel = _winGetPixel


elif sys.platform == 'darwin':
    from rubicon.objc import ObjCClass, CGPoint
    from rubicon.objc.types import register_preferred_encoding

    #####################################################################

    appkit = cdll.LoadLibrary(util.find_library('AppKit'))

    NSEvent = ObjCClass('NSEvent')
    NSEvent.declare_class_property('mouseLocation')
    # NSSystemDefined = ObjCClass('NSSystemDefined')

    #####################################################################

    core_graphics = cdll.LoadLibrary(util.find_library('CoreGraphics'))

    CGDirectDisplayID = c_uint32

    CGEventRef = c_void_p
    register_preferred_encoding(b'^{__CGEvent=}', CGEventRef)

    CGEventSourceRef = c_void_p
    register_preferred_encoding(b'^{__CGEventSource=}', CGEventSourceRef)

    CGEventTapLocation = c_uint32

    CGEventType = c_uint32

    CGEventField = c_uint32

    CGKeyCode = c_uint16

    CGMouseButton = c_uint32

    CGScrollEventUnit = c_uint32

    # size_t CGDisplayPixelsWide(CGDirectDisplayID display);
    core_graphics.CGDisplayPixelsWide.argtypes = [CGDirectDisplayID]
    core_graphics.CGDisplayPixelsWide.restype = c_size_t

    # CGEventRef CGEventCreateKeyboardEvent(CGEventSourceRef source, CGKeyCode virtualKey, bool keyDown);
    core_graphics.CGEventCreateKeyboardEvent.argtypes = [CGEventSourceRef, CGKeyCode, c_bool]
    core_graphics.CGEventCreateKeyboardEvent.restype = CGEventRef

    # CGEventRef CGEventCreateMouseEvent(
    #   CGEventSourceRef source, CGEventType mouseType, CGPoint mouseCursorPosition, CGMouseButton mouseButton);
    core_graphics.CGEventCreateMouseEvent.argtypes = [CGEventSourceRef, CGEventType, CGPoint, CGMouseButton]
    core_graphics.CGEventCreateMouseEvent.restype = CGEventRef

    # CGEventRef CGEventCreateScrollWheelEvent(
    #   CGEventSourceRef source, CGScrollEventUnit units, uint32_t wheelCount, int32_t wheel1, ...);
    core_graphics.CGEventCreateScrollWheelEvent.argtypes = [CGEventSourceRef, CGScrollEventUnit, c_uint32, c_int32]
    core_graphics.CGEventCreateScrollWheelEvent.restype = CGEventRef

    # void CGEventSetIntegerValueField(CGEventRef event, CGEventField field, int64_t value);
    core_graphics.CGEventSetIntegerValueField.argtypes = [CGEventRef, CGEventField, c_int64]
    core_graphics.CGEventSetIntegerValueField.restype = None

    # void CGEventSetType(CGEventRef event, CGEventType type);
    core_graphics.CGEventSetType.argtype = [CGEventRef, CGEventType]
    core_graphics.CGEventSetType.restype = None

    # void CGEventPost(CGEventTapLocation tap, CGEventRef event);
    core_graphics.CGEventPost.argtypes = [CGEventTapLocation, CGEventRef]
    core_graphics.CGEventPost.restype = None

    # CGDirectDisplayID CGMainDisplayID(void);
    core_graphics.CGMainDisplayID.argtypes = []
    core_graphics.CGMainDisplayID.restype = CGDirectDisplayID



    def _macPosition():
        loc = NSEvent.mouseLocation
        return int(loc.x), int(core_graphics.CGDisplayPixelsHigh(0) - loc.y)
    position = _macPosition


    def _macScreenshot(filename=None):
        if filename is not None:
            tmpFilename = filename
        else:
            tmpFilename = 'screenshot%s.png' % (datetime.datetime.now().strftime('%Y-%m%d_%H-%M-%S-%f'))
        subprocess.call(['screencapture', '-x', tmpFilename])
        im = Image.open(tmpFilename)

        # force loading before unlinking, Image.open() is lazy
        im.load()

        if filename is None:
            os.unlink(tmpFilename)
        return im
    screenshot = _macScreenshot

    def _macSize():
        return (
            core_graphics.CGDisplayPixelsWide(core_graphics.CGMainDisplayID()),
            core_graphics.CGDisplayPixelsHigh(core_graphics.CGMainDisplayID())
        )
    size = _macSize

    def _macGetPixel(x, y):
        rgbValue = screenshot().getpixel((x, y))
        return rgbValue[0], rgbValue[1], rgbValue[2]
    getPixel = _macGetPixel


elif platform.system() == 'Linux':
    from Xlib.display import Display
    import errno

    scrotExists = False
    try:
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

    _display = Display(os.environ['DISPLAY'])

    def _linuxPosition():
        coord = _display.screen().root.query_pointer()._data
        return coord["root_x"], coord["root_y"]
    position = _linuxPosition

    def _linuxScreenshot(filename=None):
        if not scrotExists:
            raise NotImplementedError('"scrot" must be installed to use screenshot functions in Linux. Run: sudo apt-get install scrot')

        if filename is not None:
            tmpFilename = filename
        else:
            tmpFilename = '.screenshot%s.png' % (datetime.datetime.now().strftime('%Y-%m%d_%H-%M-%S-%f'))

        if scrotExists:
            subprocess.call(['scrot', '-z', tmpFilename])
            im = Image.open(tmpFilename)

            # force loading before unlinking, Image.open() is lazy
            im.load()

            if filename is None:
                os.unlink(tmpFilename)
            return im
        else:
            raise Exception('The scrot program must be installed to take a screenshot with PyScreeze on Linux. Run: sudo apt-get install scrot')
    screenshot = _linuxScreenshot

    def _linuxSize():
        return _display.screen().width_in_pixels, _display.screen().height_in_pixels
    size = _linuxSize

    def _linuxGetPixel(x, y):
        rgbValue = screenshot().getpixel((x, y))
        return rgbValue[0], rgbValue[1], rgbValue[2]
    getPixel = _linuxGetPixel
# =========================================================================

RUNNING_PYTHON_2 = sys.version_info[0] == 2

if platform.system() == 'Linux':
    if RUNNING_PYTHON_2:
        try:
            import Tkinter as tkinter
            ttk = tkinter
            from Tkinter import Event
        except ImportError:
            sys.exit('NOTE: You must install tkinter on Linux to use MouseInfo. Run the following: sudo apt-get install python-tk python-dev')
    else:
        # Running Python 3+:
        try:
            import tkinter
            from tkinter import ttk
            from tkinter import Event
        except ImportError:
            sys.exit('NOTE: You must install tkinter on Linux to use MouseInfo. Run the following: sudo apt-get install python3-tk python3-dev')
else:
    # Running Windows or macOS:
    if RUNNING_PYTHON_2:
        import Tkinter as tkinter
        ttk = tkinter
        from Tkinter import Event
    else:
        # Running Python 3+:
        import tkinter
        from tkinter import ttk
        from tkinter import Event

MOUSE_INFO_BUTTON_WIDTH = 16 # A standard width for the buttons in the MouseInfo window.

class MouseInfoWindow:
    def _updateMouseInfoTextFields(self):
        # Update the XY and RGB text fields in the MouseInfo window.

        # Get the XY coordinates of the current mouse position:
        x, y = position()
        self.xyTextboxSV.set('%s,%s' % (x - self.xOrigin, y - self.yOrigin))

        # MouseInfo currently only works on the primary monitor, and doesn't
        # support multi-monitor setups. The color information isn't reliable
        # when the mouse is not on the primary monitor, so display an error instead.
        width, height = size()
        if not _PILLOW_INSTALLED:
            self.rgbSV.set('NA_Pillow_unsupported')
        elif sys.platform == 'darwin':
            # TODO - Until I can get screenshots without the mouse cursor, this feature doesn't work on mac.
            self.rgbSV.set('NA_on_macOS')
        elif not (0 <= x < width and 0 <= y < height):
            self.rgbSV.set('NA_on_multimonitor_setups')
        else:
            # Get the RGB color value of the pixel currently under the mouse:
            # NOTE: On Windows & Linux, Pillow's getpixel() returns a 3-integer tuple, but on macOS it returns a 4-integer tuple.
            r, g, b = getPixel(x, y)
            self.rgbSV.set('%s,%s,%s' % (r, g, b))

        if not _PILLOW_INSTALLED:
            self.rgbHexSV.set('NA_Pillow_unsupported')
        elif sys.platform == 'darwin':
            # TODO - Until I can get screenshots without the mouse cursor, this feature doesn't work on mac.
            self.rgbHexSV.set('NA_on_macOS')
        elif not (0 <= x < width and 0 <= y < height):
            self.rgbHexSV.set('NA_on_multimonitor_setups')
        else:
            # Convert this RGB value into a hex RGB value:
            rHex = hex(r)[2:].upper().rjust(2, '0')
            gHex = hex(g)[2:].upper().rjust(2, '0')
            bHex = hex(b)[2:].upper().rjust(2, '0')
            hexColor = '#%s%s%s' % (rHex, gHex, bHex)
            self.rgbHexSV.set(hexColor)

        if (not _PILLOW_INSTALLED) or (sys.platform == 'darwin') or (not (0 <= x < width and 0 <= y < height)):
            self.colorFrame.configure(background='black')
        else:
            # Update the color panel:
            self.colorFrame.configure(background=hexColor)

        # As long as the self.isRunning variable is True,
        # schedule this function to be called again in 100 milliseconds.
        # NOTE: Previously this if-else code was at the top of the function
        # so that I could avoid the "invalid command name" message that
        # was popping up (this didn't work though), but it was also causing
        # a weird bug where the text fields weren't populated until I moved
        # the tkinter window. I have no idea why that behavior was happening.
        # You can reproduce it by moving this if-else code to the top of this
        # function.
        if self.isRunning:
            self._updateMouseInfoJob = self.root.after(100, self._updateMouseInfoTextFields)
        else:
            return # MouseInfo window has been closed, so return immediately.


    def _copyText(self, textToCopy):
        try:
            pyperclip.copy(textToCopy)
            self.statusbarSV.set('Copied ' + textToCopy)
        except pyperclip.PyperclipException as e:
            if platform.system() == 'Linux':
                self.statusbarSV.set('Copy failed. Run "sudo apt-get install xsel".')
            else:
                self.statusbarSV.set('Clipboard error: ' + str(e))


    def _copyXyMouseInfo(self, *args):
        # Copy the contents of the XY coordinate text field in the MouseInfo
        # window to the clipboard.

        if len(args) > 0 and isinstance(args[0], Event):
            args = () # When the hotkey is pressed, an Event object is in args. Let's just get rid of it and let the rest of the code run as normal.

        if self.delayEnabledSV.get() == 'on' and len(args) == 0:
            # Start countdown by having after() call this function in 1 second:
            self.root.after(1000, self._copyXyMouseInfo, 2)
            self.xyCopyButtonSV.set('Copy in 3')
        elif len(args) == 1 and args[0] == 2:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._copyXyMouseInfo, 1)
            self.xyCopyButtonSV.set('Copy in 2')
        elif len(args) == 1 and args[0] == 1:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._copyXyMouseInfo, 0)
            self.xyCopyButtonSV.set('Copy in 1')
        else:
            # Delay disabled or countdown has finished:
            self._copyText(self.xyTextboxSV.get())
            self.xyCopyButtonSV.set('Copy XY')


    def _copyRgbMouseInfo(self, *args):
        # Copy the contents of the RGB color text field in the MouseInfo
        # window to the clipboard.

        if len(args) > 0 and isinstance(args[0], Event):
            args = () # When the hotkey is pressed, an Event object is in args. Let's just get rid of it and let the rest of the code run as normal.

        if self.delayEnabledSV.get() == 'on' and len(args) == 0:
            # Start countdown by having after() call this function in 1 second:
            self.root.after(1000, self._copyRgbMouseInfo, 2)
            self.rgbCopyButtonSV.set('Copy in 3')
        elif len(args) == 1 and args[0] == 2:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._copyRgbMouseInfo, 1)
            self.rgbCopyButtonSV.set('Copy in 2')
        elif len(args) == 1 and args[0] == 1:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._copyRgbMouseInfo, 0)
            self.rgbCopyButtonSV.set('Copy in 1')
        else:
            # Delay disabled or countdown has finished:
            self._copyText(self.rgbSV.get())
            self.rgbCopyButtonSV.set('Copy RGB')


    def _copyRgbHexMouseInfo(self, *args):
        # Copy the contents of the RGB hex color text field in the MouseInfo
        # window to the clipboard.

        if len(args) > 0 and isinstance(args[0], Event):
            args = () # When the hotkey is pressed, an Event object is in args. Let's just get rid of it and let the rest of the code run as normal.

        if self.delayEnabledSV.get() == 'on' and len(args) == 0:
            # Start countdown by having after() call this function in 1 second:
            self.root.after(1000, self._copyRgbHexMouseInfo, 2)
            self.rgbHexCopyButtonSV.set('Copy in 3')
        elif len(args) == 1 and args[0] == 2:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._copyRgbHexMouseInfo, 1)
            self.rgbHexCopyButtonSV.set('Copy in 2')
        elif len(args) == 1 and args[0] == 1:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._copyRgbHexMouseInfo, 0)
            self.rgbHexCopyButtonSV.set('Copy in 1')
        else:
            # Delay disabled or countdown has finished:
            self._copyText(self.rgbHexSV.get())
            self.rgbHexCopyButtonSV.set('Copy RGB Hex')


    def _copyAllMouseInfo(self, *args):
        # Copy the contents of the XY coordinate and RGB color text fields in the
        # MouseInfo window to the log text field.
        textFieldContents = '%s %s %s' % (self.xyTextboxSV.get(),
                                          self.rgbSV.get(),
                                          self.rgbHexSV.get())
        #self._copyText(textFieldContents)

        if len(args) > 0 and isinstance(args[0], Event):
            args = () # When the hotkey is pressed, an Event object is in args. Let's just get rid of it and let the rest of the code run as normal.

        if self.delayEnabledSV.get() == 'on' and len(args) == 0:
            # Start countdown by having after() call this function in 1 second:
            self.root.after(1000, self._copyAllMouseInfo, 2)
            self.allCopyButtonSV.set('Copy in 3')
        elif len(args) == 1 and args[0] == 2:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._copyAllMouseInfo, 1)
            self.allCopyButtonSV.set('Copy in 2')
        elif len(args) == 1 and args[0] == 1:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._copyAllMouseInfo, 0)
            self.allCopyButtonSV.set('Copy in 1')
        else:
            # Delay disabled or countdown has finished:
            textFieldContents = '%s %s %s' % (self.xyTextboxSV.get(),
                                              self.rgbSV.get(),
                                              self.rgbHexSV.get())
            self._copyText(textFieldContents)
            self.allCopyButtonSV.set('Copy All')


    def _logXyMouseInfo(self, *args):
        # Log the contents of the XY coordinate text field in the MouseInfo
        # window to the log text field.

        if len(args) > 0 and isinstance(args[0], Event):
            args = () # When the hotkey is pressed, an Event object is in args. Let's just get rid of it and let the rest of the code run as normal.

        if self.delayEnabledSV.get() == 'on' and len(args) == 0:
            # Start countdown by having after() call this function in 1 second:
            self.root.after(1000, self._logXyMouseInfo, 2)
            self.xyLogButtonSV.set('Log in 3')
        elif len(args) == 1 and args[0] == 2:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._logXyMouseInfo, 1)
            self.xyLogButtonSV.set('Log in 2')
        elif len(args) == 1 and args[0] == 1:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._logXyMouseInfo, 0)
            self.xyLogButtonSV.set('Log in 1')
        else:
            # Delay disabled or countdown has finished:
            logContents = self.logTextarea.get('1.0', 'end-1c') + '%s\n' % (self.xyTextboxSV.get()) # 'end-1c' doesn't include the final newline
            self.logTextboxSV.set(logContents)
            self._setLogTextAreaContents(logContents)
            self.statusbarSV.set('Logged ' + self.xyTextboxSV.get())
            self.xyLogButtonSV.set('Log XY')


    def _logRgbMouseInfo(self, *args):
        # Log the contents of the RGB color text field in the MouseInfo
        # window to the log text field.

        if len(args) > 0 and isinstance(args[0], Event):
            args = () # When the hotkey is pressed, an Event object is in args. Let's just get rid of it and let the rest of the code run as normal.

        if self.delayEnabledSV.get() == 'on' and len(args) == 0:
            # Start countdown by having after() call this function in 1 second:
            self.root.after(1000, self._logRgbMouseInfo, 2)
            self.rgbLogButtonSV.set('Log in 3')
        elif len(args) == 1 and args[0] == 2:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._logRgbMouseInfo, 1)
            self.rgbLogButtonSV.set('Log in 2')
        elif len(args) == 1 and args[0] == 1:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._logRgbMouseInfo, 0)
            self.rgbLogButtonSV.set('Log in 1')
        else:
            # Delay disabled or countdown has finished:
            logContents = self.logTextarea.get('1.0', 'end-1c') + '%s\n' % (self.rgbSV.get()) # 'end-1c' doesn't include the final newline
            self.logTextboxSV.set(logContents)
            self._setLogTextAreaContents(logContents)
            self.statusbarSV.set('Logged ' + self.rgbSV.get())
            self.rgbLogButtonSV.set('Log RGB')


    def _logRgbHexMouseInfo(self, *args):
        # Log the contents of the RGB hex color text field in the MouseInfo
        # window to the log text field.

        if len(args) > 0 and isinstance(args[0], Event):
            args = () # When the hotkey is pressed, an Event object is in args. Let's just get rid of it and let the rest of the code run as normal.

        if self.delayEnabledSV.get() == 'on' and len(args) == 0:
            # Start countdown by having after() call this function in 1 second:
            self.root.after(1000, self._logRgbHexMouseInfo, 2)
            self.rgbHexLogButtonSV.set('Log in 3')
        elif len(args) == 1 and args[0] == 2:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._logRgbHexMouseInfo, 1)
            self.rgbHexLogButtonSV.set('Log in 2')
        elif len(args) == 1 and args[0] == 1:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._logRgbHexMouseInfo, 0)
            self.rgbHexLogButtonSV.set('Log in 1')
        else:
            # Delay disabled or countdown has finished:
            logContents = self.logTextarea.get('1.0', 'end-1c') + '%s\n' % (self.rgbHexSV.get()) # 'end-1c' doesn't include the final newline
            self.logTextboxSV.set(logContents)
            self._setLogTextAreaContents(logContents)
            self.statusbarSV.set('Logged ' + self.rgbHexSV.get())
            self.rgbHexLogButtonSV.set('Log RGB Hex')


    def _logAllMouseInfo(self, *args):
        # Log the contents of the XY coordinate and RGB color text fields in the
        # MouseInfo window to the log text field.

        if len(args) > 0 and isinstance(args[0], Event):
            args = () # When the hotkey is pressed, an Event object is in args. Let's just get rid of it and let the rest of the code run as normal.

        if self.delayEnabledSV.get() == 'on' and len(args) == 0:
            # Start countdown by having after() call this function in 1 second:
            self.root.after(1000, self._logAllMouseInfo, 2)
            self.allLogButtonSV.set('Log in 3')
        elif len(args) == 1 and args[0] == 2:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._logAllMouseInfo, 1)
            self.allLogButtonSV.set('Log in 2')
        elif len(args) == 1 and args[0] == 1:
            # Continue countdown by having after() call this function in 1 second:
            self.root.after(1000, self._logAllMouseInfo, 0)
            self.allLogButtonSV.set('Log in 1')
        else:
            # Delay disabled or countdown has finished:
            textFieldContents = '%s %s %s' % (self.xyTextboxSV.get(),
                                              self.rgbSV.get(),
                                              self.rgbHexSV.get())
            logContents = self.logTextarea.get('1.0', 'end-1c') + '%s\n' % (textFieldContents) # 'end-1c' doesn't include the final newline
            self.logTextboxSV.set(logContents)
            self._setLogTextAreaContents(logContents)
            self.statusbarSV.set('Logged ' + textFieldContents)
            self.allLogButtonSV.set('Log All')

    def _xyOriginChanged(self, sv):
        contents = sv.get()
        if len(contents.split(',')) != 2:
            return # Do nothing if the text is invalid
        x, y = contents.split(',')
        x = x.strip()
        y = y.strip()
        if not x.isdecimal() or not y.isdecimal():
            return # Do nothing.
        self.xOrigin = int(x)
        self.yOrigin = int(y)
        self.statusbarSV.set('Set XY Origin to ' + str(self.xOrigin) + ', ' + str(self.yOrigin))

    def _setLogTextAreaContents(self, logContents):
        if RUNNING_PYTHON_2:
            self.logTextarea.delete('1.0', tkinter.END)
            self.logTextarea.insert(tkinter.END, logContents)
        else:
            self.logTextarea.replace('1.0', tkinter.END, logContents)

        # Scroll to the bottom of the text area:
        topOfTextArea, bottomOfTextArea = self.logTextarea.yview()
        self.logTextarea.yview_moveto(bottomOfTextArea)


    def _saveLogFile(self, *args):
        # Save the current contents of the log file text field. Automatically
        # overwrites the file if it exists. Displays an error message in the
        # status bar if there is a problem.
        try:
            with open(self.logFilenameSV.get(), 'w') as fo:
                fo.write(self.logTextboxSV.get())
        except Exception as e:
            self.statusbarSV.set('ERROR: ' + str(e))
        else:
            self.statusbarSV.set('Log file saved to ' + self.logFilenameSV.get())


    def _saveScreenshotFile(self, *args):
        # Saves a screenshot. Automatically overwrites the file if it exists.
        # Displays an error message in the status bar if there is a problem.

        if not _PILLOW_INSTALLED:
            self.statusbarSV.set('ERROR: NA_Pillow_unsupported')
            return

        try:
            screenshot(self.screenshotFilenameSV.get())
        except Exception as e:
            self.statusbarSV.set('ERROR: ' + str(e))
        else:
            self.statusbarSV.set('Screenshot file saved to ' + self.screenshotFilenameSV.get())


    def __init__(self):
        """Launches the MouseInfo window, which displays XY coordinate and RGB
        color information for the mouse's current position."""

        self.isRunning = True # While True, the text fields will update.

        # Create the MouseInfo window:
        self.root = tkinter.Tk()
        self.root.title('MouseInfo ' + __version__)
        self.root.minsize(400, 100)

        # Create the main frame in the MouseInfo window:
        if RUNNING_PYTHON_2:
            mainframe = tkinter.Frame(self.root)
        else:
            mainframe = ttk.Frame(self.root, padding='3 3 12 12')

        # Set up the grid for the MouseInfo window's widgets:
        mainframe.grid(column=0, row=0, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        # WIDGETS ON ROW 1:
        CUR_ROW = 1 # I'm using a variable because it's easier to make changes to the source code this way.

        # Set up the instructional text label:
        #ttk.Label(mainframe, text='Tab over the buttons and press Enter to\n"click" them as you move the mouse around.').grid(column=1, row=1, columnspan=2, sticky=tkinter.W)
        self.delayEnabledSV = tkinter.StringVar()
        self.delayEnabledSV.set('on')
        delayCheckbox = ttk.Checkbutton(mainframe, text='3 Sec. Button Delay', variable=self.delayEnabledSV, onvalue='on', offvalue='off')
        delayCheckbox.grid(column=1, row=CUR_ROW, columnspan=2, sticky=tkinter.W)

        # Set up the button to copy the XY coordinates to the clipboard:
        self.allCopyButtonSV = tkinter.StringVar()
        self.allCopyButtonSV.set('Copy All (F1)')
        self.allCopyButton = ttk.Button(mainframe, textvariable=self.allCopyButtonSV, width=MOUSE_INFO_BUTTON_WIDTH, command=self._copyAllMouseInfo)
        self.allCopyButton.grid(column=3, row=CUR_ROW, sticky=tkinter.W)
        self.allCopyButton.bind('<Return>', self._copyAllMouseInfo)

        # Set up the button to copy the XY coordinates to the clipboard:
        self.allLogButtonSV = tkinter.StringVar()
        self.allLogButtonSV.set('Log All (F5)')
        self.allLogButton = ttk.Button(mainframe, textvariable=self.allLogButtonSV, width=MOUSE_INFO_BUTTON_WIDTH, command=self._logAllMouseInfo)
        self.allLogButton.grid(column=4, row=CUR_ROW, sticky=tkinter.W)
        self.allLogButton.bind('<Return>', self._logAllMouseInfo)

        # Set up the variables for the content of the MouseInfo window's text fields:
        self.xyTextboxSV          = tkinter.StringVar() # The str contents of the xy text field.
        self.rgbSV                = tkinter.StringVar() # The str contents of the rgb text field.
        self.rgbHexSV             = tkinter.StringVar() # The str contents of the rgb hex text field.
        self.xyOriginSV           = tkinter.StringVar() # The str contents of the xy origin field.
        self.logTextboxSV         = tkinter.StringVar() # The str contents of the log text area.
        self.logFilenameSV        = tkinter.StringVar() # The str contents of the log filename text field.
        self.screenshotFilenameSV = tkinter.StringVar() # The str contents of the screenshot filename text field.
        self.statusbarSV          = tkinter.StringVar() # The str contents of the status bar at the bottom of the window.

        # WIDGETS ON ROW 3:
        CUR_ROW += 1

        # Set up the XY coordinate text field and label:
        self.xyInfoTextbox = ttk.Entry(mainframe, width=16, textvariable=self.xyTextboxSV)
        self.xyInfoTextbox.grid(column=2, row=CUR_ROW, sticky=(tkinter.W, tkinter.E))
        ttk.Label(mainframe, text='XY Position').grid(column=1, row=CUR_ROW, sticky=tkinter.W)

        # Set up the button to copy the XY coordinates to the clipboard:
        self.xyCopyButtonSV = tkinter.StringVar()
        self.xyCopyButtonSV.set('Copy XY (F2)')
        self.xyCopyButton = ttk.Button(mainframe, textvariable=self.xyCopyButtonSV, width=MOUSE_INFO_BUTTON_WIDTH, command=self._copyXyMouseInfo)
        self.xyCopyButton.grid(column=3, row=CUR_ROW, sticky=tkinter.W)
        self.xyCopyButton.bind('<Return>', self._copyXyMouseInfo)

        # Set up the button to log the XY coordinates:
        self.xyLogButtonSV = tkinter.StringVar()
        self.xyLogButtonSV.set('Log XY (F6)')
        self.xyLogButton = ttk.Button(mainframe, textvariable=self.xyLogButtonSV, width=MOUSE_INFO_BUTTON_WIDTH, command=self._logXyMouseInfo)
        self.xyLogButton.grid(column=4, row=CUR_ROW, sticky=tkinter.W)
        self.xyLogButton.bind('<Return>', self._logXyMouseInfo)

        # WIDGETS ON ROW 4:
        CUR_ROW += 1

        # Set up the RGB color text field and label:
        self.rgbSV_entry = ttk.Entry(mainframe, width=16, textvariable=self.rgbSV)
        self.rgbSV_entry.grid(column=2, row=CUR_ROW, sticky=(tkinter.W, tkinter.E))
        ttk.Label(mainframe, text='RGB Color').grid(column=1, row=CUR_ROW, sticky=tkinter.W)

        # Set up the button to copy the RGB color to the clipboard:
        self.rgbCopyButtonSV = tkinter.StringVar()
        self.rgbCopyButtonSV.set('Copy RGB (F3)')
        self.rgbCopyButton = ttk.Button(mainframe, textvariable=self.rgbCopyButtonSV, width=MOUSE_INFO_BUTTON_WIDTH, command=self._copyRgbMouseInfo)
        self.rgbCopyButton.grid(column=3, row=CUR_ROW, sticky=tkinter.W)
        self.rgbCopyButton.bind('<Return>', self._copyRgbMouseInfo)

        # Set up the button to log the XY coordinates:
        self.rgbLogButtonSV = tkinter.StringVar()
        self.rgbLogButtonSV.set('Log RGB (F7)')
        self.rgbLogButton = ttk.Button(mainframe, textvariable=self.rgbLogButtonSV, width=MOUSE_INFO_BUTTON_WIDTH, command=self._logRgbMouseInfo)
        self.rgbLogButton.grid(column=4, row=CUR_ROW, sticky=tkinter.W)
        self.rgbLogButton.bind('<Return>', self._logRgbMouseInfo)

        # WIDGETS ON ROW 5:
        CUR_ROW += 1

        # Set up the RGB hex color text field and label:
        self.rgbHexSV_entry = ttk.Entry(mainframe, width=16, textvariable=self.rgbHexSV)
        self.rgbHexSV_entry.grid(column=2, row=CUR_ROW, sticky=(tkinter.W, tkinter.E))
        ttk.Label(mainframe, text='RGB as Hex').grid(column=1, row=CUR_ROW, sticky=tkinter.W)

        # Set up the button to copy the RGB hex color to the clipboard:
        self.rgbHexCopyButtonSV = tkinter.StringVar()
        self.rgbHexCopyButtonSV.set('Copy RGB Hex (F4)')
        self.rgbHexCopyButton = ttk.Button(mainframe, textvariable=self.rgbHexCopyButtonSV, width=MOUSE_INFO_BUTTON_WIDTH, command=self._copyRgbHexMouseInfo)
        self.rgbHexCopyButton.grid(column=3, row=CUR_ROW, sticky=tkinter.W)
        self.rgbHexCopyButton.bind('<Return>', self._copyRgbHexMouseInfo)

        # Set up the button to log the XY coordinates:
        self.rgbHexLogButtonSV = tkinter.StringVar()
        self.rgbHexLogButtonSV.set('Log RGB Hex (F8)')
        self.rgbHexLogButton = ttk.Button(mainframe, textvariable=self.rgbHexLogButtonSV, width=MOUSE_INFO_BUTTON_WIDTH, command=self._logRgbHexMouseInfo)
        self.rgbHexLogButton.grid(column=4, row=CUR_ROW, sticky=tkinter.W)
        self.rgbHexLogButton.bind('<Return>', self._logRgbHexMouseInfo)

        # WIDGETS ON ROW 6:
        CUR_ROW += 1

        # Set up the frame that displays the color of the pixel currently under the mouse cursor:
        self.colorFrame = tkinter.Frame(mainframe, width=50, height=50)
        self.colorFrame.grid(column=2, row=CUR_ROW, sticky=(tkinter.W, tkinter.E))
        ttk.Label(mainframe, text='Color').grid(column=1, row=CUR_ROW, sticky=tkinter.W)

        # WIDGETS ON ROW 7:
        CUR_ROW += 1

        # Set up the XY origin text field and label:
        self.xOrigin = 0
        self.yOrigin = 0
        self.xyOriginSV.set('0, 0')
        ttk.Label(mainframe, text='XY Origin').grid(column=1, row=CUR_ROW, sticky=tkinter.W)
        self.xyOriginSV.trace("w", lambda name, index, mode, sv=self.xyOriginSV: self._xyOriginChanged(sv))
        self.xyOriginSV_entry = ttk.Entry(mainframe, width=16, textvariable=self.xyOriginSV)
        self.xyOriginSV_entry.grid(column=2, row=CUR_ROW, sticky=(tkinter.W, tkinter.E))

        # WIDGETS ON ROW 8:
        CUR_ROW += 1

        # Set up the multiline text widget where the log info appears:
        self.logTextarea = tkinter.Text(mainframe, width=20, height=6)
        self.logTextarea.grid(column=1, row=CUR_ROW, columnspan=4, sticky=(tkinter.W, tkinter.E, tkinter.N, tkinter.S))
        self.logTextareaScrollbar = ttk.Scrollbar(mainframe, orient=tkinter.VERTICAL, command=self.logTextarea.yview)
        self.logTextareaScrollbar.grid(column=5, row=CUR_ROW, sticky=(tkinter.N, tkinter.S))
        self.logTextarea['yscrollcommand'] = self.logTextareaScrollbar.set

        # WIDGETS ON ROW 9:
        CUR_ROW += 1

        self.logFilenameTextbox = ttk.Entry(mainframe, width=16, textvariable=self.logFilenameSV)
        self.logFilenameTextbox.grid(column=1, row=CUR_ROW, columnspan=3, sticky=(tkinter.W, tkinter.E))
        self.saveLogButton = ttk.Button(mainframe, text='Save Log', width=MOUSE_INFO_BUTTON_WIDTH, command=self._saveLogFile)
        self.saveLogButton.grid(column=4, row=CUR_ROW, sticky=tkinter.W)
        self.saveLogButton.bind('<Return>', self._saveLogFile)
        self.logFilenameSV.set(os.path.join(os.getcwd(), 'mouseInfoLog.txt'))

        # WIDGETS ON ROW 10:
        CUR_ROW += 1

        G_MOUSE_INFO_SCREENSHOT_FILENAME_entry = ttk.Entry(mainframe, width=16, textvariable=self.screenshotFilenameSV)
        G_MOUSE_INFO_SCREENSHOT_FILENAME_entry.grid(column=1, row=CUR_ROW, columnspan=3, sticky=(tkinter.W, tkinter.E))
        self.saveScreenshotButton = ttk.Button(mainframe, text='Save Screenshot', width=MOUSE_INFO_BUTTON_WIDTH, command=self._saveScreenshotFile)
        self.saveScreenshotButton.grid(column=4, row=CUR_ROW, sticky=tkinter.W)
        self.saveScreenshotButton.bind('<Return>', self._saveScreenshotFile)
        self.screenshotFilenameSV.set(os.path.join(os.getcwd(), 'mouseInfoScreenshot.png'))

        # WIDGETS ON ROW 11:
        CUR_ROW += 1

        statusbar = ttk.Label(mainframe, relief=tkinter.SUNKEN, textvariable=self.statusbarSV)
        statusbar.grid(column=1, row=CUR_ROW, columnspan=5, sticky=(tkinter.W, tkinter.E))

        # Add padding to all of the widgets:
        for child in mainframe.winfo_children():
            # Ensure the scrollbar and text area don't have padding in between them:
            if child == self.logTextareaScrollbar:
                child.grid_configure(padx=0, pady=3)
            elif child == self.logTextarea:
                child.grid_configure(padx=(3, 0), pady=3)
            elif child == statusbar:
                child.grid_configure(padx=0, pady=(3, 0))
            else:
                # All other widgets have a standard padding of 3:
                child.grid_configure(padx=3, pady=3)

        # Add keyboard hotkeys for the Copy/Log buttons:
        self.root.option_add('*tearOff', tkinter.FALSE) # Disable tkinter's ugly tear-off menus which are enabled by default.

        menu = tkinter.Menu(self.root)
        self.root.config(menu=menu)

        copyMenu = tkinter.Menu(menu)
        copyMenu.add_command(label='Copy All', command=self._copyAllMouseInfo, accelerator='F1', underline=5)
        copyMenu.add_command(label='Copy XY', command=self._copyXyMouseInfo, accelerator='F2', underline=5)
        copyMenu.add_command(label='Copy RGB', command=self._copyRgbMouseInfo, accelerator='F3', underline=5)
        copyMenu.add_command(label='Copy RGB as Hex', command=self._copyRgbHexMouseInfo, accelerator='F4', underline=12)
        menu.add_cascade(label='Copy', menu=copyMenu, underline=0)

        logMenu = tkinter.Menu(menu)
        logMenu.add_command(label='Log All', command=self._logAllMouseInfo, accelerator='F5', underline=4)
        logMenu.add_command(label='Log XY', command=self._logXyMouseInfo, accelerator='F6', underline=4)
        logMenu.add_command(label='Log RGB', command=self._logRgbMouseInfo, accelerator='F7', underline=4)
        logMenu.add_command(label='Log RGB as Hex', command=self._logRgbHexMouseInfo, accelerator='F8', underline=11)
        menu.add_cascade(label='Log', menu=logMenu, underline=0)

        helpMenu = tkinter.Menu(menu)
        helpMenu.add_command(label='Online Documentation', command=lambda: webbrowser.open('https://mouseinfo.readthedocs.io'), underline=6)
        menu.add_cascade(label='Help', menu=helpMenu, underline=0)

        self.root.bind_all('<F1>', self._copyAllMouseInfo)
        self.root.bind_all('<F2>', self._copyXyMouseInfo)
        self.root.bind_all('<F3>', self._copyRgbMouseInfo)
        self.root.bind_all('<F4>', self._copyRgbHexMouseInfo)
        self.root.bind_all('<F5>', self._logAllMouseInfo)
        self.root.bind_all('<F6>', self._logXyMouseInfo)
        self.root.bind_all('<F7>', self._logRgbMouseInfo)
        self.root.bind_all('<F8>', self._logRgbHexMouseInfo)


        self.root.resizable(False, False) # Prevent the window from being resized.

        self.xyInfoTextbox.focus() # Put the focus on the XY coordinate text field to start.

        self._updateMouseInfoJob = self.root.after(100, self._updateMouseInfoTextFields) # Begin updating the text fields.

        # Make the mouse info window "always on top".
        self.root.attributes('-topmost', True)
        self.root.update()

        # Start the application:
        self.root.mainloop()

        # Application has closed, set isRunning to False and cancel any "after" commands already queued:
        self.root.after_cancel(self._updateMouseInfoJob)
        self.isRunning = False

        # Destroy the tkinter root widget:
        try:
            self.root.destroy()
        except tkinter.TclError:
            pass

def mouseInfo():
    """
    Launch the MouseInfo application in a new window.

    This exists as a shortcut instead of running MouseInfoWindow() because
    PyAutoGUI (which imports mouseinfo) is set up with a simple mouseInfo()
    function and I'd like to keep this consistent with that.
    """
    MouseInfoWindow()

if __name__ == '__main__':
    MouseInfoWindow()
