# -*- coding: latin-1 -*-
#
# Xlib.protocol.display -- core display communication
#
#    Copyright (C) 2000-2002 Peter Liljenberg <petli@ctrl-c.liu.se>
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

# Standard modules
import errno
import select
import socket
import struct
import sys

# Xlib modules
from Xlib import error

from Xlib.support import lock, connect

# Xlib.protocol modules
from . import rq, event

# in Python 3, bytes are an actual array; in python 2, bytes are still
# string-like, so in order to get an array element we need to call ord()
if sys.version[0] >= '3':
    def _bytes_item(x):
        return x
else:
    def _bytes_item(x):
        return ord(x)


class Display:
    resource_classes = {}
    extension_major_opcodes = {}
    error_classes = error.xerror_class.copy()
    event_classes = event.event_class.copy()

    def __init__(self, display = None):
        name, host, displayno, screenno = connect.get_display(display)

        self.display_name = name
        self.default_screen = screenno

        self.socket = connect.get_socket(name, host, displayno)

        auth_name, auth_data = connect.get_auth(self.socket,
                                                name, host, displayno)

        # Internal structures for communication, grouped
        # by their function and locks

        # Socket error indicator, set when the socket is closed
        # in one way or another
        self.socket_error_lock = lock.allocate_lock()
        self.socket_error = None

        # Event queue
        self.event_queue_read_lock = lock.allocate_lock()
        self.event_queue_write_lock = lock.allocate_lock()
        self.event_queue = []

        # Unsent request queue and sequence number counter
        self.request_queue_lock = lock.allocate_lock()
        self.request_serial = 1
        self.request_queue = []

        # Send-and-recieve loop, see function send_and_recive
        # for a detailed explanation
        self.send_recv_lock = lock.allocate_lock()
        self.send_active = 0
        self.recv_active = 0

        self.event_waiting = 0
        self.event_wait_lock = lock.allocate_lock()
        self.request_waiting = 0
        self.request_wait_lock = lock.allocate_lock()

        # Data used by the send-and-recieve loop
        self.sent_requests = []
        self.request_length = 0
        self.data_send = b''
        self.data_recv = b''
        self.data_sent_bytes = 0

        # Resource ID structures
        self.resource_id_lock = lock.allocate_lock()
        self.resource_ids = {}
        self.last_resource_id = 0

        # Use an default error handler, one which just prints the error
        self.error_handler = None


        # Right, now we're all set up for the connection setup
        # request with the server.

        # Figure out which endianess the hardware uses
        self.big_endian = struct.unpack('BB', struct.pack('H', 0x0100))[0]

        if self.big_endian:
            order = 0x42
        else:
            order = 0x6c

        # Send connection setup
        r = ConnectionSetupRequest(self,
                                   byte_order = order,
                                   protocol_major = 11,
                                   protocol_minor = 0,
                                   auth_prot_name = auth_name,
                                   auth_prot_data = auth_data)

        # Did connection fail?
        if r.status != 1:
            raise error.DisplayConnectionError(self.display_name, r.reason)

        # Set up remaining info
        self.info = r
        self.default_screen = min(self.default_screen, len(self.info.roots) - 1)


    #
    # Public interface
    #

    def get_display_name(self):
        return self.display_name

    def get_default_screen(self):
        return self.default_screen

    def fileno(self):
        self.check_for_error()
        return self.socket.fileno()

    def next_event(self):
        self.check_for_error()

        # Main lock, so that only one thread at a time performs the
        # event waiting code.  This at least guarantees that the first
        # thread calling next_event() will get the next event, although
        # no order is guaranteed among other threads calling next_event()
        # while the first is blocking.

        self.event_queue_read_lock.acquire()

        # Lock event queue, so we can check if it is empty
        self.event_queue_write_lock.acquire()

        # We have too loop until we get an event, as
        # we might be woken up when there is no event.

        while not self.event_queue:

            # Lock send_recv so no send_and_recieve
            # can start or stop while we're checking
            # whether there are one active.
            self.send_recv_lock.acquire()

            # Release event queue to allow an send_and_recv to
            # insert any now.
            self.event_queue_write_lock.release()

            # Call send_and_recv, which will return when
            # something has occured
            self.send_and_recv(event = 1)

            # Before looping around, lock the event queue against
            # modifications.
            self.event_queue_write_lock.acquire()

        # Whiew, we have an event!  Remove it from
        # the event queue and relaese its write lock.

        event = self.event_queue[0]
        del self.event_queue[0]
        self.event_queue_write_lock.release()

        # Finally, allow any other threads which have called next_event()
        # while we were waiting to proceed.

        self.event_queue_read_lock.release()

        # And return the event!
        return event

    def pending_events(self):
        self.check_for_error()

        # Make a send_and_recv pass, receiving any events
        self.send_recv_lock.acquire()
        self.send_and_recv(recv = 1)

        # Lock the queue, get the event count, and unlock again.
        self.event_queue_write_lock.acquire()
        count = len(self.event_queue)
        self.event_queue_write_lock.release()

        return count

    def flush(self):
        self.check_for_error()
        self.send_recv_lock.acquire()
        self.send_and_recv(flush = 1)

    def close(self):
        self.flush()
        self.close_internal('client')

    def set_error_handler(self, handler):
        self.error_handler = handler


    def allocate_resource_id(self):
        """id = d.allocate_resource_id()

        Allocate a new X resource id number ID.

        Raises ResourceIDError if there are no free resource ids.
        """

        self.resource_id_lock.acquire()
        try:
            i = self.last_resource_id
            while i in self.resource_ids:
                i = i + 1
                if i > self.info.resource_id_mask:
                    i = 0
                if i == self.last_resource_id:
                    raise error.ResourceIDError('out of resource ids')

            self.resource_ids[i] = None
            self.last_resource_id = i
            return self.info.resource_id_base | i
        finally:
            self.resource_id_lock.release()

    def free_resource_id(self, rid):
        """d.free_resource_id(rid)

        Free resource id RID.  Attempts to free a resource id which
        isn't allocated by us are ignored.
        """

        self.resource_id_lock.acquire()
        try:
            i = rid & self.info.resource_id_mask

            # Attempting to free a resource id outside our range
            if rid - i != self.info.resource_id_base:
                return None

            try:
                del self.resource_ids[i]
            except KeyError:
                pass
        finally:
            self.resource_id_lock.release()



    def get_resource_class(self, class_name, default = None):
        """class = d.get_resource_class(class_name, default = None)

        Return the class to be used for X resource objects of type
        CLASS_NAME, or DEFAULT if no such class is set.
        """

        return self.resource_classes.get(class_name, default)

    def set_extension_major(self, extname, major):
        self.extension_major_opcodes[extname] = major

    def get_extension_major(self, extname):
        return self.extension_major_opcodes[extname]

    def add_extension_event(self, code, evt):
        self.event_classes[code] = evt

    def add_extension_error(self, code, err):
        self.error_classes[code] = err


    #
    # Private functions
    #

    def check_for_error(self):
        self.socket_error_lock.acquire()
        err = self.socket_error
        self.socket_error_lock.release()

        if err:
            raise err

    def send_request(self, request, wait_for_response):
        if self.socket_error:
            raise self.socket_error

        self.request_queue_lock.acquire()

        request._serial = self.request_serial
        self.request_serial = (self.request_serial + 1) % 65536

        self.request_queue.append((request, wait_for_response))
        qlen = len(self.request_queue)

        self.request_queue_lock.release()

