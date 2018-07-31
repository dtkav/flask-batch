import pytest
import pathlib
from flask_batch import add_batch_route
from flask import Flask, jsonify, request, abort


TEST_PACKET = pathlib.Path(__file__).parent / 'packet'


@pytest.fixture
def app():
    flask_app = Flask(__name__)
    add_batch_route(flask_app)
    state = {}

    @flask_app.route("/cat/<cat>", methods=["GET"])
    def get_cat(cat):
        try:
            got_cat = state[cat]
        except KeyError:
            abort(404)
        return jsonify(got_cat)

    @flask_app.route("/", methods=["GET"])
    def get_home():
        return jsonify(state)

    @flask_app.route("/cat/<cat>", methods=["PUT", "PATCH"])
    def put_home(cat):
        state.update({cat: request.json})
        return jsonify(state.get(cat))

    return flask_app


@pytest.fixture
def raw_req():
    with open(str(TEST_PACKET), 'rb') as f:
        packet = f.read()
    head_raw, body = packet.split(b'\r\n\r\n')
    req_line, headers = head_raw.split(b'\r\n', 1)
    headers = dict([
        header.split(": ", 1)
        for header in headers.decode("ascii").split('\r\n')
    ])
    method, path, _ = req_line.split()
    return path, method, headers, body
