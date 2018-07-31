import json


def test_basic_get(app):
    client = app.test_client()
    r = client.get('/')
    assert r.status_code == 200


def test_store(app):
    client = app.test_client()
    data = {"is_cat": "such"}
    headers = {"Content-Type": "application/json"}
    r = client.get('/cat/chairman_meow')
    assert r.status_code == 404
    r = client.put('/cat/chairman_meow', data=json.dumps(data),
                   headers=headers)
    assert r.status_code == 200
    r = client.get('/')
    assert r.status_code == 200
    r = client.get('/cat/chairman_meow')
    assert r.status_code == 200
    assert r.get_json()["is_cat"] == "such"


def test_batch_patch_request(app, raw_req):
    path, method, headers, body = raw_req
    client = app.test_client()
    r = client.open(path, method=method, data=body, headers=headers)
    assert r.status_code == 200
