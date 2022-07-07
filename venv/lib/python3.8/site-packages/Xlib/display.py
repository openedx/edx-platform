# Xlib.display -- high level display object
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

# Python modules
import types

# Xlib modules
from . import error, ext, X

# Xlib.protocol modules
from Xlib.protocol import display, request, event, rq

# Xlib.xobjects modules
import Xlib.xobject.resource
import Xlib.xobject.drawable
import Xlib.xobject.fontable
import Xlib.xobject.colormap
import Xlib.xobject.cursor

_resource_baseclasses = {
    'resource': Xlib.xobject.resource.Resource,
    'drawable': Xlib.xobject.drawable.Drawable,
    'window': Xlib.xobject.drawable.Window,
    'pixmap': Xlib.xobject.drawable.Pixmap,
    'fontable': Xlib.xobject.fontable.Fontable,
    'font': Xlib.xobject.fontable.Font,
    'gc': Xlib.xobject.fontable.GC,
    'colormap': Xlib.xobject.colormap.Colormap,
    'cursor': Xlib.xobject.cursor.Cursor,
    }

_resource_hierarchy = {
    'resource': ('drawable', 'window', 'pixmap',
                 'fontable', 'font', 'gc',
                 'colormap', 'cursor'),
    'drawable': ('window', 'pixmap'),
    'fontable': ('font', 'gc')
    }

class _BaseDisplay(display.Display):
    resource_classes = _resource_baseclasses.copy()

    # Implement a cache of atom names, used by Window objects when
    # dealing with some ICCCM properties not defined in Xlib.Xatom

    def __init__(self, *args, **keys):
        display.Display.__init__(*(self, ) + args, **keys)
        self._atom_cache = {}

    def get_atom(self, atomname, only_if_exists=0):
        if atomname in self._atom_cache:
            return self._atom_cache[atomname]

        r = request.InternAtom(display = self, name = atomname, only_if_exists = only_if_exists)

         # don't cache NONE responses in case someone creates this later
        if r.atom != X.NONE:
            self._atom_cache[atomname] = r.atom

        return r.atom


