#!/usr/bin/python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re

# IEC (puissances de 1024) et SI (puissances de 1000), dans l'ordre le plus long en premier
# pour que la regex tente "GiB" avant "G"
_SIZE_UNITS = {
    "TiB": 1024**4, "GiB": 1024**3, "MiB": 1024**2, "KiB": 1024**1,
    "TB":  10**12,  "GB":  10**9,   "MB":  10**6,   "KB":  10**3,
    "T":   1024**4, "G":   1024**3, "M":   1024**2, "K":   1024**1,
    "B":   1,
}

_SIZE_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(TiB|GiB|MiB|KiB|TB|GB|MB|KB|T|G|M|K|B)?\s*$"
)


def parse_size(size_str):
    """Convertit une chaîne lisible en octets. Ex : '1GiB' -> 1073741824."""
    m = _SIZE_RE.match(str(size_str))
    if not m:
        raise ValueError("Format de taille invalide : %s" % size_str)
    value = float(m.group(1))
    unit = m.group(2) or "B"
    return int(value * _SIZE_UNITS[unit])


def auth_argument_spec(**kwargs):
    """Retourne un argument_spec incluant le bloc 'auth' standard."""
    spec = dict(
        auth=dict(
            type="dict",
            required=True,
            no_log=True,
            options=dict(
                url=dict(type="str", required=True),
                access_key=dict(type="str", required=True),
                secret_key=dict(type="str", required=True, no_log=True),
            ),
        )
    )
    spec.update(kwargs)
    return spec
