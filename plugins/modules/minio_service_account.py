#!/usr/bin/python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: minio_service_account
short_description: Gère les service accounts MinIO
description:
  - Crée ou supprime un service account MinIO rattaché à un utilisateur parent.
  - Un service account hérite des droits du parent avec une policy optionnellement restreinte.
  - Le service account ne peut pas se connecter à la console MinIO.
options:
  access_key:
    description: Access key du service account. Requis pour le supprimer (state=absent).
    type: str
    required: false
  secret_key:
    description: Secret key du service account. Requis à la création.
    type: str
    required: false
    no_log: true
  user:
    description: Access key de l'utilisateur parent. Requis à la création.
    type: str
    required: false
  state:
    description: État désiré du service account.
    type: str
    default: present
    choices: [present, absent]
  statements:
    description: |
      Policy IAM restreinte optionnelle. Doit être un sous-ensemble des droits du parent.
      Si absent, le service account hérite de tous les droits du parent.
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
        description: Liste des actions S3.
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
- name: Créer un service account pour une app (droits complets du parent)
  poc.minio.minio_service_account:
    access_key: app-backend-sa
    secret_key: "{{ vault_sa_key }}"
    user: alice
    auth:
      url: http://minio:9000
      access_key: minioadmin
      secret_key: minioadmin123
  no_log: true

- name: Créer un service account avec policy restreinte
  poc.minio.minio_service_account:
    access_key: app-reader-sa
    secret_key: "{{ vault_sa_key }}"
    user: alice
    statements:
      - effect: Allow
        actions:
          - s3:GetObject
        resources:
          - arn:aws:s3:::mon-bucket/*
    auth:
      url: http://minio:9000
      access_key: minioadmin
      secret_key: minioadmin123
  no_log: true

- name: Supprimer un service account
  poc.minio.minio_service_account:
    access_key: app-backend-sa
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
access_key:
  description: Access key du service account créé.
  type: str
  returned: when state=present and created
secret_key:
  description: Secret key du service account créé. Uniquement disponible à la création.
  type: str
  returned: when state=present and created
  no_log: true
"""

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.poc.minio.plugins.module_utils.client import get_admin_client
from ansible_collections.poc.minio.plugins.module_utils.args import auth_argument_spec


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


def _sa_exists(admin, access_key):
    """Retourne True si le service account existe."""
    try:
        admin.service_account_info(access_key)
        return True
    except Exception:
        return False


def main():
    argument_spec = auth_argument_spec(
        access_key=dict(type="str", required=False, default=None),
        secret_key=dict(type="str", required=False, default=None, no_log=True),
        user=dict(type="str", required=False, default=None),
        state=dict(type="str", default="present", choices=["present", "absent"]),
        statements=dict(type="list", elements="dict", required=False, default=None),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    access_key = module.params["access_key"]
    secret_key = module.params["secret_key"]
    user = module.params["user"]
    state = module.params["state"]
    statements = module.params["statements"]
    changed = False

    admin = get_admin_client(module)

    if state == "absent":
        if not access_key:
            module.fail_json(msg="'access_key' est requis pour supprimer un service account")
        if _sa_exists(admin, access_key):
            if not module.check_mode:
                admin.service_account_remove(access_key)
            changed = True
        module.exit_json(changed=changed)

    # state == "present"
    if not user:
        module.fail_json(msg="'user' est requis pour créer un service account")
    if not secret_key:
        module.fail_json(msg="'secret_key' est requis pour créer un service account")

    if access_key and _sa_exists(admin, access_key):
        module.exit_json(changed=False, access_key=access_key)

    policy = json.dumps(_build_policy_doc(statements)) if statements else None

    if not module.check_mode:
        resp = admin.service_account_add(
            access_key=user,
            access_key_id=access_key,
            secret_key=secret_key,
            policy=policy,
        )
        result = json.loads(resp) if isinstance(resp, (str, bytes)) else resp
        module.exit_json(
            changed=True,
            access_key=result.get("accessKey", access_key),
            secret_key=result.get("secretKey", secret_key),
        )

    module.exit_json(changed=True, access_key=access_key)


if __name__ == "__main__":
    main()
