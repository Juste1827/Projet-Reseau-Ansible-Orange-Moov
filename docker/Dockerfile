# WHY Docker : Ansible (control node) n'est pas supporté nativement sur Windows.
# Cette image = ton poste "opérateur Linux" reproductible, sans installer WSL si tu as Docker Desktop.

FROM python:3.12-slim

# Paquets SSH client : network_cli ouvre un SSH vers les équipements
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work

# ansible-core = moteur ; ansible-lint = qualité CI
RUN pip install --no-cache-dir "ansible-core>=2.17" ansible-lint

# Collections réseau (versions figées via requirements.yml du dépôt)
COPY requirements.yml /tmp/requirements.yml
RUN ansible-galaxy collection install -r /tmp/requirements.yml

# Le dépôt sera monté en volume : -v ${PWD}:/work
CMD ["ansible-playbook", "--version"]
