#!/usr/bin/python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: minio_bucket_quota
short_description: Gère le quota d'un bucket MinIO
description:
  - Définit ou supprime le quota (hard limit) d'un bucket MinIO.
  - Utilise l'API admin MinIO — aucun binaire mc requis.
options:
  bucket:
    description: Nom du bucket cible.
    type: str
    required: true
  size:
    description: |
      Taille maximale du bucket. Formats acceptés : GiB, MiB, KiB, TiB, GB, MB, KB, TB.
      Ex : '1GiB', '512MiB', '10GB'.
      Ignoré si state=absent.
    type: str
    required: false
  state:
    description: >
      present applique le quota défini par size.
      absent supprime le quota existant.
    type: str
    default: present
    choices: [present, absent]
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
        description: Clé d'accès admin.
        type: str
        required: true
      secret_key:
        description: Clé secrète admin.
        type: str
        required: true
requirements:
  - python >= 3.8
  - minio >= 7.1.4
"""

EXAMPLES = r"""
- name: Quota de 1 GiB sur mon-bucket
  poc.minio.minio_bucket_quota:
    bucket: mon-bucket
    size: 1GiB
    auth:
      url: http://minio:9000
      access_key: minioadmin
      secret_key: minioadmin123

- name: Supprimer le quota
  poc.minio.minio_bucket_quota:
    bucket: mon-bucket
    state: absent
    auth:
      url: http://minio:9000
      access_key: minioadmin
      secret_key: minioadmin123
"""

RETURN = r"""
changed:
  description: Indique si le quota a été modifié.
  type: bool
  returned: always
current_quota_bytes:
  description: Quota courant en octets (0 = aucun quota).
  type: int
  returned: always
"""

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.poc.minio.plugins.module_utils.minio_utils import (
    minio_admin_client,
    minio_argument_spec,
    parse_size,
)


def _get_quota(admin, bucket):
    """Retourne le quota actuel en octets, 0 si aucun."""
    try:
        raw = admin.bucket_quota_get(bucket)
        data = json.loads(raw)
        return int(data.get("quota", 0))
    except Exception:
        return 0


def main():
    argument_spec = minio_argument_spec(
        bucket=dict(type="str", required=True),
        size=dict(type="str", required=False, default=None),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    bucket = module.params["bucket"]
    size_str = module.params["size"]
    state = module.params["state"]
    changed = False

    admin = minio_admin_client(module)
    current = _get_quota(admin, bucket)

    if state == "absent":
        if current != 0:
            if not module.check_mode:
                admin.bucket_quota_clear(bucket)
            changed = True
    else:
        if size_str is None:
            module.fail_json(msg="'size' est requis quand state=present")
        try:
            desired = parse_size(size_str)
        except ValueError as exc:
            module.fail_json(msg=str(exc))

        if current != desired:
            if not module.check_mode:
                admin.bucket_quota_set(bucket, desired)
            changed = True

    module.exit_json(changed=changed, current_quota_bytes=current)


if __name__ == "__main__":
    main()
