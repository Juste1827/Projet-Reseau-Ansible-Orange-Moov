# De A à Z : 50 antennes 4G (scénario Orange / Moov)

## 1. Pourquoi (le problème métier)

L’opérateur déploie **50 nouvelles antennes 4G** en zone rurale (ici : région de Bobo).
Chaque site a un **routeur d’accès** à configurer :

| Intention | Exemple site 001 | Les 50 sites |
|---|---|---|
| Hostname unique | `ANTENNE-BOBO-001` | `…-002` … `…-050` |
| VLAN data | VLAN 10 `DATA_TRAFFIC` | **identique** (politique) |
| Interface LAN | `GigabitEthernet0/0` | identique (même modèle de boîte) |
| IP LAN | `10.10.1.1/24` | **unique** `10.10.<id>.1/24` |
| Accès | SSH v2, Telnet interdit | identique (sécurité)

### Erreur à ne pas commettre (cause racine)

L’énoncé « tous en `10.0.10.1/24` » décrit **un** site, pas la campagne.
Si 50 routeurs ont la **même IP**, les paquets ne savent plus à qui parler : incident réseau, pas un détail de lab.
Le playbook ne « multiplie » pas une IP : il lit **une ligne par antenne** dans le plan (`data/antennes-bobo.csv`).

### Combien de temps

| Méthode | Ordre de grandeur |
|---|---|
| CLI à la main | 50 × 15 min ≈ **12 h 30** + fautes de frappe |
| Ansible (live, `serial: 10`) | minutes, **même** playbook relancé = already in sync |

## 2. Comment (la chaîne IaC)

```
Excel/CSV IPAM          Inventaire Ansible           Modules IOS
data/antennes-bobo.csv → inventory/antennes.yml → playbooks/04-antennes-4g.yml
         ↑                        ↑                         ↓
 scripts/generate_antennes.py   group_vars/antennes_4g.yml  intended/ANTENNE-BOBO-xxx.cfg
```

1. **Plan** : `python scripts/generate_antennes.py` (idempotent).
2. **Démo Windows sans boîte** : `python scripts/render_intended.py` → 50 fichiers CLI.
3. **Ansible** (Docker/WSL) :
   ```bash
   ansible-playbook playbooks/04-antennes-4g.yml --check --diff
   ```
4. **Plus tard, lab GNS3** : `-e live=true --ask-vault-pass` après backup.

## 3. Pourquoi `serial: 10`

Pousser 50 PE/accès d’un coup, c’est une fenêtre de change unique. `serial: 10` = **vagues** de 10 (réflexe opérateur : canary, puis le reste).

## 4. Pourquoi `live: false` par défaut

Sans ça, un `ansible-playbook` depuis ton PC viserait `192.0.2.x` (doc) ou pire une IP réelle mal collée. Le défaut **n’ouvre pas SSH**.

## 5. Ce que tu dis en entretien

> « La source de vérité c’est le plan d’adressage. Ansible n’invente pas les hostname. Un rôle, 50 hôtes. `ios_config` pour le CLI SSH, `ios_vlans` / `ios_interfaces` / `ios_l3_interfaces` pour l’état. Relancer le playbook est sûr grâce à `state: merged` et aux commandes non abrégées. »
