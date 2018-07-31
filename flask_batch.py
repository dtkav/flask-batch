import dtkav_werkzeug_raw as werkzeug_raw
import json
import six

from email.encoders import encode_noop
from email.generator import Generator
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from flask import request, abort, current_app

HEADERS = {"Content-Type": "application/json"}
CRLF = '\r\n'


__author__ = 'Daniel Grossmann-Kavanagh'
__email__ = 'me@danielgk.com'
__url__ = 'https://github.com/dtkav/flask-batch'
__version__ = '0.0.0'
__license__ = 'MIT'


class MIMEApplicationHTTPRequest(MIMEApplication, object):

    def __init__(self, method, path, headers, body):
        if isinstance(body, dict):
            body = json.dumps(body)
            headers['Content-Type'] = 'application/json'
            headers['Content-Length'] = len(body)
        body = body or ''
        request_line = '{method} {path} HTTP/1.1'
        lines = [request_line.format(method=method, path=path)]
        lines += ['{k}: {v}'.format(k=k, v=v) for k, v in headers.items()]
        lines.append('')
        lines.append(body)
        request = CRLF.join(lines)
        super(MIMEApplicationHTTPRequest, self).__init__(
            request, 'http', encode_noop
        )


class MIMEApplicationHTTPResponse(MIMEApplication, object):

    def __init__(self, status, headers, body):
        if isinstance(body, dict):
            body = json.dumps(body)
            headers['Content-Type'] = 'application/json'
            headers['Content-Length'] = len(body)
        body = body or ''
        response_line = 'HTTP/1.1 {status}'
        lines = [response_line.format(status=status)]
        lines += ['{k}: {v}'.format(k=k, v=v) for k, v in headers.items()]
        lines.append('')
        lines.append(body)
        response = CRLF.join(lines)
        super(MIMEApplicationHTTPResponse, self).__init__(
            response, 'http', encode_noop
        )


def strip_headers(bb):
    return bb.split(b'\n\n', 1)[1]


def parse_multi(content_type, data):
    boundary = content_type.split("=", 1)[1][1:-1].encode("ascii")
    datas = data.split(boundary)[1:]
    for d in datas[:-1]:
        try:
            d = strip_headers(d)
        except IndexError:
            continue
    return datas


def prepare_batch_response(responses):
    if len(responses) == 0:
        raise ValueError("Provide at least one response")

    batch = MIMEMultipart()

    for status, headers, body in responses:
        subrequest = MIMEApplicationHTTPResponse(
            status, headers, body)
        batch.attach(subrequest)

    buf = six.StringIO()
    generator = Generator(buf, False, 0)
    generator.flatten(batch)
    payload = buf.getvalue()

    # Strip off redundant header text
    _, body = payload.split('\n\n', 1)
    return dict(batch._headers), body


def add_batch_route(app, route='/batch', name='batch'):
    return app.add_url_rule(route, name, batch, methods=["POST"])


def batch():
    """
    Execute multiple requests, submitted as a batch.
    """
    responses = []
    app = current_app
    data = request.stream.read()
    body = None
    content_type = request.environ["CONTENT_TYPE"]
    if not content_type.startswith("multipart/mixed"):
        abort(400)

    datas = parse_multi(content_type, data)
    for d in datas:
        try:
            d = strip_headers(d)
        except IndexError:
            continue
        environ = werkzeug_raw.environ(d)
        environ.update({"SERVER_NAME": request.environ["SERVER_NAME"]})
        environ.update({"SERVER_PORT": request.environ["SERVER_PORT"]})

        with app.request_context(environ):
            try:
                rv = app.preprocess_request()
                if rv is None:
                    rv = app.dispatch_request()

            except Exception as e:
                rv = app.handle_user_exception(e)

            response = app.make_response(rv)
            response = app.process_response(response)

        responses.append((
            response.status,
            response.headers,
            response.json
        ))
        headers, body = prepare_batch_response(responses)

    if body is None:
        abort(500)

    return body, 200, headers


#class BatchRoute(object):
#
#    def __init__(self, app=None):
#        self.app = app
#        if app is not None:
#            self.init_app(app)
#
#    def init_app(self, app):
#        app.add_url_rule('/batch', 'batch', self.batch, methods=["POST"])
#
#    def batch(self):
#        """
#        Execute multiple requests, submitted as a batch.
#        """
#        responses = []
#        app = self.app
#        data = request.stream.read()
#        body = None
#        content_type = request.environ["CONTENT_TYPE"]
#        if not content_type.startswith("multipart/mixed"):
#            abort(400)
#
#        datas = parse_multi(content_type, data)
#        for d in datas:
#            try:
#                d = strip_headers(d)
#            except IndexError:
#                continue
#            environ = werkzeug_raw.environ(d)
#            environ.update({"SERVER_NAME": request.environ["SERVER_NAME"]})
#            environ.update({"SERVER_PORT": request.environ["SERVER_PORT"]})
#
#            with app.request_context(environ):
#                try:
#                    rv = app.preprocess_request()
#                    if rv is None:
#                        rv = app.dispatch_request()
#
#                except Exception as e:
#                    rv = app.handle_user_exception(e)
#
#                response = app.make_response(rv)
#                response = app.process_response(response)
#
#            responses.append((
#                response.status,
#                response.headers,
#                response.json
#            ))
#            headers, body = prepare_batch_response(responses)
#
#        if body is None:
#            abort(500)
#
#        return body, 200, headers
