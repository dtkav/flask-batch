#!/usr/bin/env python

import requests
import io

from email.generator import Generator
from email.mime.multipart import MIMEMultipart
from flask_batch.flask_batch import parse_multi, MIMEApplicationHTTPRequest
from requests.models import Response
from requests import Session


# ideal usage is something like
# with Batching():
#     res = []
#     for a in many:
#         res.append(requests.post(a.url, headers=a.headers, data=a.data))
#
# res = [...]

class Batching(Session):

    def __init__(self):
        self._batched_requests = []
        super(Batching, self).__init__()

    def send(self, request, **kwargs):
        self._batched_requests.append(request)
        return  # something

    def __exit__(self, *args):
        self.finalize()
        self.close()

    def finalize(self):
        headers, body = prepare_batch_request(self._batched_requests)
        import ipdb
        ipdb.set_trace()
        # actually send request
        # match responses with responses


def prepare_batch_request(requests):
    if len(requests) == 0:
        raise ValueError("No deferred requests")

    batch = MIMEMultipart()

    for method, uri, headers, body in requests:
        subrequest = MIMEApplicationHTTPRequest(method, uri, headers, body)
        batch.attach(subrequest)

    buf = io.StringIO()
    generator = Generator(buf, False, 0)
    generator.flatten(batch)
    payload = buf.getvalue()

    # Strip off redundant header text
    _, body = payload.split('\n\n', 1)
    return dict(batch._headers), body


def make_response(data):
    wrap, header, content = data.split(b"\r\n\r\n")
    response = Response()
    response._content, _ = content.split(b'\r\n', 1)
    status, headers = header.split(b'\r\n', 1)
    _, code, reason = status.split()
    response.code = reason
    response.error_type = reason
    response.status_code = int(code)
    return response


def decode_batch_response(resp):
    content_type = resp.headers["Content-Type"]
    datas = parse_multi(content_type, resp.content)
    responses = [make_response(d).json() for d in datas]
    return responses


def do():
    headers = {}
    requests = [
        ("PATCH", "/cat/alice", headers, {"metadata": {"type": "tabby"}}),
        ("PATCH", "/cat/bob", headers, {"metadata": {"type": "tuxedo"}})
    ]
    return prepare_batch_request(requests)


if __name__ == "__main__":
    headers, body = do()
    resp = requests.post(
        "http://127.0.0.1:5000/batch",
        headers=headers,
        data=body
    )
    content_type = resp.headers["Content-Type"]
    datas = parse_multi(content_type, resp.content)
    responses = [make_response(d).json() for d in datas[:-1]]
    print(responses)
