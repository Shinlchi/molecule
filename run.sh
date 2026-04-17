cd /Users/shin/Documents/Claude/Projects/molecule
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ansible-galaxy collection install ansible.posix community.general
molecule --version
