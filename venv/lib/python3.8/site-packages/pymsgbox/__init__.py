# PyMsgBox - A simple, cross-platform, pure Python module for JavaScript-like message boxes.
# By Al Sweigart al@inventwithpython.com

__version__ = "1.0.9"

# Modified BSD License
# Derived from Stephen Raymond Ferg's EasyGui http://easygui.sourceforge.net/

"""
The four functions in PyMsgBox:

 - alert(text='', title='', button='OK')

    Displays a simple message box with text and a single OK button. Returns the text of the button clicked on.

 - confirm(text='', title='', buttons=['OK', 'Cancel'])

    Displays a message box with OK and Cancel buttons. Number and text of buttons can be customized. Returns the text of the button clicked on.

 - prompt(text='', title='' , default='')

    Displays a message box with text input, and OK & Cancel buttons. Returns the text entered, or None if Cancel was clicked.

 - password(text='', title='', default='', mask='*')

    Displays a message box with text input, and OK & Cancel buttons. Typed characters appear as *. Returns the text entered, or None if Cancel was clicked.
"""

"""
TODO Roadmap:
- Be able to specify a custom icon in the message box.
- Be able to place the message box at an arbitrary position (including on multi screen layouts)
- Add mouse clicks to unit testing.
- progress() function to display a progress bar
- Maybe other types of dialog: open, save, file/folder picker, etc.
"""

import sys

RUNNING_PYTHON_2 = sys.version_info[0] == 2

# Because PyAutoGUI requires PyMsgBox but might be installed on systems
# without tkinter, we don't want a lack of tkinter to cause installation
# to fail. So exceptions won't be raised until the PyMsgBox functions
# are actually called.
TKINTER_IMPORT_SUCCEEDED = True

try:
    if RUNNING_PYTHON_2:
        import Tkinter as tk
    else:
        import tkinter as tk

    rootWindowPosition = "+300+200"

    if tk.TkVersion < 8.0:
        raise RuntimeError(
            "You are running Tk version: "
            + str(tk.TkVersion)
            + "You must be using Tk version 8.0 or greater to use PyMsgBox."
        )

except ImportError:
    TKINTER_IMPORT_SUCCEEDED = False


PROPORTIONAL_FONT_FAMILY = ("MS", "Sans", "Serif")
MONOSPACE_FONT_FAMILY = "Courier"

PROPORTIONAL_FONT_SIZE = 10
MONOSPACE_FONT_SIZE = (
    9
)  # a little smaller, because it it more legible at a smaller size
TEXT_ENTRY_FONT_SIZE = 12  # a little larger makes it easier to see


STANDARD_SELECTION_EVENTS = ["Return", "Button-1", "space"]

# constants for strings: (TODO: for internationalization, change these)
OK_TEXT = "OK"
CANCEL_TEXT = "Cancel"
YES_TEXT = "Yes"
NO_TEXT = "No"
RETRY_TEXT = "Retry"
ABORT_TEXT = "Abort"
IGNORE_TEXT = "Ignore"
TRY_AGAIN_TEXT = "Try Again"
CONTINUE_TEXT = "Continue"

TIMEOUT_RETURN_VALUE = "Timeout"

# Initialize some global variables that will be reset later
__choiceboxMultipleSelect = None
__widgetTexts = None
__replyButtonText = None
__choiceboxResults = None
__firstWidget = None
__enterboxText = None
__enterboxDefaultText = ""
__multenterboxText = ""
choiceboxChoices = None
choiceboxWidget = None
entryWidget = None
boxRoot = None
buttonsFrame = None


def _alertTkinter(text="", title="", button=OK_TEXT, root=None, timeout=None):
    """Displays a simple message box with text and a single OK button. Returns the text of the button clicked on."""
    assert TKINTER_IMPORT_SUCCEEDED, "Tkinter is required for pymsgbox"
    text = str(text)
    retVal = _buttonbox(
        msg=text, title=title, choices=[str(button)], root=root, timeout=timeout
    )
    if retVal is None:
        return button
    else:
        return retVal


alert = _alertTkinter


def _confirmTkinter(
    text="", title="", buttons=(OK_TEXT, CANCEL_TEXT), root=None, timeout=None
):
    """Displays a message box with OK and Cancel buttons. Number and text of buttons can be customized. Returns the text of the button clicked on."""
    assert TKINTER_IMPORT_SUCCEEDED, "Tkinter is required for pymsgbox"
    text = str(text)
    return _buttonbox(
        msg=text,
        title=title,
        choices=[str(b) for b in buttons],
        root=root,
        timeout=timeout,
    )


confirm = _confirmTkinter


def _promptTkinter(text="", title="", default="", root=None, timeout=None):
    """Displays a message box with text input, and OK & Cancel buttons. Returns the text entered, or None if Cancel was clicked."""
    assert TKINTER_IMPORT_SUCCEEDED, "Tkinter is required for pymsgbox"
    text = str(text)
    return __fillablebox(
        text, title, default=default, mask=None, root=root, timeout=timeout
    )


prompt = _promptTkinter