class Display:
    def __init__(self, display = None):
        self.display = _BaseDisplay(display)

        # Create the keymap cache
        self._keymap_codes = [()] * 256
        self._keymap_syms = {}
        self._update_keymap(self.display.info.min_keycode,
                            (self.display.info.max_keycode
                             - self.display.info.min_keycode + 1))

        # Translations for keysyms to strings.
        self.keysym_translations = {}

        # Find all supported extensions
        self.extensions = []
        self.class_extension_dicts = {}
        self.display_extension_methods = {}

        self.extension_event = rq.DictWrapper({})

        exts = self.list_extensions()

        # Go through all extension modules
        for extname, modname in ext.__extensions__:
            if extname in exts:

                # Import the module and fetch it
                __import__('ext.' + modname,globals(),level=1)
                mod = getattr(ext, modname)

                info = self.query_extension(extname)
                self.display.set_extension_major(extname, info.major_opcode)

                # Call initialiasation function
                mod.init(self, info)

                self.extensions.append(extname)


        # Finalize extensions by creating new classes
        for type_, dict in self.class_extension_dicts.items():
            origcls = self.display.resource_classes[type_]
            self.display.resource_classes[type_] = type(origcls.__name__,
                                                        (origcls, object),
                                                        dict)

        # Problem: we have already created some objects without the
        # extensions: the screen roots and default colormaps.
        # Fix that by reinstantiating them.
        for screen in self.display.info.roots:
            screen.root = self.display.resource_classes['window'](self.display, screen.root.id)
            screen.default_colormap = self.display.resource_classes['colormap'](self.display, screen.default_colormap.id)


    def get_display_name(self):
        """Returns the name used to connect to the server, either
        provided when creating the Display object, or fetched from the
        environmental variable $DISPLAY."""
        return self.display.get_display_name()

    def fileno(self):
        """Returns the file descriptor number of the underlying socket.
        This method is provided to allow Display objects to be passed
        select.select()."""
        return self.display.fileno()

    def close(self):
        """Close the display, freeing the resources that it holds."""
        self.display.close()

    def set_error_handler(self, handler):
        """Set the default error handler which will be called for all
        unhandled errors. handler should take two arguments as a normal
        request error handler, but the second argument (the request) will
        be None.  See section Error Handling."""
        self.display.set_error_handler(handler)

    def flush(self):
        """Flush the request queue, building and sending the queued
        requests. This can be necessary in applications that never wait
        for events, and in threaded applications."""
        self.display.flush()

    def sync(self):
        """Flush the queue and wait until the server has processed all
        the queued requests. Use this e.g. when it is important that
        errors caused by a certain request is trapped."""
        # Do a light-weight replyrequest to sync.  There must
        # be a better way to do it...
        self.get_pointer_control()

    def next_event(self):
        """Return the next event. If there are no events queued, it will
        block until the next event is fetched from the server."""
        return self.display.next_event()

    def pending_events(self):
        """Return the number of events queued, i.e. the number of times
        that Display.next_event() can be called without blocking."""
        return self.display.pending_events()

    def has_extension(self, extension):
        """Check if both the server and the client library support the X
        extension named extension."""
        return extension in self.extensions

    def create_resource_object(self, type, id):
        """Create a resource object of type for the integer id. type
        should be one of the following strings:

        resource
        drawable
        window
        pixmap
        fontable
        font
        gc
        colormap
        cursor

        This function can be used when a resource ID has been fetched
        e.g. from an resource or a command line argument. Resource
        objects should never be created by instantiating the appropriate
        class directly, since any X extensions dynamically added by the
        library will not be available.
        """
        return self.display.resource_classes[type](self.display, id)

    # We need this to handle display extension methods
    def __getattr__(self, attr):
        try:
            function = self.display_extension_methods[attr]
            return types.MethodType(function, self)
        except KeyError:
            raise AttributeError(attr)

    ###
    ### display information retrieval
    ###

    def screen(self, sno = None):
        if sno is None:
            return self.display.info.roots[self.display.default_screen]
        else:
            return self.display.info.roots[sno]

    def screen_count(self):
        """Return the total number of screens on the display."""
        return len(self.display.info.roots)

    def get_default_screen(self):
        """Return the number of the default screen, extracted from the
        display name."""
        return self.display.get_default_screen()

    ###
    ### Extension module interface
    ###

    def extension_add_method(self, object, name, function):
        """extension_add_method(object, name, function)

        Add an X extension module method.  OBJECT is the type of
        object to add the function to, a string from this list:

            display
            resource
            drawable
            window
            pixmap
            fontable
            font
            gc
            colormap
            cursor

        NAME is the name of the method, a string.  FUNCTION is a
        normal function whose first argument is a 'self'.
        """

        if object == 'display':
            if hasattr(self, name):
                raise AssertionError('attempting to replace display method: %s' % name)

            self.display_extension_methods[name] = function

        else:
            types = (object, ) + _resource_hierarchy.get(object, ())
            for type in types:
                cls = _resource_baseclasses[type]
                if hasattr(cls, name):
                    raise AssertionError('attempting to replace %s method: %s' % (type, name))

                # Maybe should check extension overrides too
                try:
                    self.class_extension_dicts[type][name] = function
                except KeyError:
                    self.class_extension_dicts[type] = { name: function }

    def extension_add_event(self, code, evt, name = None):
        """extension_add_event(code, evt, [name])

        Add an extension event.  CODE is the numeric code, and EVT is
        the event class.  EVT will be cloned, and the attribute _code
        of the new event class will be set to CODE.

        If NAME is omitted, it will be set to the name of EVT.  This
        name is used to insert an entry in the DictWrapper
        extension_event.
        """

        newevt = type(evt.__name__, evt.__bases__,
                      evt.__dict__.copy())
        newevt._code = code

        self.display.add_extension_event(code, newevt)

        if name is None:
            name = evt.__name__

        setattr(self.extension_event, name, code)


    def add_extension_error(self, code, err):
        """add_extension_error(code, err)

        Add an extension error.  CODE is the numeric code, and ERR is
        the error class.
        """

        self.display.add_extension_error(code, err)

    ###
    ### keymap cache implementation
    ###

    # The keycode->keysym map is stored in a list with 256 elements.
    # Each element represents a keycode, and the tuple elements are
    # the keysyms bound to the key.

    # The keysym->keycode map is stored in a mapping, where the keys
    # are keysyms.  The values are a sorted list of tuples with two
    # elements each: (index, keycode)
    # keycode is the code for a key to which this keysym is bound, and
    # index is the keysyms index in the map for that keycode.

    def keycode_to_keysym(self, keycode, index):
        """Convert a keycode to a keysym, looking in entry index.
        Normally index 0 is unshifted, 1 is shifted, 2 is alt grid, and 3
        is shift+alt grid. If that key entry is not bound, X.NoSymbol is
        returned."""
        try:
            return self._keymap_codes[keycode][index]
        except IndexError:
            return X.NoSymbol

    def keysym_to_keycode(self, keysym):
        """Look up the primary keycode that is bound to keysym. If
        several keycodes are found, the one with the lowest index and
        lowest code is returned. If keysym is not bound to any key, 0 is
        returned."""
        try:
            return self._keymap_syms[keysym][0][1]
        except (KeyError, IndexError):
            return 0

    def keysym_to_keycodes(self, keysym):
        """Look up all the keycodes that is bound to keysym. A list of
        tuples (keycode, index) is returned, sorted primarily on the
        lowest index and secondarily on the lowest keycode."""
        try:
            # Copy the map list, reversing the arguments
            return [(x[1], x[0]) for x in self._keymap_syms[keysym]]
        except KeyError:
            return []

    def refresh_keyboard_mapping(self, evt):
        """This method should be called once when a MappingNotify event
        is received, to update the keymap cache. evt should be the event
        object."""
        if isinstance(evt, event.MappingNotify):
            if evt.request == X.MappingKeyboard:
                self._update_keymap(evt.first_keycode, evt.count)
        else:
            raise TypeError('expected a MappingNotify event')

    def _update_keymap(self, first_keycode, count):
        """Internal function, called to refresh the keymap cache.
        """

        # Delete all sym->code maps for the changed codes

        lastcode = first_keycode + count
        for keysym, codes in self._keymap_syms.items():
            i = 0
            while i < len(codes):
                code = codes[i][1]
                if code >= first_keycode and code < lastcode:
                    del codes[i]
                else:
                    i = i + 1

        # Get the new keyboard mapping
        keysyms = self.get_keyboard_mapping(first_keycode, count)

        # Replace code->sym map with the new map
        self._keymap_codes[first_keycode:lastcode] = keysyms

        # Update sym->code map
        code = first_keycode
        for syms in keysyms:
            index = 0
            for sym in syms:
                if sym != X.NoSymbol:
                    if sym in self._keymap_syms:
                        symcodes = self._keymap_syms[sym]
                        symcodes.append((index, code))
                        symcodes.sort()
                    else:
                        self._keymap_syms[sym] = [(index, code)]

                index = index + 1
            code = code + 1

    ###
    ### client-internal keysym to string translations
    ###

    def lookup_string(self, keysym):
        """Return a string corresponding to KEYSYM, or None if no
        reasonable translation is found.
        """
        s = self.keysym_translations.get(keysym)
        if s is not None:
            return s

        import Xlib.XK
        return Xlib.XK.keysym_to_string(keysym)

    def rebind_string(self, keysym, newstring):
        """Change the translation of KEYSYM to NEWSTRING.
        If NEWSTRING is None, remove old translation if any.
        """
        if newstring is None:
            try:
                del self.keysym_translations[keysym]
            except KeyError:
                pass
        else:
            self.keysym_translations[keysym] = newstring


    ###
    ### X requests
    ###

    def intern_atom(self, name, only_if_exists = 0):
        """Intern the string name, returning its atom number. If
        only_if_exists is true and the atom does not already exist, it
        will not be created and X.NONE is returned."""
        r = request.InternAtom(display = self.display,
                               name = name,
                               only_if_exists = only_if_exists)
        return r.atom

    def get_atom(self, atom, only_if_exists = 0):
        """Alias for intern_atom, using internal cache"""
        return self.display.get_atom(atom, only_if_exists)


    def get_atom_name(self, atom):
        """Look up the name of atom, returning it as a string. Will raise
        BadAtom if atom does not exist."""
        r = request.GetAtomName(display = self.display,
                                atom = atom)
        return r.name

    def get_selection_owner(self, selection):
        """Return the window that owns selection (an atom), or X.NONE if
        there is no owner for the selection. Can raise BadAtom."""
        r = request.GetSelectionOwner(display = self.display,
                                      selection = selection)
        return r.owner

    def send_event(self, destination, event, event_mask = 0, propagate = 0,
                   onerror = None):
        """Send a synthetic event to the window destination which can be
        a window object, or X.PointerWindow or X.InputFocus. event is the
        event object to send, instantiated from one of the classes in
        protocol.events. See XSendEvent(3X11) for details.

        There is also a Window.send_event() method."""
        request.SendEvent(display = self.display,
                          onerror = onerror,
                          propagate = propagate,
                          destination = destination,
                          event_mask = event_mask,
                          event = event)

    def ungrab_pointer(self, time, onerror = None):
        """elease a grabbed pointer and any queued events. See
        XUngrabPointer(3X11)."""
        request.UngrabPointer(display = self.display,
                              onerror = onerror,
                              time = time)

    def change_active_pointer_grab(self, event_mask, cursor, time, onerror = None):
        """Change the dynamic parameters of a pointer grab. See
        XChangeActivePointerGrab(3X11)."""
        request.ChangeActivePointerGrab(display = self.display,
                                        onerror = onerror,
                                        cursor = cursor,
                                        time = time,
                                        event_mask = event_mask)

    def ungrab_keyboard(self, time, onerror = None):
        """Ungrab a grabbed keyboard and any queued events. See
        XUngrabKeyboard(3X11)."""
        request.UngrabKeyboard(display = self.display,
                               onerror = onerror,
                               time = time)

    def allow_events(self, mode, time, onerror = None):
        """Release some queued events. mode should be one of
        X.AsyncPointer, X.SyncPointer, X.AsyncKeyboard, X.SyncKeyboard,
        X.ReplayPointer, X.ReplayKeyboard, X.AsyncBoth, or X.SyncBoth.
        time should be a timestamp or X.CurrentTime."""
        request.AllowEvents(display = self.display,
                            onerror = onerror,
                            mode = mode,
                            time = time)

    def grab_server(self, onerror = None):
        """Disable processing of requests on all other client connections
        until the server is ungrabbed. Server grabbing should be avoided
        as much as possible."""
        request.GrabServer(display = self.display,
                           onerror = onerror)

    def ungrab_server(self, onerror = None):
        """Release the server if it was previously grabbed by this client."""
        request.UngrabServer(display = self.display,
                             onerror = onerror)

    def warp_pointer(self, x, y, src_window = X.NONE, src_x = 0, src_y = 0,
                     src_width = 0, src_height = 0, onerror = None):
        """Move the pointer relative its current position by the offsets
        (x, y). However, if src_window is a window the pointer is only
        moved if the specified rectangle in src_window contains it. If
        src_width is 0 it will be replaced with the width of src_window -
        src_x. src_height is treated in a similar way.

        To move the pointer to absolute coordinates, use Window.warp_pointer()."""
        request.WarpPointer(display = self.display,
                            onerror = onerror,
                            src_window = src_window,
                            dst_window = X.NONE,
                            src_x = src_x,
                            src_y = src_y,
                            src_width = src_width,
                            src_height = src_height,
                            dst_x = x,
                            dst_y = y)

    def set_input_focus(self, focus, revert_to, time, onerror = None):
        """Set input focus to focus, which should be a window,
        X.PointerRoot or X.NONE. revert_to specifies where the focus
        reverts to if the focused window becomes not visible, and should
        be X.RevertToParent, RevertToPointerRoot, or RevertToNone. See
        XSetInputFocus(3X11) for details.

        There is also a Window.set_input_focus()."""
        request.SetInputFocus(display = self.display,
                              onerror = onerror,
                              revert_to = revert_to,
                              focus = focus,
                              time = time)

    def get_input_focus(self):
        """Return an object with the following attributes:

        focus
            The window which currently holds the input
            focus, X.NONE or X.PointerRoot.
        revert_to
            Where the focus will revert, one of X.RevertToParent,
            RevertToPointerRoot, or RevertToNone. """
        return request.GetInputFocus(display = self.display)

    def query_keymap(self):
        """Return a bit vector for the logical state of the keyboard,
        where each bit set to 1 indicates that the corresponding key is
        currently pressed down. The vector is represented as a list of 32
        integers. List item N contains the bits for keys 8N to 8N + 7
        with the least significant bit in the byte representing key 8N."""
        r = request.QueryKeymap(display = self.display)
        return r.map

    def open_font(self, name):
        """Open the font identifed by the pattern name and return its
        font object. If name does not match any font, None is returned."""
        fid = self.display.allocate_resource_id()
        ec = error.CatchError(error.BadName)

        request.OpenFont(display = self.display,
                         onerror = ec,
                         fid = fid,
                         name = name)
        self.sync()

        if ec.get_error():
            self.display.free_resource_id(fid)
            return None
        else:
            cls = self.display.get_resource_class('font', Xlib.xobject.fontable.Font)
            return cls(self.display, fid, owner = 1)

    def list_fonts(self, pattern, max_names):
        """Return a list of font names matching pattern. No more than
        max_names will be returned."""
        r = request.ListFonts(display = self.display,
                              max_names = max_names,
                              pattern = pattern)
        return r.fonts

    def list_fonts_with_info(self, pattern, max_names):
        """Return a list of fonts matching pattern. No more than
        max_names will be returned. Each list item represents one font
        and has the following properties:

        name
            The name of the font.
        min_bounds
        max_bounds
        min_char_or_byte2
        max_char_or_byte2
        default_char
        draw_direction
        min_byte1
        max_byte1
        all_chars_exist
        font_ascent
        font_descent
        replies_hint
            See the descripton of XFontStruct in XGetFontProperty(3X11)
            for details on these values.
        properties
            A list of properties. Each entry has two attributes:

            name
                The atom identifying this property.
            value
                A 32-bit unsigned value.
        """
        return request.ListFontsWithInfo(display = self.display,
                                         max_names = max_names,
                                         pattern = pattern)

    def set_font_path(self, path, onerror = None):
        """Set the font path to path, which should be a list of strings.
        If path is empty, the default font path of the server will be
        restored."""
        request.SetFontPath(display = self.display,
                            onerror = onerror,
                            path = path)

    def get_font_path(self):
        """Return the current font path as a list of strings."""
        r = request.GetFontPath(display = self.display)
        return r.paths

    def query_extension(self, name):
        """Ask the server if it supports the extension name. If it is
        supported an object with the following attributes is returned:

        major_opcode
            The major opcode that the requests of this extension uses.
        first_event
            The base event code if the extension have additional events, or 0.
        first_error
            The base error code if the extension have additional errors, or 0.

        If the extension is not supported, None is returned."""
        r = request.QueryExtension(display = self.display,
                                   name = name)
        if r.present:
            return r
        else:
            return None

    def list_extensions(self):
        """Return a list of all the extensions provided by the server."""
        r = request.ListExtensions(display = self.display)
        return r.names

    def change_keyboard_mapping(self, first_keycode, keysyms, onerror = None):
        """Modify the keyboard mapping, starting with first_keycode.
        keysyms is a list of tuples of keysyms. keysyms[n][i] will be
        assigned to keycode first_keycode+n at index i."""
        request.ChangeKeyboardMapping(display = self.display,
                                      onerror = onerror,
                                      first_keycode = first_keycode,
                                      keysyms = keysyms)

    def get_keyboard_mapping(self, first_keycode, count):
        """Return the current keyboard mapping as a list of tuples,
        starting at first_keycount and no more than count."""
        r = request.GetKeyboardMapping(display = self.display,
                                       first_keycode = first_keycode,
                                       count = count)
        return r.keysyms

    def change_keyboard_control(self, onerror = None, **keys):
        """Change the parameters provided as keyword arguments:

        key_click_percent
            The volume of key clicks between 0 (off) and 100 (load).
            -1 will restore default setting.
        bell_percent
            The base volume of the bell, coded as above.
        bell_pitch
            The pitch of the bell in Hz, -1 restores the default.
        bell_duration
            The duration of the bell in milliseconds, -1 restores
            the default.
        led

        led_mode
            led_mode should be X.LedModeOff or X.LedModeOn. If led is
            provided, it should be a 32-bit mask listing the LEDs that
            should change. If led is not provided, all LEDs are changed.
        key

        auto_repeat_mode
            auto_repeat_mode should be one of X.AutoRepeatModeOff,
            X.AutoRepeatModeOn, or X.AutoRepeatModeDefault. If key is
            provided, that key will be modified, otherwise the global
            state for the entire keyboard will be modified."""
        request.ChangeKeyboardControl(display = self.display,
                                      onerror = onerror,
                                      attrs = keys)

    def get_keyboard_control(self):
        """Return an object with the following attributes:

        global_auto_repeat
            X.AutoRepeatModeOn or X.AutoRepeatModeOff.

        auto_repeats
            A list of 32 integers. List item N contains the bits for keys
            8N to 8N + 7 with the least significant bit in the byte
            representing key 8N. If a bit is on, autorepeat is enabled
            for the corresponding key.

        led_mask
            A 32-bit mask indicating which LEDs are on.

        key_click_percent
            The volume of key click, from 0 to 100.

        bell_percent

        bell_pitch

        bell_duration
            The volume, pitch and duration of the bell. """
        return request.GetKeyboardControl(display = self.display)

    def bell(self, percent = 0, onerror = None):
        """Ring the bell at the volume percent which is relative the base
        volume. See XBell(3X11)."""
        request.Bell(display = self.display,
                     onerror = onerror,
                     percent = percent)

    def change_pointer_control(self, accel = None, threshold = None, onerror = None):
        """To change the pointer acceleration, set accel to a tuple (num,
        denum). The pointer will then move num/denum times the normal
        speed if it moves beyond the threshold number of pixels at once.
        To change the threshold, set it to the number of pixels. -1
        restores the default."""
        if accel is None:
            do_accel = 0
            accel_num = 0
            accel_denum = 0
        else:
            do_accel = 1
            accel_num, accel_denum = accel

        if threshold is None:
            do_threshold = 0
        else:
            do_threshold = 1

        request.ChangePointerControl(display = self.display,
                                     onerror = onerror,
                                     do_accel = do_accel,
                                     do_thres = do_threshold,
                                     accel_num = accel_num,
                                     accel_denum = accel_denum,
                                     threshold = threshold)

    def get_pointer_control(self):
        """Return an object with the following attributes:

        accel_num

        accel_denom
            The acceleration as numerator/denumerator.

        threshold
            The number of pixels the pointer must move before the
            acceleration kicks in."""
        return request.GetPointerControl(display = self.display)

    def set_screen_saver(self, timeout, interval, prefer_blank, allow_exposures, onerror = None):
        """See XSetScreenSaver(3X11)."""
        request.SetScreenSaver(display = self.display,
                               onerror = onerror,
                               timeout = timeout,
                               interval = interval,
                               prefer_blank = prefer_blank,
                               allow_exposures = allow_exposures)

    def get_screen_saver(self):
        """Return an object with the attributes timeout, interval,
        prefer_blanking, allow_exposures. See XGetScreenSaver(3X11) for
        details."""
        return request.GetScreenSaver(display = self.display)

    def change_hosts(self, mode, host_family, host, onerror = None):
        """mode is either X.HostInsert or X.HostDelete. host_family is
        one of X.FamilyInternet, X.FamilyDECnet or X.FamilyChaos.

        host is a list of bytes. For the Internet family, it should be the
        four bytes of an IPv4 address."""
        request.ChangeHosts(display = self.display,
                            onerror = onerror,
                            mode = mode,
                            host_family = host_family,
                            host = host)

    def list_hosts(self):
        """Return an object with the following attributes:

mode
    X.EnableAccess if the access control list is used, X.DisableAccess otherwise.
hosts
    The hosts on the access list. Each entry has the following attributes:

    family
        X.FamilyInternet, X.FamilyDECnet, or X.FamilyChaos.
    name
        A list of byte values, the coding depends on family. For the Internet family, it is the 4 bytes of an IPv4 address.

"""
        return request.ListHosts(display = self.display)

    def set_access_control(self, mode, onerror = None):
        """Enable use of access control lists at connection setup if mode
        is X.EnableAccess, disable if it is X.DisableAccess."""
        request.SetAccessControl(display = self.display,
                                 onerror = onerror,
                                 mode = mode)

    def set_close_down_mode(self, mode, onerror = None):
        """Control what will happen with the client's resources at
        connection close. The default is X.DestroyAll, the other values
        are X.RetainPermanent and X.RetainTemporary."""
        request.SetCloseDownMode(display = self.display,
                                 onerror = onerror,
                                 mode = mode)

    def force_screen_saver(self, mode, onerror = None):
        """If mode is X.ScreenSaverActive the screen saver is activated.
        If it is X.ScreenSaverReset, the screen saver is deactivated as
        if device input had been received."""
        request.ForceScreenSaver(display = self.display,
                                 onerror = onerror,
                                 mode = mode)

    def set_pointer_mapping(self, map):
        """Set the mapping of the pointer buttons. map is a list of
        logical button numbers. map must be of the same length as the
        list returned by Display.get_pointer_mapping().

        map[n] sets the
        logical number for the physical button n+1. Logical number 0
        disables the button. Two physical buttons cannot be mapped to the
        same logical number.

        If one of the buttons to be altered are
        logically in the down state, X.MappingBusy is returned and the
        mapping is not changed. Otherwise the mapping is changed and
        X.MappingSuccess is returned."""
        r = request.SetPointerMapping(display = self.display,
                                      map = map)
        return r.status

    def get_pointer_mapping(self):
        """Return a list of the pointer button mappings. Entry N in the
        list sets the logical button number for the physical button N+1."""
        r = request.GetPointerMapping(display = self.display)
        return r.map

    def set_modifier_mapping(self, keycodes):
        """Set the keycodes for the eight modifiers X.Shift, X.Lock,
        X.Control, X.Mod1, X.Mod2, X.Mod3, X.Mod4 and X.Mod5. keycodes
        should be a eight-element list where each entry is a list of the
        keycodes that should be bound to that modifier.

        If any changed
        key is logically in the down state, X.MappingBusy is returned and
        the mapping is not changed. If the mapping violates some server
        restriction, X.MappingFailed is returned. Otherwise the mapping
        is changed and X.MappingSuccess is returned."""
        r = request.SetModifierMapping(display = self.display,
                                       keycodes = keycodes)
        return r.status

    def get_modifier_mapping(self):
        """Return a list of eight lists, one for each modifier. The list
        can be indexed using X.ShiftMapIndex, X.Mod1MapIndex, and so on.
        The sublists list the keycodes bound to that modifier."""
        r = request.GetModifierMapping(display = self.display)
        return r.keycodes

    def no_operation(self, onerror = None):
        """Do nothing but send a request to the server."""
        request.NoOperation(display = self.display,
                            onerror = onerror)
