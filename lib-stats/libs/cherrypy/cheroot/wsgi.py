"""
Simplest example on how to use this server::

    from cheroot import wsgi

    def my_crazy_app(environ, start_response):
        status = '200 OK'
        response_headers = [('Content-type','text/plain')]
        start_response(status, response_headers)
        return ['Hello world!']

    addr = '0.0.0.0', 8070
    server = wsgi.Server(addr, my_crazy_app)
    server.start()

The Cheroot WSGI server can serve as many WSGI applications
as you want in one instance by using a PathInfoDispatcher::

    path_map = {
        '/': my_crazy_app,
        '/blog': my_blog_app,
    }
    d = wsgi.PathInfoDispatcher(path_map)
    server = wsgi.Server(addr, d)
"""

import sys

import six
from six.moves import filter

from . import server
from .workers import threadpool
from ._compat import ntob, bton


class Server(server.HTTPServer):

    """A subclass of HTTPServer which calls a WSGI application."""

    wsgi_version = (1, 0)
    """The version of WSGI to produce."""

    def __init__(self, bind_addr, wsgi_app, numthreads=10, server_name=None,
                 max=-1, request_queue_size=5, timeout=10, shutdown_timeout=5,
                 accepted_queue_size=-1, accepted_queue_timeout=10):
        super(Server, self).__init__(
            bind_addr,
            gateway=wsgi_gateways[self.wsgi_version],
            server_name=server_name,
        )
        self.wsgi_app = wsgi_app
        self.request_queue_size = request_queue_size
        self.timeout = timeout
        self.shutdown_timeout = shutdown_timeout
        self.requests = threadpool.ThreadPool(self, min=numthreads or 1, max=max,
            accepted_queue_size=accepted_queue_size,
            accepted_queue_timeout=accepted_queue_timeout)

    def _get_numthreads(self):
        return self.requests.min

    def _set_numthreads(self, value):
        self.requests.min = value
    numthreads = property(_get_numthreads, _set_numthreads)


class Gateway(server.Gateway):

    """A base class to interface HTTPServer with WSGI."""

    def __init__(self, req):
        self.req = req
        self.started_response = False
        self.env = self.get_environ()
        self.remaining_bytes_out = None

    def get_environ(self):
        """Return a new environ dict targeting the given wsgi.version"""
        raise NotImplemented

    def respond(self):
        """Process the current request."""

        """
        From PEP 333:

            The start_response callable must not actually transmit
            the response headers. Instead, it must store them for the
            server or gateway to transmit only after the first
            iteration of the application return value that yields
            a NON-EMPTY string, or upon the application's first
            invocation of the write() callable.
        """

        response = self.req.server.wsgi_app(self.env, self.start_response)
        try:
            for chunk in filter(None, response):
                if not isinstance(chunk, six.binary_type):
                    raise ValueError('WSGI Applications must yield bytes')
                self.write(chunk)
        finally:
            if hasattr(response, 'close'):
                response.close()

    def start_response(self, status, headers, exc_info=None):
        """
        WSGI callable to begin the HTTP response.
        """
        # "The application may call start_response more than once,
        # if and only if the exc_info argument is provided."
        if self.started_response and not exc_info:
            raise AssertionError('WSGI start_response called a second '
                                 'time with no exc_info.')
        self.started_response = True

        # "if exc_info is provided, and the HTTP headers have already been
        # sent, start_response must raise an error, and should raise the
        # exc_info tuple."
        if self.req.sent_headers:
            try:
                six.reraise(*exc_info)
            finally:
                exc_info = None

        self.req.status = self._encode_status(status)

        for k, v in headers:
            if not isinstance(k, str):
                raise TypeError(
                    'WSGI response header key %r is not of type str.' % k)
            if not isinstance(v, str):
                raise TypeError(
                    'WSGI response header value %r is not of type str.' % v)
            if k.lower() == 'content-length':
                self.remaining_bytes_out = int(v)
            out_header = ntob(k), ntob(v)
            self.req.outheaders.append(out_header)

        return self.write

    @staticmethod
    def _encode_status(status):
        """
        According to PEP 3333, when using Python 3, the response status
        and headers must be bytes masquerading as unicode; that is, they
        must be of type "str" but are restricted to code points in the
        "latin-1" set.
        """
        if six.PY2:
            return status
        if not isinstance(status, str):
            raise TypeError('WSGI response status is not of type str.')
        return status.encode('ISO-8859-1')

    def write(self, chunk):
        """WSGI callable to write unbuffered data to the client.

        This method is also used internally by start_response (to write
        data from the iterable returned by the WSGI application).
        """
        if not self.started_response:
            raise AssertionError('WSGI write called before start_response.')

        chunklen = len(chunk)
        rbo = self.remaining_bytes_out
        if rbo is not None and chunklen > rbo:
            if not self.req.sent_headers:
                # Whew. We can send a 500 to the client.
                self.req.simple_response(
                    '500 Internal Server Error',
                    'The requested resource returned more bytes than the '
                    'declared Content-Length.')
            else:
                # Dang. We have probably already sent data. Truncate the chunk
                # to fit (so the client doesn't hang) and raise an error later.
                chunk = chunk[:rbo]

        if not self.req.sent_headers:
            self.req.sent_headers = True
            self.req.send_headers()

        self.req.write(chunk)

        if rbo is not None:
            rbo -= chunklen
            if rbo < 0:
                raise ValueError(
                    'Response body exceeds the declared Content-Length.')


