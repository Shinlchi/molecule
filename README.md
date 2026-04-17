# demo.harbor_like

Collection Ansible de démo qui imite la configuration d'un Harbor-like à partir
d'une liste déclarative d'`entries`. L'objectif est de montrer la structure
complète d'une collection testée avec `molecule` et lintée avec `ansible-lint`
et `yamllint`.

## Contenu

- `roles/configure` : rôle principal. Prend en entrée :
  - `server` : objet décrivant le serveur cible (url, credentials, …).
  - `entries` : liste d'entrées à appliquer. Chaque entrée peut définir un
    bloc `project`, `registry`, `robot`, etc. Dans cet exemple on se
    concentre sur `project`.
- `playbooks/consumer.yml` : playbook consommateur montrant comment un autre
  projet appelle `demo.harbor_like.configure` avec ses propres `entries`.
- `roles/configure/molecule/default/` : scénario molecule (driver `docker`,
  fallback `delegated`) qui exécute `converge → idempotence → verify`, soit
  exactement la séquence RUN / RUN IDEMPOT / AUDIT.

## Format des entries

```yaml
harbor_entries:
  - project:
      - name: demo
        visibility: public
  - project:
      - name: internal
        visibility: private
```

Chaque entry est un dict avec une seule clé (`project`, `registry`, …) dont la
valeur est une liste d'objets à créer. Le rôle boucle sur `entries` et délègue
à `tasks/create_entry.yml` pour chaque item.

## Lint

```bash
yamllint .
ansible-lint
```

## Tests (molecule)

```bash
cd roles/configure
molecule test                 # converge + idempotence + verify + destroy
# ou étape par étape :
molecule converge
molecule idempotence
molecule verify
molecule destroy
```

## Utilisation depuis un autre projet

```yaml
# requirements.yml
collections:
  - name: demo.harbor_like
    source: https://example.com/demo/harbor_like
    version: ">=1.0.0"
```

```bash
ansible-galaxy collection install -r requirements.yml
ansible-playbook -i inventory my_playbook.yml
```

Voir `playbooks/consumer.yml` pour un exemple complet.
