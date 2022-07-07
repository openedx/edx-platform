# Xlib.X -- basic X constants
#
#    Copyright (C) 2000 Peter Liljenberg <petli@ctrl-c.liu.se>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# Avoid overwriting None if doing "from Xlib.X import *"
NONE                = 0

ParentRelative      = 1  # background pixmap in CreateWindow
                         # and ChangeWindowAttributes

CopyFromParent      = 0  # border pixmap in CreateWindow
                         # and ChangeWindowAttributes
                         # special VisualID and special window
                         # class passed to CreateWindow

PointerWindow       = 0  # destination window in SendEvent
InputFocus          = 1  # destination window in SendEvent
PointerRoot         = 1  # focus window in SetInputFocus
AnyPropertyType     = 0  # special Atom, passed to GetProperty
AnyKey              = 0  # special Key Code, passed to GrabKey
AnyButton           = 0  # special Button Code, passed to GrabButton
AllTemporary        = 0  # special Resource ID passed to KillClient
CurrentTime         = 0  # special Time
NoSymbol            = 0  # special KeySym


#-----------------------------------------------------------------------
# Event masks:
#
NoEventMask               = 0
KeyPressMask              = (1<<0)
KeyReleaseMask            = (1<<1)
ButtonPressMask           = (1<<2)
ButtonReleaseMask         = (1<<3)
EnterWindowMask           = (1<<4)
LeaveWindowMask           = (1<<5)
PointerMotionMask         = (1<<6)
PointerMotionHintMask     = (1<<7)
Button1MotionMask         = (1<<8)
Button2MotionMask         = (1<<9)
Button3MotionMask         = (1<<10)
Button4MotionMask         = (1<<11)
Button5MotionMask         = (1<<12)
ButtonMotionMask          = (1<<13)
KeymapStateMask           = (1<<14)
ExposureMask              = (1<<15)
VisibilityChangeMask      = (1<<16)
StructureNotifyMask       = (1<<17)
ResizeRedirectMask        = (1<<18)
SubstructureNotifyMask    = (1<<19)
SubstructureRedirectMask  = (1<<20)
FocusChangeMask           = (1<<21)
PropertyChangeMask        = (1<<22)
ColormapChangeMask        = (1<<23)
OwnerGrabButtonMask       = (1<<24)

#-----------------------------------------------------------------------
# Event names:
#
# Used in "type" field in XEvent structures.  Not to be confused with event
# masks above.  They start from 2 because 0 and 1 are reserved in the
# protocol for errors and replies.
#
KeyPress               = 2
KeyRelease             = 3
ButtonPress            = 4
ButtonRelease          = 5
MotionNotify           = 6
EnterNotify            = 7
LeaveNotify            = 8
FocusIn                = 9
FocusOut               = 10
KeymapNotify           = 11
Expose                 = 12
GraphicsExpose         = 13
NoExpose               = 14
VisibilityNotify       = 15
CreateNotify           = 16
DestroyNotify          = 17
UnmapNotify            = 18
MapNotify              = 19
MapRequest             = 20
ReparentNotify         = 21
ConfigureNotify        = 22
ConfigureRequest       = 23
GravityNotify          = 24
ResizeRequest          = 25
CirculateNotify        = 26
CirculateRequest       = 27
PropertyNotify         = 28
SelectionClear         = 29
SelectionRequest       = 30
SelectionNotify        = 31
ColormapNotify         = 32
ClientMessage          = 33
MappingNotify          = 34
LASTEvent              = 35    # must be bigger than any event


#-----------------------------------------------------------------------
# Key masks:
#
# Used as modifiers to GrabButton and GrabKey, results of QueryPointer,
# state in various key-, mouse-, and button-related events.
#
ShiftMask = (1<<0)
LockMask = (1<<1)
ControlMask = (1<<2)
Mod1Mask = (1<<3)
Mod2Mask = (1<<4)
Mod3Mask = (1<<5)
Mod4Mask = (1<<6)
Mod5Mask = (1<<7)