def _passwordTkinter(text="", title="", default="", mask="*", root=None, timeout=None):
    """Displays a message box with text input, and OK & Cancel buttons. Typed characters appear as *. Returns the text entered, or None if Cancel was clicked."""
    assert TKINTER_IMPORT_SUCCEEDED, "Tkinter is required for pymsgbox"
    text = str(text)
    return __fillablebox(text, title, default, mask=mask, root=root, timeout=timeout)


password = _passwordTkinter


# Load the native versions of the alert/confirm/prompt/password functions, if available:
if sys.platform == "win32":
    from . import _native_win

    NO_ICON = 0
    STOP = 0x10
    QUESTION = 0x20
    WARNING = 0x30
    INFO = 0x40
    alert = _native_win.alert
    confirm = _native_win.confirm


def timeoutBoxRoot():
    global boxRoot, __replyButtonText, __enterboxText
    boxRoot.destroy()
    __replyButtonText = TIMEOUT_RETURN_VALUE
    __enterboxText = TIMEOUT_RETURN_VALUE


def _buttonbox(msg, title, choices, root=None, timeout=None):
    """
    Display a msg, a title, and a set of buttons.
    The buttons are defined by the members of the choices list.
    Return the text of the button that the user selected.

    @arg msg: the msg to be displayed.
    @arg title: the window title
    @arg choices: a list or tuple of the choices to be displayed
    """
    global boxRoot, __replyButtonText, __widgetTexts, buttonsFrame

    # Initialize __replyButtonText to the first choice.
    # This is what will be used if the window is closed by the close button.
    __replyButtonText = choices[0]

    if root:
        root.withdraw()
        boxRoot = tk.Toplevel(master=root)
        boxRoot.withdraw()
    else:
        boxRoot = tk.Tk()
        boxRoot.withdraw()

    boxRoot.title(title)
    boxRoot.iconname("Dialog")
    boxRoot.geometry(rootWindowPosition)
    boxRoot.minsize(400, 100)

    # ------------- define the messageFrame ---------------------------------
    messageFrame = tk.Frame(master=boxRoot)
    messageFrame.pack(side=tk.TOP, fill=tk.BOTH)

    # ------------- define the buttonsFrame ---------------------------------
    buttonsFrame = tk.Frame(master=boxRoot)
    buttonsFrame.pack(side=tk.TOP, fill=tk.BOTH)

    # -------------------- place the widgets in the frames -----------------------
    messageWidget = tk.Message(messageFrame, text=msg, width=400)
    messageWidget.configure(font=(PROPORTIONAL_FONT_FAMILY, PROPORTIONAL_FONT_SIZE))
    messageWidget.pack(side=tk.TOP, expand=tk.YES, fill=tk.X, padx="3m", pady="3m")

    __put_buttons_in_buttonframe(choices)

    # -------------- the action begins -----------
    # put the focus on the first button
    __firstWidget.focus_force()

    boxRoot.deiconify()
    if timeout is not None:
        boxRoot.after(timeout, timeoutBoxRoot)
    boxRoot.mainloop()
    try:
        boxRoot.destroy()
    except tk.TclError:
        if __replyButtonText != TIMEOUT_RETURN_VALUE:
            __replyButtonText = None

    if root:
        root.deiconify()
    return __replyButtonText


def __put_buttons_in_buttonframe(choices):
    """Put the buttons in the buttons frame"""
    global __widgetTexts, __firstWidget, buttonsFrame

    __firstWidget = None
    __widgetTexts = {}

    i = 0

    for buttonText in choices:
        tempButton = tk.Button(buttonsFrame, takefocus=1, text=buttonText)
        _bindArrows(tempButton)
        tempButton.pack(
            expand=tk.YES, side=tk.LEFT, padx="1m", pady="1m", ipadx="2m", ipady="1m"
        )

        # remember the text associated with this widget
        __widgetTexts[tempButton] = buttonText

        # remember the first widget, so we can put the focus there
        if i == 0:
            __firstWidget = tempButton
            i = 1

        # for the commandButton, bind activation events to the activation event handler
        commandButton = tempButton
        handler = __buttonEvent
        for selectionEvent in STANDARD_SELECTION_EVENTS:
            commandButton.bind("<%s>" % selectionEvent, handler)

        if CANCEL_TEXT in choices:
            commandButton.bind("<Escape>", __cancelButtonEvent)


def _bindArrows(widget, skipArrowKeys=False):
    widget.bind("<Down>", _tabRight)
    widget.bind("<Up>", _tabLeft)

    if not skipArrowKeys:
        widget.bind("<Right>", _tabRight)
        widget.bind("<Left>", _tabLeft)


def _tabRight(event):
    boxRoot.event_generate("<Tab>")


def _tabLeft(event):
    boxRoot.event_generate("<Shift-Tab>")


def __buttonEvent(event):
    """
    Handle an event that is generated by a person clicking a button.
    """
    global boxRoot, __widgetTexts, __replyButtonText
    __replyButtonText = __widgetTexts[event.widget]
    boxRoot.quit()  # quit the main loop


