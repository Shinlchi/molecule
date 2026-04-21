#!/usr/bin/python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: minio_user
short_description: Gère les utilisateurs MinIO
description:
  - Crée, supprime ou met à jour un utilisateur MinIO.
  - Attache ou détache une policy builtin (readwrite, readonly, writeonly, etc.).
options:
  access_key:
    description: Nom d'utilisateur (access key).
    type: str
    required: true
  secret_key:
    description: Mot de passe (secret key). Requis à la création.
    type: str
    required: false
  policy:
    description: |
      Policy builtin MinIO à attacher à l'utilisateur.
      Valeurs : readwrite, readonly, writeonly, diagnostics, consoleAdmin.
    type: str
    required: false
  force:
    description: Force la mise à jour du secret_key même si l'utilisateur existe.
    type: bool
    default: false
  state:
    description: État désiré de l'utilisateur.
    type: str
    default: present
    choices: [present, absent, enabled, disabled]
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
- name: Créer un utilisateur avec policy readwrite
  poc.minio.minio_user:
    access_key: ulamog
    secret_key: "{{ vault_ulamog_key }}"
    policy: readwrite
    auth:
      url: http://minio:9000
      access_key: minioadmin
      secret_key: minioadmin123
    state: present
  no_log: true

- name: Désactiver un utilisateur
  poc.minio.minio_user:
    access_key: ulamog
    state: disabled
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
from ansible_collections.poc.minio.plugins.module_utils.minio_utils import (
    minio_admin_client,
    minio_argument_spec,
)


def _user_info(admin, access_key):
    """Retourne le dict user_info ou None si l'utilisateur n'existe pas."""
    try:
        raw = admin.user_info(access_key)
        return json.loads(raw)
    except Exception:
        return None


def _current_policies(info):
    """Retourne la liste des policies courantes de l'utilisateur."""
    raw = (info or {}).get("policyName", "") or ""
    return [p.strip() for p in raw.split(",") if p.strip()]


def main():
    argument_spec = minio_argument_spec(
        access_key=dict(type="str", required=True),
        secret_key=dict(type="str", required=False, no_log=True),
        policy=dict(type="str", required=False, default=None),
        force=dict(type="bool", default=False),
        state=dict(
            type="str",
            default="present",
            choices=["present", "absent", "enabled", "disabled"],
        ),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    access_key = module.params["access_key"]
    secret_key = module.params["secret_key"]
    policy = module.params["policy"]
    force = module.params["force"]
    state = module.params["state"]
    changed = False

    admin = minio_admin_client(module)
    info = _user_info(admin, access_key)
    exists = info is not None

    if state == "absent":
        if exists:
            if not module.check_mode:
                admin.user_remove(access_key)
            changed = True
        module.exit_json(changed=changed)

    # state ∈ {present, enabled, disabled}
    if not exists:
        if not secret_key:
            module.fail_json(msg="'secret_key' est requis pour créer un utilisateur")
        if not module.check_mode:
            admin.user_add(access_key, secret_key)
        changed = True
        # info n'est pas encore dispo — on ne peut pas comparer les policies
        current_policies = []
    else:
        current_policies = _current_policies(info)
        if force and secret_key:
            if not module.check_mode:
                admin.user_add(access_key, secret_key)
            changed = True

    # Gestion de la policy
    if policy is not None:
        if policy not in current_policies:
            if not module.check_mode:
                # Détache les policies existantes puis attache la nouvelle
                if current_policies:
                    admin.detach_policy(current_policies, user=access_key)
                admin.attach_policy([policy], user=access_key)
            changed = True

    # Gestion de l'état enabled/disabled
    if state in ("enabled", "disabled") and exists:
        current_status = (info or {}).get("status", "enabled")
        if state == "enabled" and current_status != "enabled":
            if not module.check_mode:
                admin.user_enable(access_key)
            changed = True
        elif state == "disabled" and current_status != "disabled":
            if not module.check_mode:
                admin.user_disable(access_key)
            changed = True

    module.exit_json(changed=changed)


if __name__ == "__main__":
    main()