#       if qlen > 10:
#           self.flush()

    def close_internal(self, whom):
        # Clear out data structures
        self.request_queue = None
        self.sent_requests = None
        self.event_queue = None
        self.data_send = None
        self.data_recv = None

        # Close the connection
        self.socket.close()

        # Set a connection closed indicator
        self.socket_error_lock.acquire()
        self.socket_error = error.ConnectionClosedError(whom)
        self.socket_error_lock.release()


    def send_and_recv(self, flush = None, event = None, request = None, recv = None):
        """send_and_recv(flush = None, event = None, request = None, recv = None)

        Perform I/O, or wait for some other thread to do it for us.

        send_recv_lock MUST be LOCKED when send_and_recv is called.
        It will be UNLOCKED at return.

        Exactly or one of the parameters flush, event, request and recv must
        be set to control the return condition.

        To attempt to send all requests in the queue, flush should
        be true.  Will return immediately if another thread is
        already doing send_and_recv.

        To wait for an event to be recieved, event should be true.

        To wait for a response to a certain request (either an error
        or a response), request should be set the that request's
        serial number.

        To just read any pending data from the server, recv should be true.

        It is not guaranteed that the return condition has been
        fulfilled when the function returns, so the caller has to loop
        until it is finished.
        """

        # We go to sleep if there is already a thread doing what we
        # want to do:

        #  If flushing, we want to send
        #  If waiting for a response to a request, we want to send
        #    (to ensure that the request was sent - we alway recv
        #     when we get to the main loop, but sending is the important
        #     thing here)
        #  If waiting for an event, we want to recv
        #  If just trying to receive anything we can, we want to recv

        if (((flush or request is not None) and self.send_active)
            or ((event or recv) and self.recv_active)):

            # Signal that we are waiting for something.  These locks
            # together with the *_waiting variables are used as
            # semaphores.  When an event or a request response arrives,
            # it will zero the *_waiting and unlock the lock.  The
            # locks will also be unlocked when an active send_and_recv
            # finishes to signal the other waiting threads that one of
            # them has to take over the send_and_recv function.

            # All this makes these locks and variables a part of the
            # send_and_recv control logic, and hence must be modified
            # only when we have the send_recv_lock locked.
            if event:
                wait_lock = self.event_wait_lock
                if not self.event_waiting:
                    self.event_waiting = 1
                    wait_lock.acquire()

            elif request is not None:
                wait_lock = self.request_wait_lock
                if not self.request_waiting:
                    self.request_waiting = 1
                    wait_lock.acquire()

            # Release send_recv, allowing a send_and_recive
            # to terminate or other threads to queue up
            self.send_recv_lock.release()

            # Return immediately if flushing, even if that
            # might mean that not necessarily all requests
            # have been sent.
            if flush or recv:
                return

            # Wait for something to happen, as the wait locks are
            # unlocked either when what we wait for has arrived (not
            # necessarily the exact object we're waiting for, though),
            # or when an active send_and_recv exits.

            # Release it immediately afterwards as we're only using
            # the lock for synchonization.  Since we're not modifying
            # event_waiting or request_waiting here we don't have
            # to lock send_and_recv_lock.  In fact, we can't do that
            # or we trigger a dead-lock.

            wait_lock.acquire()
            wait_lock.release()

            # Return to caller to let it check whether it has
            # got the data it was waiting for
            return


        # There's no thread doing what we need to do.  Find out exactly
        # what to do

        # There must always be some thread recieving data, but it must not
        # necessarily be us

        if not self.recv_active:
            recieving = 1
            self.recv_active = 1
        else:
            recieving = 0

        flush_bytes = None
        sending = 0

        # Loop, recieving and sending data.
        while 1:

            # We might want to start sending data
            if sending or not self.send_active:

                # Turn all requests on request queue into binary form
                # and append them to self.data_send

                self.request_queue_lock.acquire()
                for req, wait in self.request_queue:
                    self.data_send = self.data_send + req._binary
                    if wait:
                        self.sent_requests.append(req)

                del self.request_queue[:]
                self.request_queue_lock.release()

                # If there now is data to send, mark us as senders

                if self.data_send:
                    self.send_active = 1
                    sending = 1
                else:
                    self.send_active = 0
                    sending = 0

            # We've done all setup, so release the lock and start waiting
            # for the network to fire up
            self.send_recv_lock.release()

            # If we're flushing, figure out how many bytes we
            # have to send so that we're not caught in an interminable
            # loop if other threads continuously append requests.
            if flush and flush_bytes is None:
                flush_bytes = self.data_sent_bytes + len(self.data_send)


            try:
                # We're only checking for the socket to be writable
                # if we're the sending thread.  We always check for it
                # to become readable: either we are the recieving thread
                # and should take care of the data, or the recieving thread
                # might finish recieving after having read the data

                if sending:
                    writeset = [self.socket]
                else:
                    writeset = []

                # Timeout immediately if we're only checking for
                # something to read or if we're flushing, otherwise block

                if recv or flush:
                    timeout = 0
                else:
                    timeout = None

                rs, ws, es = select.select([self.socket], writeset, [], timeout)

            # Ignore errors caused by a signal recieved while blocking.
            # All other errors are re-raised.
            except OSError as err:
                if err.errno != errno.EINTR:
                    raise err

                # We must lock send_and_recv before we can loop to
                # the start of the loop

                self.send_recv_lock.acquire()
                continue


            # Socket is ready for sending data, send as much as possible.
            if ws:
                try:
                    i = self.socket.send(self.data_send)
                except OSError as err:
                    self.close_internal('server: %s' % err[1])
                    raise self.socket_error

                self.data_send = self.data_send[i:]
                self.data_sent_bytes = self.data_sent_bytes + i


            # There is data to read
            gotreq = 0
            if rs:

                # We're the recieving thread, parse the data
                if recieving:
                    try:
                        bytes_recv = self.socket.recv(2048)
                    except OSError as err:
                        self.close_internal('server: %s' % err.strerror)
                        raise self.socket_error

                    if not bytes_recv:
                        # Clear up, set a connection closed indicator and raise it
                        self.close_internal('server')
                        raise self.socket_error

                    self.data_recv = self.data_recv + bytes_recv
                    gotreq = self.parse_response(request)

                # Otherwise return, allowing the calling thread to figure
                # out if it has got the data it needs
                else:
                    # We must be a sending thread if we're here, so reset
                    # that indicator.
                    self.send_recv_lock.acquire()
                    self.send_active = 0
                    self.send_recv_lock.release()

                    # And return to the caller
                    return


            # There are three different end of send-recv-loop conditions.
            # However, we don't leave the loop immediately, instead we
            # try to send and recieve any data that might be left.  We
            # do this by giving a timeout of 0 to select to poll
            # the socket.

            # When flushing: all requests have been sent
            if flush and flush_bytes >= self.data_sent_bytes:
                break

            # When waiting for an event: an event has been read
            if event and self.event_queue:
                break

            # When processing a certain request: got its reply
            if request is not None and gotreq:
                break

            # Always break if we just want to recieve as much as possible
            if recv:
                break

            # Else there's may still data which must be sent, or
            # we haven't got the data we waited for.  Lock and loop

            self.send_recv_lock.acquire()


        # We have accomplished the callers request.
        # Record that there are now no active send_and_recv,
        # and wake up all waiting thread

        self.send_recv_lock.acquire()

        if sending:
            self.send_active = 0
        if recieving:
            self.recv_active = 0

        if self.event_waiting:
            self.event_waiting = 0
            self.event_wait_lock.release()

        if self.request_waiting:
            self.request_waiting = 0
            self.request_wait_lock.release()

        self.send_recv_lock.release()


    def parse_response(self, request):
        """Internal method.

        Parse data recieved from server.  If REQUEST is not None
        true is returned if the request with that serial number
        was recieved, otherwise false is returned.

        If REQUEST is -1, we're parsing the server connection setup
        response.
        """

        if request == -1:
            return self.parse_connection_setup()

        # Parse ordinary server response
        gotreq = 0
        while 1:
            # Are we're waiting for additional data for a request response?
            if self.request_length:
                if len(self.data_recv) < self.request_length:
                    return gotreq
                else:
                    gotreq = self.parse_request_response(request) or gotreq


            # Every response is at least 32 bytes long, so don't bother
            # until we have recieved that much
            if len(self.data_recv) < 32:
                return gotreq

            # Check the first byte to find out what kind of response it is
            rtype = _bytes_item(self.data_recv[0])

            # Error resposne
            if rtype == 0:
                gotreq = self.parse_error_response(request) or gotreq

            # Request response
            elif rtype == 1:
                # Set reply length, and loop around to see if
                # we have got the full response
                rlen = int(struct.unpack('=L', self.data_recv[4:8])[0])
                self.request_length = 32 + rlen * 4

            # Else event response
            else:
                self.parse_event_response(rtype)


    def parse_error_response(self, request):
        # Code is second byte
        code = _bytes_item(self.data_recv[1])

        # Fetch error class
        estruct = self.error_classes.get(code, error.XError)

        e = estruct(self, self.data_recv[:32])
        self.data_recv = self.data_recv[32:]

        # print 'recv Error:', e

        req = self.get_waiting_request(e.sequence_number)

        # Error for a request whose response we are waiting for,
        # or which have an error handler.  However, if the error
        # handler indicates that it hasn't taken care of the
        # error, pass it on to the default error handler

        if req and req._set_error(e):

            # If this was a ReplyRequest, unlock any threads waiting
            # for a request to finish

            if isinstance(req, rq.ReplyRequest):
                self.send_recv_lock.acquire()

                if self.request_waiting:
                    self.request_waiting = 0
                    self.request_wait_lock.release()

                self.send_recv_lock.release()

            return request == e.sequence_number

        # Else call the error handler
        else:
            if self.error_handler:
                rq.call_error_handler(self.error_handler, e, None)
            else:
                self.default_error_handler(e)

            return 0


    def default_error_handler(self, err):
        sys.stderr.write('X protocol error:\n%s\n' % err)


    def parse_request_response(self, request):
        req = self.get_waiting_replyrequest()

        # Sequence number is always data[2:4]
        # Do sanity check before trying to parse the data
        sno = struct.unpack('=H', self.data_recv[2:4])[0]
        if sno != req._serial:
            raise RuntimeError("Expected reply for request %s, but got %s.  Can't happen!"
                               % (req._serial, sno))

        req._parse_response(self.data_recv[:self.request_length])
        # print 'recv Request:', req

        self.data_recv = self.data_recv[self.request_length:]
        self.request_length = 0


        # Unlock any response waiting threads

        self.send_recv_lock.acquire()

        if self.request_waiting:
            self.request_waiting = 0
            self.request_wait_lock.release()

        self.send_recv_lock.release()


        return req.sequence_number == request


    def parse_event_response(self, etype):
        # Skip bit 8 at lookup, that is set if this event came from an
        # SendEvent
        estruct = self.event_classes.get(etype & 0x7f, event.AnyEvent)

        e = estruct(display = self, binarydata = self.data_recv[:32])

        self.data_recv = self.data_recv[32:]

        # Drop all requests having an error handler,
        # but which obviously succeded.

        # Decrement it by one, so that we don't remove the request
        # that generated these events, if there is such a one.
        # Bug reported by Ilpo Nyyssönen
        self.get_waiting_request((e.sequence_number - 1) % 65536)

        # print 'recv Event:', e

        # Insert the event into the queue
        self.event_queue_write_lock.acquire()
        self.event_queue.append(e)
        self.event_queue_write_lock.release()

        # Unlock any event waiting threads
        self.send_recv_lock.acquire()

        if self.event_waiting:
            self.event_waiting = 0
            self.event_wait_lock.release()

        self.send_recv_lock.release()


    def get_waiting_request(self, sno):
        if not self.sent_requests:
            return None

        # Normalize sequence numbers, even if they have wrapped.
        # This ensures that
        #   sno <= last_serial
        # and
        #   self.sent_requests[0]._serial <= last_serial

        if self.sent_requests[0]._serial > self.request_serial:
            last_serial = self.request_serial + 65536
            if sno < self.request_serial:
                sno = sno + 65536

        else:
            last_serial = self.request_serial
            if sno > self.request_serial:
                sno = sno - 65536

        # No matching events at all
        if sno < self.sent_requests[0]._serial:
            return None

        # Find last req <= sno
        req = None
        reqpos = len(self.sent_requests)
        adj = 0
        last = 0

        for i in range(0, len(self.sent_requests)):
            rno = self.sent_requests[i]._serial + adj

            # Did serial numbers just wrap around?
            if rno < last:
                adj = 65536
                rno = rno + adj

            last = rno

            if sno == rno:
                req = self.sent_requests[i]
                reqpos = i + 1
                break
            elif sno < rno:
                req = None
                reqpos = i
                break

        # Delete all request such as req <= sno
        del self.sent_requests[:reqpos]

        return req

    def get_waiting_replyrequest(self):
        for i in range(0, len(self.sent_requests)):
            if hasattr(self.sent_requests[i], '_reply'):
                req = self.sent_requests[i]
                del self.sent_requests[:i + 1]
                return req

        # Reply for an unknown request?  No, that can't happen.
        else:
            raise RuntimeError("Request reply to unknown request.  Can't happen!")

    def parse_connection_setup(self):
        """Internal function used to parse connection setup response.
        """

        # Only the ConnectionSetupRequest has been sent so far
        r = self.sent_requests[0]

        while 1:
            # print 'data_send:', repr(self.data_send)
            # print 'data_recv:', repr(self.data_recv)

            if r._data:
                alen = r._data['additional_length'] * 4

                # The full response haven't arrived yet
                if len(self.data_recv) < alen:
                    return 0

                # Connection failed or further authentication is needed.
                # Set reason to the reason string
                if r._data['status'] != 1:
                    r._data['reason'] = self.data_recv[:r._data['reason_length']]

                # Else connection succeeded, parse the reply
                else:
                    x, d = r._success_reply.parse_binary(self.data_recv[:alen],
                                                         self, rawdict = 1)
                    r._data.update(x)

                del self.sent_requests[0]

                self.data_recv = self.data_recv[alen:]

                return 1

            else:
                # The base reply is 8 bytes long
                if len(self.data_recv) < 8:
                    return 0

                r._data, d = r._reply.parse_binary(self.data_recv[:8],
                                                   self, rawdict = 1)
                self.data_recv = self.data_recv[8:]

                # Loop around to see if we have got the additional data
                # already


