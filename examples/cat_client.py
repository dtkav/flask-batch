#!/usr/bin/env python
from flask_batch.client import Batching
from pprint import pprint
import json

headers = {"Content-Type": "application/json"}

responses = []
with Batching("http://localhost:5000/batch") as b:
    responses.append(
        b.patch(
            "http://localhost:5000/cat/alice",
            data=json.dumps({"name": "fance"}),
            headers=headers
        )
    )
    responses.append(
        b.patch(
            "http://localhost:5000/cat/bob",
            data=json.dumps({"name": "duhbob"}),
            headers=headers
        )
    )

for response in responses:
    pprint(response)
    pprint(response.json())
