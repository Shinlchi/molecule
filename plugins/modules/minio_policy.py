#!/usr/bin/python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: minio_policy
short_description: Gère les policies IAM MinIO
description:
  - Crée, met à jour ou supprime une policy IAM custom dans MinIO.
options:
  name:
    description: Nom de la policy.
    type: str
    required: true
  state:
    description: État désiré de la policy.
    type: str
    default: present
    choices: [present, absent]
  statements:
    description: |
      Liste des statements IAM. Requis quand state=present.
    type: list
    elements: dict
    required: false
    suboptions:
      effect:
        description: Allow ou Deny.
        type: str
        required: true
        choices: [Allow, Deny]
      actions:
        description: Liste des actions S3 (ex: s3:GetObject).
        type: list
        elements: str
        required: true
      resources:
        description: Liste des ARNs de ressources cibles.
        type: list
        elements: str
        required: true
  auth:
    description: Paramètres de connexion admin MinIO.
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
- name: Créer une policy lecture seule sur un bucket
  poc.minio.minio_policy:
    name: app-readonly
    statements:
      - effect: Allow
        actions:
          - s3:GetObject
          - s3:ListBucket
        resources:
          - arn:aws:s3:::mon-bucket
          - arn:aws:s3:::mon-bucket/*
    auth:
      url: http://minio:9000
      access_key: minioadmin
      secret_key: minioadmin123

- name: Supprimer une policy
  poc.minio.minio_policy:
    name: app-readonly
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
from ansible_collections.poc.minio.plugins.module_utils.client import get_admin_client
from ansible_collections.poc.minio.plugins.module_utils.args import auth_argument_spec

try:
    from minio.minioadmin import _COMMAND
    HAS_COMMAND = True
except ImportError:
    HAS_COMMAND = False


def _build_policy_doc(statements):
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": s["effect"],
                "Action": s["actions"],
                "Resource": s["resources"],
            }
            for s in statements
        ],
    }


def _get_policy(admin, name):
    """Retourne le document de policy ou None si elle n'existe pas."""
    try:
        raw = admin.policy_info(name)
        return json.loads(raw) if isinstance(raw, (str, bytes)) else raw
    except Exception:
        return None


def _policy_changed(current, desired):
    """Compare deux documents de policy (normalisation par tri des clés)."""
    return json.dumps(current, sort_keys=True) != json.dumps(desired, sort_keys=True)


def _apply_policy(admin, name, statements):
    if not HAS_COMMAND:
        raise RuntimeError("minio.minioadmin._COMMAND introuvable — version minio incompatible")
    body = json.dumps(_build_policy_doc(statements)).encode()
    admin._url_open(method="PUT", command=_COMMAND.ADD_CANNED_POLICY, query_params={"name": name}, body=body)


def main():
    argument_spec = auth_argument_spec(
        name=dict(type="str", required=True),
        state=dict(type="str", default="present", choices=["present", "absent"]),
        statements=dict(type="list", elements="dict", required=False, default=None),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    name = module.params["name"]
    state = module.params["state"]
    statements = module.params["statements"]
    changed = False

    admin = get_admin_client(module)
    current = _get_policy(admin, name)
    exists = current is not None

    if state == "absent":
        if exists:
            if not module.check_mode:
                admin.policy_remove(name)
            changed = True
        module.exit_json(changed=changed)

    # state == "present"
    if statements is None:
        module.fail_json(msg="'statements' est requis quand state=present")

    desired = _build_policy_doc(statements)

    if not exists:
        if not module.check_mode:
            _apply_policy(admin, name, statements)
        changed = True
    elif _policy_changed(current, desired):
        if not module.check_mode:
            _apply_policy(admin, name, statements)
        changed = True

    module.exit_json(changed=changed)


if __name__ == "__main__":
    main()
