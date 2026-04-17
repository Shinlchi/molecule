# 1) pipx (si pas déjà là)
brew install pipx
pipx ensurepath


# 2) ansible + molecule + plugins docker + linters dans le même venv pipx
pipx install --include-deps "ansible-core>=2.15,<2.18"
pipx inject ansible-core \
  "molecule>=24" \
  "molecule-plugins[docker]>=23.5" \
  "docker>=7" \
  "ansible-lint>=24" \
  "yamllint>=1.35" \
  "pytest-testinfra>=10"

# 3) collections requises par le scénario
ansible-galaxy collection install ansible.posix community.general

# 4) vérif
molecule --version
ansible --version
ansible-lint --version
yamllint --version