# This module contains all the Windows-specific code to create native
# message boxes using the winapi.

# If you'd like to learn more about calling the winapi functions from
# Python, you can check out my other module "nicewin" to see nicely-documented
# examples. It is at https://github.com/asweigart/nicewin

# The documentation for the MessageBox winapi is at:
# https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-messagebox

import sys, ctypes
import pymsgbox

MB_OK = 0x0
MB_OKCANCEL = 0x1
MB_ABORTRETRYIGNORE = 0x2
MB_YESNOCANCEL = 0x3
MB_YESNO = 0x4
MB_RETRYCANCEL = 0x5
MB_CANCELTRYCONTINUE = 0x6

NO_ICON = 0
STOP = MB_ICONHAND = MB_ICONSTOP = MB_ICONERRPR = 0x10
QUESTION = MB_ICONQUESTION = 0x20
WARNING = MB_ICONEXCLAIMATION = 0x30
INFO = MB_ICONASTERISK = MB_ICONINFOMRAITON = 0x40

MB_DEFAULTBUTTON1 = 0x0
MB_DEFAULTBUTTON2 = 0x100
MB_DEFAULTBUTTON3 = 0x200
MB_DEFAULTBUTTON4 = 0x300

MB_SETFOREGROUND = 0x10000
MB_TOPMOST = 0x40000

IDABORT = 0x3
IDCANCEL = 0x2
IDCONTINUE = 0x11
IDIGNORE = 0x5
IDNO = 0x7
IDOK = 0x1
IDRETRY = 0x4
IDTRYAGAIN = 0x10
IDYES = 0x6

runningOnPython2 = sys.version_info[0] == 2
if runningOnPython2:
    messageBoxFunc = ctypes.windll.user32.MessageBoxA
else:  # Python 3 functions.
    messageBoxFunc = ctypes.windll.user32.MessageBoxW


def alert(
    text="",
    title="",
    button=pymsgbox.OK_TEXT,
    root=None,
    timeout=None,
    icon=NO_ICON,
    _tkinter=False,
):
    """Displays a simple message box with text and a single OK button. Returns the text of the button clicked on."""
    text = str(text)
    if (_tkinter) or (timeout is not None) or (button != pymsgbox.OK_TEXT):
        # Timeouts are not supported by Windows message boxes.
        # Call the original tkinter alert function, not this native one:
        return pymsgbox._alertTkinter(text, title, button, root, timeout)

    messageBoxFunc(0, text, title, MB_OK | MB_SETFOREGROUND | MB_TOPMOST | icon)
    return button


def confirm(
    text="",
    title="",
    buttons=(pymsgbox.OK_TEXT, pymsgbox.CANCEL_TEXT),
    root=None,
    timeout=None,
    icon=QUESTION,
    _tkinter=False,
):
    """Displays a message box with OK and Cancel buttons. Number and text of buttons can be customized. Returns the text of the button clicked on."""
    text = str(text)
    buttonFlag = None
    if len(buttons) == 1:
        if buttons[0] == pymsgbox.OK_TEXT:
            buttonFlag = MB_OK
    elif len(buttons) == 2:
        if buttons[0] == pymsgbox.OK_TEXT and buttons[1] == pymsgbox.CANCEL_TEXT:
            buttonFlag = MB_OKCANCEL
        elif buttons[0] == pymsgbox.YES_TEXT and buttons[1] == pymsgbox.NO_TEXT:
            buttonFlag = MB_YESNO
        elif buttons[0] == pymsgbox.RETRY_TEXT and buttons[1] == pymsgbox.CANCEL_TEXT:
            buttonFlag = MB_RETRYCANCEL
    elif len(buttons) == 3:
        if (
            buttons[0] == pymsgbox.ABORT_TEXT
            and buttons[1] == pymsgbox.RETRY_TEXT
            and buttons[2] == pymsgbox.IGNORE_TEXT
        ):
            buttonFlag = MB_ABORTRETRYIGNORE
        elif (
            buttons[0] == pymsgbox.CANCEL_TEXT
            and buttons[1] == pymsgbox.TRY_AGAIN_TEXT
            and buttons[2] == pymsgbox.CONTINUE_TEXT
        ):
            buttonFlag = MB_CANCELTRYCONTINUE
        elif (
            buttons[0] == pymsgbox.YES_TEXT
            and buttons[1] == pymsgbox.NO_TEXT
            and buttons[2] == pymsgbox.CANCEL_TEXT
        ):
            buttonFlag = MB_YESNOCANCEL

    if (_tkinter) or (timeout is not None) or (buttonFlag is None):
        # Call the original tkinter confirm() function, not this native one:
        return pymsgbox._confirmTkinter(text, title, buttons, root, timeout)

    retVal = messageBoxFunc(
        0, text, title, buttonFlag | MB_SETFOREGROUND | MB_TOPMOST | icon
    )
    if retVal == IDOK or len(buttons) == 1:
        return pymsgbox.OK_TEXT
    elif retVal == IDCANCEL:
        return pymsgbox.CANCEL_TEXT
    elif retVal == IDYES:
        return pymsgbox.YES_TEXT
    elif retVal == IDNO:
        return pymsgbox.NO_TEXT
    elif retVal == IDTRYAGAIN:
        return pymsgbox.TRY_TEXT
    elif retVal == IDRETRY:
        return pymsgbox.RETRY_TEXT
    elif retVal == IDIGNORE:
        return pymsgbox.IGNORE_TEXT
    elif retVal == IDCONTINUE:
        return pymsgbox.CONTINUE_TEXT
    elif retVal == IDABORT:
        return pymsgbox.ABORT_TEXT
    else:
        assert False, "Unexpected return value from MessageBox: %s" % (retVal)


'''
def prompt(text='', title='' , default=''):
    """Displays a message box with text input, and OK & Cancel buttons. Returns the text entered, or None if Cancel was clicked."""
    pass

def password(text='', title='', default='', mask='*'):
    """Displays a message box with text input, and OK & Cancel buttons. Typed characters appear as *. Returns the text entered, or None if Cancel was clicked."""
    pass

'''
