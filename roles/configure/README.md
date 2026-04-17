# Role: demo.harbor_like.configure

Applique une configuration Harbor-like à partir d'une liste déclarative
d'entries.

## Variables d'entrée

| Variable  | Type | Requis | Description                                  |
|-----------|------|--------|----------------------------------------------|
| `server`  | dict | oui    | URL + credentials du Harbor-like cible       |
| `entries` | list | oui    | Liste d'entrées à appliquer (cf. ci-dessous) |

### `server`

```yaml
server:
  url: https://harbor.example.com
  username: admin
  password: "{{ lookup('env', 'HARBOR_PASSWORD') }}"
  validate_certs: true
```

### `entries`

Chaque item est un dict avec **une seule clé** qui décrit le type d'objet à
appliquer. Dans cette démo on ne gère que `project`, mais la structure permet
d'étendre à `registry`, `robot`, `replication`, etc.

```yaml
entries:
  - project:
      - name: demo
        visibility: public
  - project:
      - name: internal
        visibility: private
        storage_limit_gb: 50
```

## Exemple d'appel

```yaml
- hosts: localhost
  roles:
    - role: demo.harbor_like.configure
      vars:
        server:
          url: https://harbor.example.com
          username: admin
          password: "{{ harbor_admin_password }}"
        entries: "{{ harbor_entries }}"
```

## Tests

Un scénario molecule complet est disponible dans `molecule/default/` :

```bash
molecule test      # converge + idempotence + verify + destroy
```
