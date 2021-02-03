# Copyright (C) AB Strakt
# See LICENSE for details.

"""
pyOpenSSL - A simple wrapper around the OpenSSL library
"""

from odoo.addons.tools_edi_as2.OpenSSL import crypto, SSL
from odoo.addons.tools_edi_as2.OpenSSL.version import (
    __author__, __copyright__, __email__, __license__, __summary__, __title__,
    __uri__, __version__,
)


__all__ = [
    "SSL", "crypto",

    "__author__", "__copyright__", "__email__", "__license__", "__summary__",
    "__title__", "__uri__", "__version__",
]
