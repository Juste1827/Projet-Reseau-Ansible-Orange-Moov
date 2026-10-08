# Pourquoi l'IaC réseau (avant le comment)

## Le problème que tu vends en entretien

Configurer un PE Cisco à la main, puis le Huawei voisin « pareil » à l’œil, ça diverge en 3 changements. Chez un opérateur (Orange, Moov), l’écart Cisco/Huawei est quotidien : **même service (VLAN DATA/VOICE, IP de SVI), deux CLI**.

Ansible n’est pas « un script qui colle des commandes ». C’est :

1. **Une source de vérité** (YAML) : *quoi* (hostname, VLAN 10, `10.10.10.1/24`)
2. **Une projection constructeur** (rôle + template) : *comment* (`hostname` vs `sysname`)
3. **Un moteur idempotent** : relancer ne « re-tape » pas, ça **aligne** l’état

## Pourquoi pas juste Paramiko / un .txt de commandes ?

| Approche | Relancer 10 fois | Multi-vendor | Audit |
|---|---|---|---|
| Coller du CLI | 10 fois les mêmes commandes (risque, bruit, ordre) | if/else partout | difficile |
| Ansible resource modules | compare au running-config | un rôle par OS | logs + Git + `--check` |

## Pourquoi `merged` et pas `replaced`

- **merged** : pose VLAN 10 et 20, **laisse** un VLAN 99 de management déjà là.
- **replaced** : le YAML devient la vérité **totale** de la ressource — un VLAN oublié disparaît.

En accès télécom, **merged** est le défaut prudent. `replaced` se justifie sur un lab ou un standard stricte d’opérateur.

## Pourquoi `--check` avant le push

Le running-config d’un PE n’est pas un fichier Git. `--check` + `--diff` = tu **lis** le delta comme un merge request, puis tu appliques. C’est le même réflexe que `terraform plan`.

## Pourquoi Windows + pas de routeur, ce n’est pas un faux projet

Ansible control node = Linux. Toi tu es sur Windows. Donc :

- le **cœur IaC** (inventaire, templates, idempotence) tourne en Python **ici**
- le **vrai Ansible** tourne en Docker/WSL/CI (syntax-check, lint)
- le **SSH live** attend GNS3/EVE-NG (`-e live=true`)

Un recruteur sérieux comprend cette séparation. C’est même plus honnête que de prétendre SSH vers `192.0.2.11`.
