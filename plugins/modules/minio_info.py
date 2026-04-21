#!/usr/bin/python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: minio_info
short_description: Retourne l'état complet d'un serveur MinIO
description:
  - Collecte la liste des buckets (avec quota), des utilisateurs (avec policy et statut).
options:
  auth:
    description: Paramètres de connexion MinIO.
    type: dict
    required: true
    suboptions:
      url:
        type: str
        required: true
      access_key:
        type: str
        required: true
      secret_key:
        type: str
        required: true
requirements:
  - python >= 3.8
  - minio >= 7.1.4
"""

EXAMPLES = r"""
- name: Audit MinIO
  poc.minio.minio_info:
    auth:
      url: http://minio:9000
      access_key: minioadmin
      secret_key: minioadmin123
  register: minio_state
"""

RETURN = r"""
buckets:
  description: Liste des buckets avec leur quota.
  type: list
  returned: always
  elements: dict
  contains:
    name:
      type: str
    quota_bytes:
      type: int
      description: 0 signifie aucun quota défini.
users:
  description: Liste des utilisateurs avec leur policy et statut.
  type: list
  returned: always
  elements: dict
  contains:
    access_key:
      type: str
    policy:
      type: str
    status:
      type: str
"""

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.poc.minio.plugins.module_utils.minio_utils import (
    minio_client,
    minio_admin_client,
    minio_argument_spec,
)


def _bucket_quota(admin, name):
    try:
        raw = admin.bucket_quota_get(name)
        return int(json.loads(raw).get("quota", 0))
    except Exception:
        return 0


def _user_list(admin):
    try:
        raw = admin.user_list()
        return json.loads(raw)
    except Exception:
        return {}


def main():
    module = AnsibleModule(
        argument_spec=minio_argument_spec(),
        supports_check_mode=True,
    )

    client = minio_client(module)
    admin = minio_admin_client(module)

    buckets = []
    for b in client.list_buckets():
        buckets.append({
            "name": b.name,
            "quota_bytes": _bucket_quota(admin, b.name),
        })

    users = []
    for access_key, info in _user_list(admin).items():
        users.append({
            "access_key": access_key,
            "policy": info.get("policyName", ""),
            "status": info.get("status", ""),
        })

    module.exit_json(changed=False, buckets=buckets, users=users)


if __name__ == "__main__":
    main()
