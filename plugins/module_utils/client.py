#!/usr/bin/python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from urllib.parse import urlparse

try:
    import minio
    import minio.credentials.providers
    HAS_MINIO = True
except ImportError:
    HAS_MINIO = False


def ensure_minio(module):
    if not HAS_MINIO:
        module.fail_json(msg="Le package Python 'minio>=7.1.4' est requis.")


def get_client(module):
    """Client S3 MinIO (opérations sur les buckets et objets)."""
    ensure_minio(module)
    auth = module.params["auth"]
    parsed = urlparse(auth["url"])
    return minio.Minio(
        parsed.netloc,
        access_key=auth["access_key"],
        secret_key=auth["secret_key"],
        secure=parsed.scheme == "https",
    )


def get_admin_client(module):
    """Client admin MinIO (utilisateurs, policies, quotas)."""
    ensure_minio(module)
    auth = module.params["auth"]
    parsed = urlparse(auth["url"])
    return minio.MinioAdmin(
        endpoint=parsed.netloc,
        credentials=minio.credentials.providers.StaticProvider(
            auth["access_key"],
            auth["secret_key"],
        ),
        secure=parsed.scheme == "https",
    )
