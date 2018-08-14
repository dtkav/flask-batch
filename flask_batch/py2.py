# The following code is from the python standard lib
# Copyright (C) 2001-2010 Python Software Foundation
#
# It has been slightly modified to support HTTP
# compliant newline characters (\r\n) in python 2.7

import six

from email.header import Header as OldHeader
from email.header import _max_append
from email.generator import Generator
from email.generator import _make_boundary, fcre, _is8bitstring

from StringIO import StringIO

CRLF = '\r\n'
NL = CRLF


class Header(OldHeader):

    def _encode_chunks(self, newchunks, maxlinelen):
        # MIME-encode a header with many different charsets and/or encodings.
        #
        # Given a list of pairs (string, charset), return a MIME-encoded
        # string suitable for use in a header field.  Each pair may have
        # different charsets and/or encodings, and the resulting header will
        # accurately reflect each setting.
        #
        # Each encoding can be email.utils.QP (quoted-printable, for
        # ASCII-like character sets like iso-8859-1), email.utils.BASE64
        # (Base64, for non-ASCII like character sets like KOI8-R and
        # iso-2022-jp), or None (no encoding).
        #
        # Each pair will be represented on a separate line; the resulting
        # string will be in the format:
        #
        # =?charset1?q?Mar=EDa_Gonz=E1lez_Alonso?=\n
        #  =?charset2?b?SvxyZ2VuIEL2aW5n?="
        chunks = []
        for header, charset in newchunks:
            if not header:
                continue
            if charset is None or charset.header_encoding is None:
                s = header
            else:
                s = charset.header_encode(header)
            # Don't add more folding whitespace than necessary
            if chunks and chunks[-1].endswith(' '):
                extra = ''
            else:
                extra = ' '
            _max_append(chunks, s, maxlinelen, extra)
        joiner = NL + self._continuation_ws
        return joiner.join(chunks)


class HTTPGenerator(Generator):

    def _handle_multipart(self, msg):
        # The trick here is to write out each part separately, merge them all
        # together, and then make sure that the boundary we've chosen isn't
        # present in the payload.
        msgtexts = []
        subparts = msg.get_payload()
        if subparts is None:
            subparts = []
        elif isinstance(subparts, six.string_types):
            # e.g. a non-strict parse of a message with no starting boundary.
            self._fp.write(subparts)
            return
        elif not isinstance(subparts, list):
            # Scalar payload
            subparts = [subparts]
        for part in subparts:
            s = StringIO()
            g = self.clone(s)
            g.flatten(part, unixfrom=False)
            msgtexts.append(s.getvalue())
        # BAW: What about boundaries that are wrapped in double-quotes?
        boundary = msg.get_boundary()
        if not boundary:
            # Create a boundary that doesn't appear in any of the
            # message texts.
            alltext = NL.join(msgtexts)
            boundary = _make_boundary(alltext)
            msg.set_boundary(boundary)
        # If there's a preamble, write it out, with a trailing CRLF
        if msg.preamble is not None:
            if self._mangle_from_:
                preamble = fcre.sub('>From ', msg.preamble)
            else:
                preamble = msg.preamble
            self._fp.write(preamble)
        # dash-boundary transport-padding CRLF
        self._fp.write('--' + boundary + NL)
        # body-part
        if msgtexts:
            self._fp.write(msgtexts.pop(0))
        # *encapsulation
        # --> delimiter transport-padding
        # --> CRLF body-part
        for body_part in msgtexts:
            # delimiter transport-padding CRLF
            self._fp.write(NL + '--' + boundary + NL)
            # body-part
            self._fp.write(body_part)
        # close-delimiter transport-padding
        self._fp.write(NL + '--' + boundary + '--' + NL)
        if msg.epilogue is not None:
            if self._mangle_from_:
                epilogue = fcre.sub('>From ', msg.epilogue)
            else:
                epilogue = msg.epilogue
            self._fp.write(epilogue)

    def _write_headers(self, msg):
        for h, v in msg.items():
            self._fp.write('%s: ' % h)
            if self._maxheaderlen == 0:
                # Explicit no-wrapping
                self._fp.write(v + NL)
            elif isinstance(v, Header):
                # Header instances know what to do
                self._fp.write(v.encode() + NL)
            elif _is8bitstring(v):
                # If we have raw 8bit data in a byte string, we have no idea
                # what the encoding is.  There is no safe way to split this
                # string.  If it's ascii-subset, then we could do a normal
                # ascii split, but if it's multibyte then we could break the
                # string.  There's no way to know so the least harm seems to
                # be to not split the string and risk it being too long.
                self._fp.write(v + NL)
            else:
                # Header's got lots of smarts, so use it.  Note that this is
                # fundamentally broken though because we lose idempotency when
                # the header string is continued with tabs.  It will now be
                # continued with spaces.  This was reversedly broken before we
                # fixed bug 1974.  Either way, we lose.
                h = Header(
                    v, maxlinelen=self._maxheaderlen, header_name=h).encode()
                self._fp.write(h + NL)
        # A blank line always separates headers from body
        self._fp.write(NL)
