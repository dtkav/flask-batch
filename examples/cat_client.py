#!/usr/bin/env python
from flask_batch.client import Batching
from pprint import pprint

responses = []
with Batching("http://localhost:5000/batch") as b:
    alice = b.patch("/cat/alice", json={"name": "fance"})
    bob = b.patch("/cat/bob", json={"name": "duhbob"})

pprint(alice)
pprint(alice.json())

pprint(bob)
pprint(bob.json())
