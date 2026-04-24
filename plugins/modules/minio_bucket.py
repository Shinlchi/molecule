#!/usr/bin/python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: minio_bucket
short_description: Gère les buckets MinIO
description:
  - Crée ou supprime un bucket MinIO.
  - Définit ou supprime le quota du bucket.
options:
  name:
    description: Nom du bucket.
    type: str
    required: true
  state:
    description: État désiré du bucket.
    type: str
    default: present
    choices: [present, absent]
  quota:
    description: |
      Quota maximum du bucket. Formats acceptés : GiB, MiB, KiB, TiB, GB, MB, KB, TB.
      Ex : '1GiB', '512MiB'. Utiliser absent pour supprimer le quota.
    type: str
    required: false
  auth:
    description: Paramètres de connexion MinIO.
    type: dict
    required: true
    suboptions:
      url:
        description: URL du serveur MinIO.
        type: str
        required: true
      access_key:
        description: Clé d'accès (root user ou service account).
        type: str
        required: true
      secret_key:
        description: Clé secrète.
        type: str
        required: true
requirements:
  - python >= 3.8
  - minio >= 7.1.4
"""

EXAMPLES = r"""
- name: Créer un bucket avec quota
  poc.minio.minio_bucket:
    name: mon-bucket
    quota: 10GiB
    auth:
      url: http://minio:9000
      access_key: minioadmin
      secret_key: minioadmin123

- name: Supprimer un bucket
  poc.minio.minio_bucket:
    name: mon-bucket
    state: absent
    auth:
      url: http://minio:9000
      access_key: minioadmin
      secret_key: minioadmin123
"""

RETURN = r"""
changed:
  description: Indique si l'état a changé.
  type: bool
  returned: always
"""

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.poc.minio.plugins.module_utils.client import get_client, get_admin_client
from ansible_collections.poc.minio.plugins.module_utils.args import auth_argument_spec, parse_size


def _get_quota(admin, name):
    try:
        raw = admin.bucket_quota_get(name)
        return int(json.loads(raw).get("quota", 0))
    except Exception:
        return 0


def main():
    argument_spec = auth_argument_spec(
        name=dict(type="str", required=True),
        state=dict(type="str", default="present", choices=["present", "absent"]),
        quota=dict(type="str", required=False, default=None),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    name = module.params["name"]
    state = module.params["state"]
    quota_str = module.params["quota"]
    changed = False

    client = get_client(module)
    exists = client.bucket_exists(name)

    if state == "present" and not exists:
        if not module.check_mode:
            client.make_bucket(name)
        changed = True
    elif state == "absent" and exists:
        if not module.check_mode:
            client.remove_bucket(name)
        changed = True

    if state == "present" and quota_str is not None:
        admin = get_admin_client(module)
        current = _get_quota(admin, name)

        if quota_str == "absent":
            if current != 0:
                if not module.check_mode:
                    admin.bucket_quota_clear(name)
                changed = True
        else:
            try:
                desired = parse_size(quota_str)
            except ValueError as exc:
                module.fail_json(msg=str(exc))
            if current != desired:
                if not module.check_mode:
                    admin.bucket_quota_set(name, desired)
                changed = True

    module.exit_json(changed=changed)


if __name__ == "__main__":
    main()
