from flask import Flask, request, jsonify
from flask_batch import add_batch_route

app = Flask(__name__)
app.url_map.strict_slashes = False
add_batch_route(app)

state = {"alice": "hello"}

HEADERS = {"Content-Type": "application/json"}


@app.route("/cat/<cat>", methods=["GET"])
def get_cat(cat):
    return jsonify(state.get(cat))


@app.route("/", methods=["GET"])
def get_home():
    return jsonify(state)


@app.route("/cat/<cat>", methods=["PATCH"])
def patch_cat(cat):
    state.update({cat: request.json})
    return jsonify(state.get(cat))


@app.route("/cat/<cat>", methods=["PUT", "POST"])
def put_home(cat):
    state.update({cat: request.json})
    return jsonify(state.get(cat))


if __name__ == "__main__":
    app.run(debug=True)
