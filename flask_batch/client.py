#!/usr/bin/env python

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc

import requests
import six

from email.mime.multipart import MIMEMultipart
from .flask_batch import parse_multi, MIMEApplicationHTTPRequest
from .polyfill import HTTPGenerator
from requests.models import Response
from requests.compat import urlparse, urlunparse
from requests import Session


class _FutureDict(collections_abc.Mapping):
    err = ValueError("Complete batching request before accessing result")

    def __init__(self, future, *args, **kwargs):
        self._future = future  # somehow ensure same request/response pair
        super(_FutureDict, self).__init__(*args, **kwargs)

    def __getitem__(self):
        raise self.err

    def __iter__(self):
        raise self.err

    def __len__(self):
        raise self.err


class _FutureResponse(requests.Response):
    def __init__(self, future_dict):
        super(_FutureResponse, self).__init__()
        self._future_dict = future_dict
        self.status_code = 204

    def json(self):
        return self._future_dict

    @property
    def content(self):
        return self._future_dict


class Batching(Session):

    def __init__(self, batch_url):
        self._futures = []
        self._requests = []
        self._batch_url = batch_url
        self._batch_url_parsed = urlparse(batch_url)
        super(Batching, self).__init__()

    def _prepend_host(self, path):
        scheme = self._batch_url_parsed.scheme
        netloc = self._batch_url_parsed.netloc
        parsed = urlparse(path)
        return urlunparse((scheme, netloc, parsed.path, parsed.params,
                           parsed.query, parsed.fragment))

    def prepare_request(self, request):
        # enforce same scheme, netloc as batch_url
        request.url = self._prepend_host(request.url)
        return super(Batching, self).prepare_request(request)

    def send(self, request, **kwargs):
        fd = _FutureDict(request)
        fr = _FutureResponse(fd)
        self._futures.append(fr)
        self._requests.append(request)
        return fr

    def __exit__(self, *args):
        self.finalize()
        self.close()

    def before_request(self):
        pass

    def after_response(self):
        pass

    def finalize(self):
        headers, data = prepare_batch_request(self._requests)
        self._request_headers = headers
        self._request_data = data
        self.before_request()
        resp = requests.post(self._batch_url, data=data, headers=headers)
        self._response = resp
        self.after_response()
        resp.raise_for_status()
        decoded = decode_batch_response(resp)
        for f, r in zip(self._futures, decoded):
            f._future_dict = r.json()
            f.status_code = r.status_code


def prepare_batch_request(requests):
    if len(requests) == 0:
        raise ValueError("No deferred requests")

    batch = MIMEMultipart()

    for request in requests:
        method = request.method
        uri = request.url
        headers = request.headers
        body = request.body
        subrequest = MIMEApplicationHTTPRequest(method, uri, headers, body)
        batch.attach(subrequest)

    buf = six.StringIO()
    generator = HTTPGenerator(buf, False, 0)
    generator.flatten(batch)
    payload = buf.getvalue()

    # Strip off redundant header text
    _, body = payload.split('\r\n\r\n', 1)
    return dict(batch._headers), body


def make_response(content_id, data):
    header, content = data.split(b"\r\n\r\n", 1)
    response = Response()
    response._content, _ = content.rsplit(b'\r\n', 1)
    status, headers = header.split(b'\r\n', 1)
    _, code, reason = status.split(b' ', 2)
    response.code = reason
    response.error_type = reason
    response.status_code = int(code)
    response.content_id = content_id
    return response


def decode_batch_response(resp):
    content_type = resp.headers["Content-Type"]
    messages = parse_multi(content_type, resp.content)
    return [make_response(content_id, m) for content_id, m in messages]
