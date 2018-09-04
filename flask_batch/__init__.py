from .flask_batch import batch

__author__ = 'Daniel Grossmann-Kavanagh'
__email__ = 'me@danielgk.com'
__url__ = 'https://github.com/dtkav/flask-batch'
__version__ = '0.0.2'
__license__ = 'MIT'


def add_batch_route(app, route='/batch', name='batch'):
    return app.add_url_rule(route, name, batch, methods=["POST"])
