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
- name: Créer un bucket
  poc.minio.minio_bucket:
    name: mon-bucket
    auth:
      url: http://minio:9000
      access_key: minioadmin
      secret_key: minioadmin123
    state: present
"""

RETURN = r"""
changed:
  description: Indique si l'état a changé.
  type: bool
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.poc.minio.plugins.module_utils.minio_utils import (
    minio_client,
    minio_argument_spec,
)


def main():
    argument_spec = minio_argument_spec(
        name=dict(type="str", required=True),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    name = module.params["name"]
    state = module.params["state"]
    changed = False

    client = minio_client(module)
    exists = client.bucket_exists(name)

    if state == "present" and not exists:
        if not module.check_mode:
            client.make_bucket(name)
        changed = True
    elif state == "absent" and exists:
        if not module.check_mode:
            client.remove_bucket(name)
        changed = True

    module.exit_json(changed=changed)


if __name__ == "__main__":
    main()