def __cancelButtonEvent(event):
    """Handle pressing Esc by clicking the Cancel button."""
    global boxRoot, __widgetTexts, __replyButtonText
    __replyButtonText = CANCEL_TEXT
    boxRoot.quit()


def __fillablebox(msg, title="", default="", mask=None, root=None, timeout=None):
    """
    Show a box in which a user can enter some text.
    You may optionally specify some default text, which will appear in the
    enterbox when it is displayed.
    Returns the text that the user entered, or None if he cancels the operation.
    """

    global boxRoot, __enterboxText, __enterboxDefaultText
    global cancelButton, entryWidget, okButton

    if title == None:
        title == ""
    if default == None:
        default = ""
    __enterboxDefaultText = default
    __enterboxText = __enterboxDefaultText

    if root:
        root.withdraw()
        boxRoot = tk.Toplevel(master=root)
        boxRoot.withdraw()
    else:
        boxRoot = tk.Tk()
        boxRoot.withdraw()

    boxRoot.title(title)
    boxRoot.iconname("Dialog")
    boxRoot.geometry(rootWindowPosition)
    boxRoot.bind("<Escape>", __enterboxCancel)

    # ------------- define the messageFrame ---------------------------------
    messageFrame = tk.Frame(master=boxRoot)
    messageFrame.pack(side=tk.TOP, fill=tk.BOTH)

    # ------------- define the buttonsFrame ---------------------------------
    buttonsFrame = tk.Frame(master=boxRoot)
    buttonsFrame.pack(side=tk.TOP, fill=tk.BOTH)

    # ------------- define the entryFrame ---------------------------------
    entryFrame = tk.Frame(master=boxRoot)
    entryFrame.pack(side=tk.TOP, fill=tk.BOTH)

    # ------------- define the buttonsFrame ---------------------------------
    buttonsFrame = tk.Frame(master=boxRoot)
    buttonsFrame.pack(side=tk.TOP, fill=tk.BOTH)

    # -------------------- the msg widget ----------------------------
    messageWidget = tk.Message(messageFrame, width="4.5i", text=msg)
    messageWidget.configure(font=(PROPORTIONAL_FONT_FAMILY, PROPORTIONAL_FONT_SIZE))
    messageWidget.pack(side=tk.RIGHT, expand=1, fill=tk.BOTH, padx="3m", pady="3m")

    # --------- entryWidget ----------------------------------------------
    entryWidget = tk.Entry(entryFrame, width=40)
    _bindArrows(entryWidget, skipArrowKeys=True)
    entryWidget.configure(font=(PROPORTIONAL_FONT_FAMILY, TEXT_ENTRY_FONT_SIZE))
    if mask:
        entryWidget.configure(show=mask)
    entryWidget.pack(side=tk.LEFT, padx="3m")
    entryWidget.bind("<Return>", __enterboxGetText)
    entryWidget.bind("<Escape>", __enterboxCancel)

    # put text into the entryWidget and have it pre-highlighted
    if __enterboxDefaultText != "":
        entryWidget.insert(0, __enterboxDefaultText)
        entryWidget.select_range(0, tk.END)

    # ------------------ ok button -------------------------------
    okButton = tk.Button(buttonsFrame, takefocus=1, text=OK_TEXT)
    _bindArrows(okButton)
    okButton.pack(expand=1, side=tk.LEFT, padx="3m", pady="3m", ipadx="2m", ipady="1m")

    # for the commandButton, bind activation events to the activation event handler
    commandButton = okButton
    handler = __enterboxGetText
    for selectionEvent in STANDARD_SELECTION_EVENTS:
        commandButton.bind("<%s>" % selectionEvent, handler)

    # ------------------ cancel button -------------------------------
    cancelButton = tk.Button(buttonsFrame, takefocus=1, text=CANCEL_TEXT)
    _bindArrows(cancelButton)
    cancelButton.pack(
        expand=1, side=tk.RIGHT, padx="3m", pady="3m", ipadx="2m", ipady="1m"
    )

    # for the commandButton, bind activation events to the activation event handler
    commandButton = cancelButton
    handler = __enterboxCancel
    for selectionEvent in STANDARD_SELECTION_EVENTS:
        commandButton.bind("<%s>" % selectionEvent, handler)

    # ------------------- time for action! -----------------
    entryWidget.focus_force()  # put the focus on the entryWidget
    boxRoot.deiconify()
    if timeout is not None:
        boxRoot.after(timeout, timeoutBoxRoot)
    boxRoot.mainloop()  # run it!

    # -------- after the run has completed ----------------------------------
    if root:
        root.deiconify()
    try:
        boxRoot.destroy()  # button_click didn't destroy boxRoot, so we do it now
    except tk.TclError:
        if __enterboxText != TIMEOUT_RETURN_VALUE:
            return None

    return __enterboxText


def __enterboxGetText(event):
    global __enterboxText

    __enterboxText = entryWidget.get()
    boxRoot.quit()


def __enterboxRestore(event):
    global entryWidget

    entryWidget.delete(0, len(entryWidget.get()))
    entryWidget.insert(0, __enterboxDefaultText)


def __enterboxCancel(event):
    global __enterboxText

    __enterboxText = None
    boxRoot.quit()