PixmapFormat = rq.Struct( rq.Card8('depth'),
                          rq.Card8('bits_per_pixel'),
                          rq.Card8('scanline_pad'),
                          rq.Pad(5)
                          )

VisualType = rq.Struct ( rq.Card32('visual_id'),
                         rq.Card8('visual_class'),
                         rq.Card8('bits_per_rgb_value'),
                         rq.Card16('colormap_entries'),
                         rq.Card32('red_mask'),
                         rq.Card32('green_mask'),
                         rq.Card32('blue_mask'),
                         rq.Pad(4)
                         )

Depth = rq.Struct( rq.Card8('depth'),
                   rq.Pad(1),
                   rq.LengthOf('visuals', 2),
                   rq.Pad(4),
                   rq.List('visuals', VisualType)
                   )

Screen = rq.Struct( rq.Window('root'),
                    rq.Colormap('default_colormap'),
                    rq.Card32('white_pixel'),
                    rq.Card32('black_pixel'),
                    rq.Card32('current_input_mask'),
                    rq.Card16('width_in_pixels'),
                    rq.Card16('height_in_pixels'),
                    rq.Card16('width_in_mms'),
                    rq.Card16('height_in_mms'),
                    rq.Card16('min_installed_maps'),
                    rq.Card16('max_installed_maps'),
                    rq.Card32('root_visual'),
                    rq.Card8('backing_store'),
                    rq.Card8('save_unders'),
                    rq.Card8('root_depth'),
                    rq.LengthOf('allowed_depths', 1),
                    rq.List('allowed_depths', Depth)
                    )