#-----------------------------------------------------------------------
# Modifier names:
#
# Used to build a SetModifierMapping request or to read a
# GetModifierMapping request.  These correspond to the masks defined above.
#
ShiftMapIndex = 0
LockMapIndex = 1
ControlMapIndex = 2
Mod1MapIndex = 3
Mod2MapIndex = 4
Mod3MapIndex = 5
Mod4MapIndex = 6
Mod5MapIndex = 7

#-----------------------------------------------------------------------
# Button masks:
#
# Used in same manner as Key masks above. Not to be confused with button
# names below.  Note that 0 is already defined above as "AnyButton".
#
Button1Mask            = (1<<8)
Button2Mask            = (1<<9)
Button3Mask            = (1<<10)
Button4Mask            = (1<<11)
Button5Mask            = (1<<12)

AnyModifier            = (1<<15)  # used in GrabButton, GrabKey

#-----------------------------------------------------------------------
# Button names:
#
# Used as arguments to GrabButton and as detail in ButtonPress and
# ButtonRelease events.  Not to be confused with button masks above.
# Note that 0 is already defined above as "AnyButton".
#
Button1                = 1
Button2                = 2
Button3                = 3
Button4                = 4
Button5                = 5


#-----------------------------------------------------------------------
# XXX These still need documentation -- for now, read <X11/X.h>
#
NotifyNormal = 0
NotifyGrab = 1
NotifyUngrab = 2
NotifyWhileGrabbed = 3
NotifyHint = 1
NotifyAncestor = 0
NotifyVirtual = 1
NotifyInferior = 2
NotifyNonlinear = 3
NotifyNonlinearVirtual = 4
NotifyPointer = 5
NotifyPointerRoot = 6
NotifyDetailNone = 7
VisibilityUnobscured = 0
VisibilityPartiallyObscured = 1
VisibilityFullyObscured = 2
PlaceOnTop = 0
PlaceOnBottom = 1
FamilyInternet = 0
FamilyDECnet = 1
FamilyChaos = 2
PropertyNewValue = 0
PropertyDelete = 1
ColormapUninstalled = 0
ColormapInstalled = 1
GrabModeSync = 0
GrabModeAsync = 1
GrabSuccess = 0
AlreadyGrabbed = 1
GrabInvalidTime = 2
GrabNotViewable = 3
GrabFrozen = 4
AsyncPointer = 0
SyncPointer = 1
ReplayPointer = 2
AsyncKeyboard = 3
SyncKeyboard = 4
ReplayKeyboard = 5
AsyncBoth = 6
SyncBoth = 7
RevertToNone = 0
RevertToPointerRoot = PointerRoot
RevertToParent = 2
Success = 0
BadRequest = 1
BadValue = 2
BadWindow = 3
BadPixmap = 4
BadAtom = 5
BadCursor = 6
BadFont = 7
BadMatch = 8
BadDrawable = 9
BadAccess = 10
BadAlloc = 11
BadColor = 12
BadGC = 13
BadIDChoice = 14
BadName = 15
BadLength = 16
BadImplementation = 17
FirstExtensionError = 128
LastExtensionError = 255
InputOutput = 1
InputOnly = 2
CWBackPixmap = (1<<0)
CWBackPixel = (1<<1)
CWBorderPixmap = (1<<2)
CWBorderPixel = (1<<3)
CWBitGravity = (1<<4)
CWWinGravity = (1<<5)
CWBackingStore = (1<<6)
CWBackingPlanes = (1<<7)
CWBackingPixel = (1<<8)
CWOverrideRedirect = (1<<9)
CWSaveUnder = (1<<10)
CWEventMask = (1<<11)
CWDontPropagate = (1<<12)
CWColormap = (1<<13)
CWCursor = (1<<14)
CWX = (1<<0)
CWY = (1<<1)
CWWidth = (1<<2)
CWHeight = (1<<3)
CWBorderWidth = (1<<4)
CWSibling = (1<<5)
CWStackMode = (1<<6)
ForgetGravity = 0
NorthWestGravity = 1
NorthGravity = 2
NorthEastGravity = 3
WestGravity = 4
CenterGravity = 5
EastGravity = 6
SouthWestGravity = 7
SouthGravity = 8
SouthEastGravity = 9
StaticGravity = 10
UnmapGravity = 0
NotUseful = 0
WhenMapped = 1
Always = 2
IsUnmapped = 0
IsUnviewable = 1
IsViewable = 2
SetModeInsert = 0
SetModeDelete = 1
DestroyAll = 0
RetainPermanent = 1
RetainTemporary = 2
Above = 0
Below = 1
TopIf = 2
BottomIf = 3
Opposite = 4
RaiseLowest = 0
LowerHighest = 1
PropModeReplace = 0
PropModePrepend = 1
PropModeAppend = 2
GXclear = 0x0
GXand = 0x1
GXandReverse = 0x2
GXcopy = 0x3
GXandInverted = 0x4
GXnoop = 0x5
GXxor = 0x6
GXor = 0x7
GXnor = 0x8
GXequiv = 0x9
GXinvert = 0xa
GXorReverse = 0xb
GXcopyInverted = 0xc
GXorInverted = 0xd
GXnand = 0xe
GXset = 0xf
LineSolid = 0
LineOnOffDash = 1
LineDoubleDash = 2
CapNotLast = 0
CapButt = 1
CapRound = 2
CapProjecting = 3
JoinMiter = 0
JoinRound = 1
JoinBevel = 2
FillSolid = 0
FillTiled = 1
FillStippled = 2
FillOpaqueStippled = 3
EvenOddRule = 0
WindingRule = 1
ClipByChildren = 0
IncludeInferiors = 1
Unsorted = 0
YSorted = 1
YXSorted = 2
YXBanded = 3
CoordModeOrigin = 0
CoordModePrevious = 1
Complex = 0
Nonconvex = 1
Convex = 2
ArcChord = 0
ArcPieSlice = 1
GCFunction = (1<<0)
GCPlaneMask = (1<<1)
GCForeground = (1<<2)
GCBackground = (1<<3)
GCLineWidth = (1<<4)
GCLineStyle = (1<<5)
GCCapStyle = (1<<6)
GCJoinStyle = (1<<7)
GCFillStyle = (1<<8)
GCFillRule = (1<<9)
GCTile = (1<<10)
GCStipple = (1<<11)
GCTileStipXOrigin = (1<<12)
GCTileStipYOrigin = (1<<13)
GCFont = (1<<14)
GCSubwindowMode = (1<<15)
GCGraphicsExposures = (1<<16)
GCClipXOrigin = (1<<17)
GCClipYOrigin = (1<<18)
GCClipMask = (1<<19)
GCDashOffset = (1<<20)
GCDashList = (1<<21)
GCArcMode = (1<<22)
GCLastBit = 22
FontLeftToRight = 0
FontRightToLeft = 1
FontChange = 255
XYBitmap = 0
XYPixmap = 1
ZPixmap = 2
AllocNone = 0
AllocAll = 1
DoRed = (1<<0)
DoGreen = (1<<1)
DoBlue = (1<<2)
CursorShape = 0
TileShape = 1
StippleShape = 2
AutoRepeatModeOff = 0
AutoRepeatModeOn = 1
AutoRepeatModeDefault = 2
LedModeOff = 0
LedModeOn = 1
KBKeyClickPercent = (1<<0)
KBBellPercent = (1<<1)
KBBellPitch = (1<<2)
KBBellDuration = (1<<3)
KBLed = (1<<4)
KBLedMode = (1<<5)
KBKey = (1<<6)
KBAutoRepeatMode = (1<<7)
MappingSuccess = 0
MappingBusy = 1
MappingFailed = 2
MappingModifier = 0
MappingKeyboard = 1
MappingPointer = 2
DontPreferBlanking = 0
PreferBlanking = 1
DefaultBlanking = 2
DisableScreenSaver = 0
DisableScreenInterval = 0
DontAllowExposures = 0
AllowExposures = 1
DefaultExposures = 2
ScreenSaverReset = 0
ScreenSaverActive = 1
HostInsert = 0
HostDelete = 1
EnableAccess = 1
DisableAccess = 0
StaticGray = 0
GrayScale = 1
StaticColor = 2
PseudoColor = 3
TrueColor = 4
DirectColor = 5
LSBFirst = 0
MSBFirst = 1
