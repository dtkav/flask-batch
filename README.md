# Flask-Batch (alpha)
_Batch multiple requests at the http layer._
Flask-Batch is inpsired by [how google cloud storage does batching](https://cloud.google.com/storage/docs/json_api/v1/how-tos/batch).

It adds a `/batch` route to your API which can execute batched HTTP requests against your
API server side. The client wraps several requests in a single request using the `multipart/mixed` content type.

![](sequence-diagram.svg)

# Why Batch?
Often the round-trip-time from a client to a server is high.
Batching requests reduces the penalty of a high RTT, without the added complexity of request parallelization.

# Batching Done Right
Often API designers will create custom batch endpoints for specific operations.
Creating custom API endpoints for performing bulk operations usually end up
being clunky. Each one ends up unique. This means more code to maintain, and more bugs.

It can be difficult to reason about bulk json API endpoints.
For example, what happens on error? Does the bulk operation fail? continue?
roll back?

Batching at the HTTP layer results in clear and expected behaviors that are easy
to reason about. HTTP batching simply behaves the same way as all of the individual requests that are sent in the batch.

# Status
This project is in `alpha`. I'm hoping to eventually get it approved as a flask extension.
