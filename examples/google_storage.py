#!/usr/bin/env ipython
import os
import requests
from google.oauth2.service_account import Credentials
from flask_batch.client import prepare_batch_request, decode_batch_response


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


scopes = ('https://www.googleapis.com/auth/devstorage.full_control',
          'https://www.googleapis.com/auth/devstorage.read_only',
          'https://www.googleapis.com/auth/devstorage.read_write')


creds = Credentials.from_service_account_file(CREDS_FILE_PATH)
creds = creds.with_scopes(scopes)

url = "https://www.googleapis.com/batch/storage/v1/"
headers = {"Content-Type": "application/json"}

to_batch = [
    (
        "PATCH",
        "/storage/v1/b/flask_batch/o/favi.ico",
        headers,
        {"metadata": {"type": "tabby"}}
    ),
    (
        "PATCH",
        "/storage/v1/b/flask_batch/o/favi.ico",
        headers,
        {"metadata": {"type": "tuxedo"}}
    )
]

headers, data = prepare_batch_request(to_batch)

creds.before_request(gRequest(), "POST", url, headers)
resp = requests.post(url, data=data, headers=headers)
responses = decode_batch_response(resp)

print(responses)
