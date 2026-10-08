# netauto-ansible-lab

Lab **IaC réseau** : déployer une config de base **multi-constructeurs** (Cisco IOS + Huawei VRP) avec Ansible — hostname, VLAN, IP d’interface — de façon **reproductible, idempotente et sûre**.

Conçu pour un portfolio type poste **Automatisation réseau / Orange · Moov** : tu peux cloner, lancer la démo **sans aucun routeur**, et expliquer le *pourquoi* en entretien.

## Topologie lab (fictive, RFC 5737)

```
 VLAN10 DATA 10.10.10.0/24          VLAN20 VOICE 10.20.20.0/24
        .1 Cisco SVI                         .1 Cisco SVI
        .2 Huawei Vlanif                     .2 Huawei Vlanif

 R1-PE-ABJ (Cisco IOS)  Gi0/0 10.0.0.1/30
         |  P2P
 R2-PE-ABJ (Huawei VRP) Gi0/0/0 10.0.0.2/30
```

Les IP `192.0.2.11/12` sont des adresses de **documentation** : impossible de viser un vrai nœud opérateur par erreur.

## Pourquoi cette architecture

| Couche | Rôle | Analogie télécom |
|---|---|---|
| `inventory/` | Source de vérité (quoi) | Fichier d’ingénierie / IPAM |
| `templates/` | Dialecte CLI (comment) | Cisco vs VRP |
| `roles/` | Modules idempotents | Playbook d’exploit |
| `scripts/render_intended.py` | Démo Windows sans Ansible | « plan » Git, sans SSH |
| `live: false` | Garde-fou | jamais de push par défaut |

**Idempotence** : `pytest` relance le rendu **10 fois** et exige le même SHA256.

**Sécurité** : pas de mot de passe dans Git ; `vault.yml.example` ; push SSH uniquement avec `-e live=true` ; backup playbook **read-only** (`show` / `display`).

## Arborescence

```
inventory/          hosts, group_vars, host_vars (vérité)
playbooks/          01 deploy · 02 backup · 03 check
roles/              cisco_ios_base · huawei_vrp_base
templates/          cisco_ios_base.j2 · huawei_vrp_base.j2
filter_plugins/     CIDR → adresse + masque (une seule fois dans le YAML)
scripts/            rendu Windows + demo.ps1
tests/              preuve d'idempotence
docker/             control node Ansible pour Windows
```

## Démarrer sur Windows (sans routeur)

Python est déjà installé.

```powershell
cd $env:USERPROFILE\netauto-ansible-lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\render_intended.py
python -m pytest -q
```

Ou en une commande : `.\scripts\demo.ps1`

Tu obtiens :

- `intended/R1-PE-ABJ.cfg` — CLI Cisco (`hostname`, `vlan 10`, `ip address …`)
- `intended/R2-PE-ABJ.cfg` — CLI Huawei (`sysname`, `Vlanif10`, `undo shutdown`)

Relance `render_intended.py` autant de fois que tu veux : **même fichier**.

## Ansible réel (Docker ou WSL)

Ansible **n’est pas** un control node officiel sur Windows. En entretien, dis-le : c’est pour ça que le lab sépare *rendu* et *push*.

```powershell
docker build -f docker/Dockerfile -t netauto-ansible-lab .
docker run --rm -v ${PWD}:/work -w /work netauto-ansible-lab ansible-playbook --syntax-check playbooks/01-deploy-base.yml
docker run --rm -v ${PWD}:/work -w /work netauto-ansible-lab ansible-playbook playbooks/01-deploy-base.yml --check --diff
```

`--check` = dry-run (équivalent `terraform plan`). Avec `live: false`, les tasks SSH sont **skipped**, le template intended s’écrit quand même.

## Quand tu auras GNS3 / EVE-NG / CML

1. Remplace `ansible_host` par les IP de tes VM.
2. Copie `inventory/group_vars/all/vault.yml.example` → `vault.yml` puis `ansible-vault encrypt`.
3. Backup : `ansible-playbook playbooks/02-backup-config.yml -e live=true --ask-vault-pass`
4. Plan : `ansible-playbook playbooks/01-deploy-base.yml --check --diff -e live=true --ask-vault-pass`
5. Apply : enlève `--check` seulement après lecture du diff.

## Phrase CV (alignée sur ce dépôt)

> Automatisation réseau & IaC (Ansible) : playbooks multi-constructeurs (Cisco IOS, Huawei VRP) pour une config de base (hostname, VLAN, IP), source de vérité YAML, rôles idempotents (`state: merged`), garde-fou `--check` / `live=false`, secrets Vault, preuve d’idempotence par tests.

## Limites (honnêteté entretien)

- Pas de routeurs physiques dans ce repo : le SSH live est **opt-in**.
- `community.network` (Huawei CE) est en maintenance ; un cœur NE/AR Orange viserait `huaweidatacom.ne`.
- `state: merged` n’efface pas un VLAN oublié du YAML (prudent). Pour un standard strict, on passerait en `replaced` **par ressource**, jamais un `write erase`.

Lecture : [docs/pourquoi-iac.md](docs/pourquoi-iac.md)
