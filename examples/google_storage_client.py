#!/usr/bin/env ipython
import os
import requests
import json
from google.oauth2.service_account import Credentials
from flask_batch.client import Batching

CREDS_FILE_PATH = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]


class gRequest(object):
    """ wrap requests with google's expected api
    """

    def __call__(*args, **kwargs):
        kwargs["data"] = kwargs["body"]
        del kwargs["body"]
        resp = requests.request(**kwargs)
        resp.data = resp.content
        resp.status = resp.status_code
        return resp


class GBatching(Batching):

    def __init__(self, creds, *args, **kwargs):
        self._creds = creds
        super(GBatching, self).__init__(*args, **kwargs)

    def before_request(self):
        self._creds.before_request(
            gRequest(),
            "POST",
            self._batch_url,
            self._request_headers
        )


scopes = ('https://www.googleapis.com/auth/devstorage.full_control',
          'https://www.googleapis.com/auth/devstorage.read_only',
          'https://www.googleapis.com/auth/devstorage.read_write')

creds = Credentials.from_service_account_file(CREDS_FILE_PATH)
creds = creds.with_scopes(scopes)

batch_url = "https://www.googleapis.com/batch/storage/v1/"

responses = []
with GBatching(creds, batch_url) as s:

    json_headers = {"Content-Type": "application/json"}
    responses.append(s.patch(
        "https://www.googleapis.com/storage/v1/b/flask_batch/o/favi.ico",
        headers=json_headers,
        data=json.dumps({"metadata": {"type": "tabby"}})
    ))
    responses.append(s.patch(
        "https://www.googleapis.com/storage/v1/b/flask_batch/o/favi.ico",
        headers=json_headers,
        data=json.dumps({"metadata": {"type": "tuxedo"}})
    ))

print([r.json() for r in responses])
