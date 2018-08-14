import six

CRLF = '\r\n'
NL = CRLF

if six.PY2:
    from .py2 import HTTPGenerator  # noqa

else:
    from email.generator import Generator
    from email._policybase import Compat32

    class BatchPolicy(Compat32):
        linesep = CRLF

    class HTTPGenerator(Generator, object):

        def __init__(self, *args, **kwargs):
            kwargs.setdefault("policy", BatchPolicy())
            super(HTTPGenerator, self).__init__(*args, **kwargs)
