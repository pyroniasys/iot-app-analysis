"""Parse bounce messages generated by Postfix.

This also matches something called 'Keftamail' which looks just like Postfix
bounces with the word Postfix scratched out and the word 'Keftamail' written
in in crayon.

It also matches something claiming to be 'The BNS Postfix program', and
'SMTP_Gateway'.  Everybody's gotta be different, huh?
"""

import re

from enum import Enum
from flufl.bounce.interfaces import (
    IBounceDetector, NoFailures, NoTemporaryFailures)
from io import BytesIO
from public import public
from zope.interface import implementer


# Are these heuristics correct or guaranteed?
pcre = re.compile(
    b'[ \\t]*the\\s*(bns)?\\s*(postfix|keftamail|smtp_gateway)',
    re.IGNORECASE)
rcre = re.compile(b'failure reason:$', re.IGNORECASE)
acre = re.compile(b'<(?P<addr>[^>]*)>:')

REPORT_TYPES = ('multipart/mixed', 'multipart/report')


class ParseState(Enum):
    start = 0
    salutation_found = 1


def flatten(msg, leaves):
    # Give us all the leaf (non-multipart) subparts.
    if msg.is_multipart():
        for part in msg.get_payload():
            flatten(part, leaves)
    else:
        leaves.append(msg)


def findaddr(msg):
    addresses = set()
    body = BytesIO(msg.get_payload(decode=True))
    state = ParseState.start
    for line in body:
        # Preserve leading whitespace.
        line = line.rstrip()
        # Yes, use match() to match at beginning of string.
        if state is ParseState.start and (
                pcre.match(line) or rcre.match(line)):
            # Then...
            state = ParseState.salutation_found
        elif state is ParseState.salutation_found and line:
            mo = acre.search(line)
            if mo:
                addresses.add(mo.group('addr'))
            # Probably a continuation line.
    return addresses


@public
@implementer(IBounceDetector)
class Postfix:
    """Parse bounce messages generated by Postfix."""

    def process(self, msg):
        """See `IBounceDetector`."""
        if msg.get_content_type() not in REPORT_TYPES:
            return NoFailures
        # We're looking for the plain/text subpart with a Content-Description:
        # of 'notification'.
        leaves = []
        flatten(msg, leaves)
        for subpart in leaves:
            content_type = subpart.get_content_type()
            content_desc = subpart.get('content-description', '').lower()
            if content_type == 'text/plain' and content_desc == 'notification':
                return NoTemporaryFailures, set(findaddr(subpart))
        return NoFailures