class ConnectionSetupRequest(rq.GetAttrData):
    _request = rq.Struct( rq.Set('byte_order', 1, (0x42, 0x6c)),
                          rq.Pad(1),
                          rq.Card16('protocol_major'),
                          rq.Card16('protocol_minor'),
                          rq.LengthOf('auth_prot_name', 2),
                          rq.LengthOf('auth_prot_data', 2),
                          rq.Pad(2),
                          rq.String8('auth_prot_name'),
                          rq.String8('auth_prot_data') )

    _reply = rq.Struct ( rq.Card8('status'),
                         rq.Card8('reason_length'),
                         rq.Card16('protocol_major'),
                         rq.Card16('protocol_minor'),
                         rq.Card16('additional_length') )

    _success_reply = rq.Struct( rq.Card32('release_number'),
                                rq.Card32('resource_id_base'),
                                rq.Card32('resource_id_mask'),
                                rq.Card32('motion_buffer_size'),
                                rq.LengthOf('vendor', 2),
                                rq.Card16('max_request_length'),
                                rq.LengthOf('roots', 1),
                                rq.LengthOf('pixmap_formats', 1),
                                rq.Card8('image_byte_order'),
                                rq.Card8('bitmap_format_bit_order'),
                                rq.Card8('bitmap_format_scanline_unit'),
                                rq.Card8('bitmap_format_scanline_pad'),
                                rq.Card8('min_keycode'),
                                rq.Card8('max_keycode'),
                                rq.Pad(4),
                                rq.String8('vendor'),
                                rq.List('pixmap_formats', PixmapFormat),
                                rq.List('roots', Screen),
                                )


    def __init__(self, display, *args, **keys):
        self._binary = self._request.to_binary(*args, **keys)
        self._data = None

        # Don't bother about locking, since no other threads have
        # access to the display yet

        display.request_queue.append((self, 1))

        # However, we must lock send_and_recv, but we don't have
        # to loop.

        display.send_recv_lock.acquire()
        display.send_and_recv(request = -1)
