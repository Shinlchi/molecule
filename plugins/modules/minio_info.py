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
  - Collecte la liste des policies, buckets, utilisateurs, groupes et service accounts.
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
policies:
  description: Noms des policies custom (hors policies système MinIO).
  type: list
  returned: always
  elements: str
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
groups:
  description: Liste des groupes avec leurs membres et policy.
  type: list
  returned: always
  elements: dict
  contains:
    name:
      type: str
    members:
      type: list
    policy:
      type: str
    status:
      type: str
service_accounts:
  description: Liste des service accounts avec leur user parent.
  type: list
  returned: always
  elements: dict
  contains:
    access_key:
      type: str
    parent_user:
      type: str
"""

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.poc.minio.plugins.module_utils.client import get_client, get_admin_client
from ansible_collections.poc.minio.plugins.module_utils.args import auth_argument_spec
from minio.minioadmin import _COMMAND, decrypt

_BUILTIN_POLICIES = {"readonly", "readwrite", "writeonly", "diagnostics", "consoleAdmin"}


def _list_policies(admin):
    raw = admin.policy_list()
    data = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
    return [name for name in (data or {}) if name not in _BUILTIN_POLICIES]


def _bucket_quota(admin, name):
    try:
        raw = admin.bucket_quota_get(name)
        return int(json.loads(raw).get("quota", 0))
    except Exception:
        return 0


def _list_buckets(client, admin):
    return [
        {"name": b.name, "quota_bytes": _bucket_quota(admin, b.name)}
        for b in client.list_buckets()
    ]


def _list_users(admin):
    raw = admin.user_list()
    data = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
    return [
        {
            "access_key": ak,
            "policy": info.get("policyName", ""),
            "status": info.get("status", ""),
        }
        for ak, info in (data or {}).items()
    ]


def _list_groups(admin):
    raw = admin.group_list()
    names = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
    groups = []
    for name in (names or []):
        try:
            info_raw = admin.group_info(name)
            info = json.loads(info_raw) if isinstance(info_raw, (str, bytes)) else info_raw
        except Exception:
            info = {}
        groups.append({
            "name": name,
            "members": info.get("members") or [],
            "policy": info.get("policy") or None,
            "status": info.get("status", "enabled"),
        })
    return groups


def _list_service_accounts(admin, users):
    secret = admin._provider.retrieve().secret_key
    service_accounts = []
    for user in users:
        try:
            response = admin._url_open(
                method="GET",
                command=_COMMAND.SERVICE_ACCOUNT_LIST,
                query_params={"user": user},
                preload_content=False,
            )
            data = json.loads(decrypt(response, secret))
            for sa in data.get("accounts") or []:
                service_accounts.append({
                    "access_key": sa.get("accessKey"),
                    "parent_user": user,
                })
        except Exception:
            pass
    return service_accounts


def main():
    module = AnsibleModule(
        argument_spec=auth_argument_spec(),
        supports_check_mode=True,
    )

    client = get_client(module)
    admin = get_admin_client(module)

    users = _list_users(admin)
    user_keys = [u["access_key"] for u in users]

    module.exit_json(
        changed=False,
        policies=_list_policies(admin),
        buckets=_list_buckets(client, admin),
        users=users,
        groups=_list_groups(admin),
        service_accounts=_list_service_accounts(admin, user_keys),
    )


if __name__ == "__main__":
    main()
