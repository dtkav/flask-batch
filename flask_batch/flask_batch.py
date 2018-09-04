import werkzeug_raw
import json
import six
from .polyfill import HTTPGenerator

from email.encoders import encode_noop
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from flask import request, abort, current_app

HEADERS = {"Content-Type": "application/json"}
CRLF = '\r\n'


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
    headers, body = bb.split(b'\r\n\r\n', 1)
    headers = headers.replace(b"\r", b"").split(b"\n")
    content_id = None
    for h in headers:
        if h.lower().startswith(b"content-id"):
            _, content_id = h.split(b":")
            content_id = content_id.strip()

    return content_id, body


def unquote(s):
    s = s[1:] if s.startswith(b'"') else s
    s = s[:-1] if s.endswith(b'"') else s
    return s


def parse_multi(content_type, multi):
    _, boundary_raw = content_type.split("=", 1)
    boundary = b"--" + unquote(boundary_raw.encode("ascii"))
    payloads = multi.split(boundary)[1:-1]
    return [strip_headers(payload) for payload in payloads]


def prepare_batch_response(responses):
    if len(responses) == 0:
        raise ValueError("Provide at least one response")

    batch = MIMEMultipart()

    for status, headers, body in responses:
        subrequest = MIMEApplicationHTTPResponse(
            status, headers, body)
        batch.attach(subrequest)

    buf = six.StringIO()
    generator = HTTPGenerator(buf, False, 0)
    generator.flatten(batch)
    payload = buf.getvalue()

    # Strip off redundant header text
    _, body = payload.split('\r\n\r\n', 1)
    return dict(batch._headers), body


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

    multi = parse_multi(content_type, data)
    for content_id, payload in multi:
        environ = werkzeug_raw.environ(payload)

        # ensure we only issue requests against the same host
        # as the original request
        environ.update({"SERVER_NAME": request.environ["SERVER_NAME"]})
        environ.update({"SERVER_PORT": request.environ["SERVER_PORT"]})
        environ.update({"HTTP_HOST": request.environ["HTTP_HOST"]})

        # if we don't have content-length
        environ.update({"wsgi.input_terminated": 1})

        with app.request_context(environ):
            try:
                rv = app.preprocess_request()
                if rv is None:
                    rv = app.dispatch_request()

            except Exception as e:
                rv = app.handle_user_exception(e)

            response = app.make_response(rv)
            response = app.process_response(response)
            if content_id:
                response.headers.extend({"Content-ID": content_id})

        responses.append((
            response.status,
            response.headers,
            response.json
        ))
        headers, body = prepare_batch_response(responses)

    if body is None:
        abort(500)

    return body, 200, headers
