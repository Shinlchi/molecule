#!/usr/bin/python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: minio_group
short_description: Gère les groupes MinIO
description:
  - Crée, supprime, active ou désactive un groupe MinIO.
  - Gère les membres et la policy attachée au groupe.
options:
  name:
    description: Nom du groupe.
    type: str
    required: true
  state:
    description: État désiré du groupe.
    type: str
    default: present
    choices: [present, absent, enabled, disabled]
  members:
    description: Liste des access keys des utilisateurs membres du groupe.
    type: list
    elements: str
    required: false
    default: []
  policy:
    description: Nom de la policy à attacher au groupe.
    type: str
    required: false
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
- name: Créer un groupe avec membres et policy
  poc.minio.minio_group:
    name: app-team
    members:
      - alice
      - bob
    policy: app-readonly
    auth:
      url: http://minio:9000
      access_key: minioadmin
      secret_key: minioadmin123

- name: Désactiver un groupe
  poc.minio.minio_group:
    name: app-team
    state: disabled
    auth:
      url: http://minio:9000
      access_key: minioadmin
      secret_key: minioadmin123

- name: Supprimer un groupe
  poc.minio.minio_group:
    name: app-team
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


def _group_info(admin, name):
    """Retourne le dict group_info ou None si le groupe n'existe pas."""
    try:
        raw = admin.group_info(name)
        return json.loads(raw) if isinstance(raw, (str, bytes)) else raw
    except Exception:
        return None


def main():
    argument_spec = auth_argument_spec(
        name=dict(type="str", required=True),
        state=dict(type="str", default="present", choices=["present", "absent", "enabled", "disabled"]),
        members=dict(type="list", elements="str", required=False, default=[]),
        policy=dict(type="str", required=False, default=None),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    name = module.params["name"]
    state = module.params["state"]
    members = module.params["members"]
    policy = module.params["policy"]
    changed = False

    admin = get_admin_client(module)
    info = _group_info(admin, name)
    exists = info is not None

    if state == "absent":
        if exists:
            if not module.check_mode:
                admin.group_remove(name)
            changed = True
        module.exit_json(changed=changed)

    # state ∈ {present, enabled, disabled}
    if not exists:
        if not module.check_mode:
            admin.group_add(name, members)
        changed = True
        current_members = []
        current_policy = None
        current_status = "enabled"
    else:
        current_members = info.get("members", []) or []
        current_policy = info.get("policy") or None
        current_status = info.get("status", "enabled")

        desired_members = set(members)
        existing_members = set(current_members)

        to_add = desired_members - existing_members
        to_remove = existing_members - desired_members

        if to_add:
            if not module.check_mode:
                admin.group_add(name, list(to_add))
            changed = True

        if to_remove:
            if not module.check_mode:
                admin.group_remove(name, list(to_remove))
            changed = True

    # Gestion de la policy
    if policy is not None and policy != current_policy:
        if not module.check_mode:
            try:
                admin.attach_policy([policy], group=name)
                changed = True
            except Exception as e:
                if "XMinioAdminPolicyChangeAlreadyApplied" in str(e):
                    pass  # policy déjà attachée — pas un changement réel
                else:
                    raise
        else:
            changed = True

    # Gestion de l'état enabled/disabled
    if state == "enabled" and current_status != "enabled":
        if not module.check_mode:
            admin.group_enable(name)
        changed = True
    elif state == "disabled" and current_status != "disabled":
        if not module.check_mode:
            admin.group_disable(name)
        changed = True

    module.exit_json(changed=changed)


if __name__ == "__main__":
    main()
