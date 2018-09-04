Flask-Batch
===========

|Travis CI build status| |GitHub license| |Latest Version|

*Batch multiple requests at the http layer.* Flask-Batch is inpsired by
`how google cloud storage does
batching <https://cloud.google.com/storage/docs/json_api/v1/how-tos/batch>`__.

It adds a ``/batch`` route to your API which can execute batched HTTP
requests against your API server side. The client wraps several requests
in a single request using the ``multipart/mixed`` content type.


Installation
============

.. code:: bash

    pip install Flask-Batch

    # to include the dependencies for the batching client
    pip install Flask-Batch[client]


Getting Started
===============

Server
------

.. code:: python

    from flask import Flask
    from flask_batch import add_batch_route

    app = Flask(__name__)
    add_batch_route(app)

    # that's it!

Client
------

The client wraps a requests session.

.. code:: python

    from flask_batch.client import Batching
    import json

    alice_data = bob_data = {"example": "json"}

    with Batching("http://localhost:5000/batch") as s:
        alice = s.patch("/people/alice/", json=alice_data)
        bob = s.patch("/people/bob/", json=bob_data)

    alice         # <Response [200]>
    alice.json()  # {"response": "json"}

Why Batch?
==========

Often the round-trip-time from a client to a server is high. Batching
requests reduces the penalty of a high RTT, without the added complexity
of request parallelization.

.. figure:: sequence-diagram.svg
   :alt: 

Batching Done Right
===================

Often API designers will create custom batch endpoints for specific
operations. Creating custom API endpoints for performing bulk operations
usually end up being clunky. Each one ends up unique. This means more
code to maintain, and more bugs.

It can be difficult to reason about bulk json API endpoints. For
example, what happens on error? Does the bulk operation fail? continue?
roll back?

Batching at the HTTP layer results in clear and expected behaviors that
are easy to reason about. HTTP batching simply behaves the same way as
all of the individual requests that are sent in the batch.

Status
======

This project is in ``alpha``. I'm hoping to eventually get it approved
as a flask extension.

.. |Travis CI build status| image:: https://api.travis-ci.org/dtkav/flask-batch.svg?branch=master
   :target: https://travis-ci.org/dtkav/flask-batch/
.. |GitHub license| image:: https://img.shields.io/github/license/dtkav/flask-batch.svg
   :target: https://github.com/dtkav/flask-batch/blob/master/LICENSE
.. |Latest Version| image:: https://img.shields.io/pypi/v/flask-batch.svg
   :target: https://pypi.python.org/pypi/flask-batch
