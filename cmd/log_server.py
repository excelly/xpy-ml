import sys
import os
from getopt import getopt

import pickle
import logging
import logging.config
import logging.handlers
import SocketServer
import struct

import ex.util as eu

def usage():
    print('''setup a server that listens to log messages.
python log_server.py

--port=server port
--help: show this message

other options can be adjusted in ex/logging_server.conf
''')
    sys.exit(1)

class LogRecordStreamHandler(SocketServer.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4: break
            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = pickle.loads(chunk)
            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)

    def handleLogRecord(self, record):
        logger = logging.getLogger()
        logger.handle(record)

class LogRecordSocketReceiver(SocketServer.ThreadingTCPServer):
    """simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = 1

    def __init__(self, port, handler=LogRecordStreamHandler):
        SocketServer.ThreadingTCPServer.__init__(
            self, ('localhost', port), handler)
        self.abort = 0
        self.timeout = 1

    def serve_until_stopped(self):
        import select
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [], self.timeout)
            if rd: self.handle_request()
            abort = self.abort

def main():
    try:
        opts=dict(getopt(sys.argv[1:], '', ['port=','help'])[0])
    except GetoptError:
        usage()

    if opts.has_key('--help'): usage()
    port=opts.get('--port', logging.handlers.DEFAULT_TCP_LOGGING_PORT)

    logging.config.fileConfig(eu.exBase() + "/logging_server.conf")

    tcpserver = LogRecordSocketReceiver(port)
    print("Starting logging server...")
    tcpserver.serve_until_stopped()

if __name__ == "__main__":
    main()