class Gateway_10(Gateway):

    """A Gateway class to interface HTTPServer with WSGI 1.0.x."""

    def get_environ(self):
        """Return a new environ dict targeting the given wsgi.version"""
        req = self.req
        env = {
            # set a non-standard environ entry so the WSGI app can know what
            # the *real* server protocol is (and what features to support).
            # See http://www.faqs.org/rfcs/rfc2145.html.
            'ACTUAL_SERVER_PROTOCOL': req.server.protocol,
            'PATH_INFO': bton(req.path),
            'QUERY_STRING': bton(req.qs),
            'REMOTE_ADDR': req.conn.remote_addr or '',
            'REMOTE_PORT': str(req.conn.remote_port or ''),
            'REQUEST_METHOD': bton(req.method),
            'REQUEST_URI': bton(req.uri),
            'SCRIPT_NAME': '',
            'SERVER_NAME': req.server.server_name,
            # Bah. "SERVER_PROTOCOL" is actually the REQUEST protocol.
            'SERVER_PROTOCOL': bton(req.request_protocol),
            'SERVER_SOFTWARE': req.server.software,
            'wsgi.errors': sys.stderr,
            'wsgi.input': req.rfile,
            'wsgi.multiprocess': False,
            'wsgi.multithread': True,
            'wsgi.run_once': False,
            'wsgi.url_scheme': bton(req.scheme),
            'wsgi.version': (1, 0),
        }

        if isinstance(req.server.bind_addr, six.string_types):
            # AF_UNIX. This isn't really allowed by WSGI, which doesn't
            # address unix domain sockets. But it's better than nothing.
            env['SERVER_PORT'] = ''
        else:
            env['SERVER_PORT'] = str(req.server.bind_addr[1])

        # Request headers
        env.update(
            ('HTTP_' + bton(k).upper().replace('-', '_'), bton(v))
            for k, v in req.inheaders.items()
        )

        # CONTENT_TYPE/CONTENT_LENGTH
        ct = env.pop('HTTP_CONTENT_TYPE', None)
        if ct is not None:
            env['CONTENT_TYPE'] = ct
        cl = env.pop('HTTP_CONTENT_LENGTH', None)
        if cl is not None:
            env['CONTENT_LENGTH'] = cl

        if req.conn.ssl_env:
            env.update(req.conn.ssl_env)

        return env


class Gateway_u0(Gateway_10):

    """A Gateway class to interface HTTPServer with WSGI u.0.

    WSGI u.0 is an experimental protocol, which uses unicode for keys
    and values in both Python 2 and Python 3.
    """

    def get_environ(self):
        """Return a new environ dict targeting the given wsgi.version"""
        req = self.req
        env_10 = super(Gateway_u0, self).get_environ(self)
        env = dict(map(self._decode_key, env_10.items()))
        env[six.u('wsgi.version')] = ('u', 0)

        # Request-URI
        enc = env.setdefault(six.u('wsgi.url_encoding'), six.u('utf-8'))
        try:
            env['PATH_INFO'] = req.path.decode(enc)
            env['QUERY_STRING'] = req.qs.decode(enc)
        except UnicodeDecodeError:
            # Fall back to latin 1 so apps can transcode if needed.
            env['wsgi.url_encoding'] = 'ISO-8859-1'
            env['PATH_INFO'] = env_10['PATH_INFO']
            env['QUERY_STRING'] = env_10['QUERY_STRING']

        env.update(map(self._decode_value, env.items()))

        return env

    @staticmethod
    def _decode_key(item):
        k, v = item
        if six.PY2:
            k = k.decode('ISO-8859-1')
        return k, v

    @staticmethod
    def _decode_value(item):
        k, v = item
        skip_keys = 'REQUEST_URI', 'wsgi.input'
        if six.PY3 or not isinstance(v, bytes) or k in skip_keys:
            return k, v
        return k, v.decode('ISO-8859-1')


wsgi_gateways = {
    (1, 0): Gateway_10,
    ('u', 0): Gateway_u0,
}


class PathInfoDispatcher(object):

    """A WSGI dispatcher for dispatch based on the PATH_INFO.

    apps: a dict or list of (path_prefix, app) pairs.
    """

    def __init__(self, apps):
        try:
            apps = list(apps.items())
        except AttributeError:
            pass

        # Sort the apps by len(path), descending
        by_path_len = lambda app: len(app[0])
        apps.sort(key=by_path_len, reverse=True)

        # The path_prefix strings must start, but not end, with a slash.
        # Use "" instead of "/".
        self.apps = [(p.rstrip('/'), a) for p, a in apps]

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'] or '/'
        for p, app in self.apps:
            # The apps list should be sorted by length, descending.
            if path.startswith(p + '/') or path == p:
                environ = environ.copy()
                environ['SCRIPT_NAME'] = environ['SCRIPT_NAME'] + p
                environ['PATH_INFO'] = path[len(p):]
                return app(environ, start_response)

        start_response('404 Not Found', [('Content-Type', 'text/plain'),
                                         ('Content-Length', '0')])
        return ['']


# compatibility aliases
globals().update(
    WSGIServer=Server,
    WSGIGateway=Gateway,
    WSGIGateway_u0=Gateway_u0,
    WSGIGateway_10=Gateway_10,
    WSGIPathInfoDispatcher=PathInfoDispatcher,
)
