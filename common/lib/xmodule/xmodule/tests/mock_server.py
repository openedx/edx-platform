from threading import Thread
import socket
import threading

import SimpleHTTPServer
import SocketServer

class ThreadedRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def handle(self):
        data = self.request.recv(1024)
        cur_thread = threading.current_thread()
        response = "{}: {}".format(cur_thread.name, data)
        self.request.sendall(response)
        return

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

def create_server(host,port):
    """
    Mock a server to be used for the open ended grading tests
    @param host: the hostname ie "localhost" or "127.0.0.1"
    @param port: the integer of the port to open a connection on
    @return: The created server object
    """
    server = ThreadedTCPServer((host,port), ThreadedRequestHandler)

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    return server