# Les modules du lab (briques, pas de magie)

Ansible ne « pilote pas un routeur ». Il appelle des **modules**. Chaque module = une API avec un contrat (idempotent si tu respectes le format running-config).

## Module 1 — `cisco.ios.ios_config`

**Pourquoi** : coller des **lignes CLI** comme dans `configure terminal`. Utile quand il n’y a pas (ou pas simple) de resource module : SSH, VTY, knobs exotiques.

```yaml
- name: Configurer le hostname du routeur
  cisco.ios.ios_config:
    lines:
      - hostname ANTENNE-BOBO-001
```

C’est l’équivalent de SSH → `conf t` → `hostname ANTENNE-BOBO-001`.

**Piège d’idempotence** : `host ANTENNE-…` (abrégé) ≠ la ligne du `show run` (`hostname …`) → Ansible croit que ça change **à chaque run**. Toujours la forme longue.

Dans le lab, le hostname est `hostname {{ hostname }}` pour que les 50 sites ne soient pas en dur dans le playbook.

## Module 2 — `cisco.ios.ios_vlans`

**Pourquoi** : un VLAN n’est pas « une commande », c’est un **objet** (id, nom, active/suspend). Le resource module déclare l’état.

```yaml
- name: Créer le VLAN 10 pour le trafic data
  cisco.ios.ios_vlans:
    config:
      - vlan_id: 10
        name: DATA_TRAFFIC
        state: active
    state: merged
```

**Pourquoi `merged`** : on **ajoute/aligne** VLAN 10. On ne supprime pas un VLAN de management déjà présent sur le site (`replaced` le ferait pour la ressource VLAN).

**Pourquoi VLAN 10** : isoler le data. Un VLAN voix 20 (autre campagne) ne « voit » pas le data sans routage / ACL — segmentation = sécu + QoS.

## Module 3 — `cisco.ios.ios_interfaces` … et le piège IP

**Pourquoi** : le **port physique** (description, shutdown, MTU, speed). C’est le câble vers l’antenne 4G.

```yaml
- name: Configurer l'interface GigabitEthernet0/0
  cisco.ios.ios_interfaces:
    config:
      - name: GigabitEthernet0/0
        description: "Lien vers l'antenne 4G"
        enabled: true
    state: merged
```

### Cause racine d’une erreur fréquente

On voit souvent ceci (à **ne pas** copier tel quel) :

```yaml
# FAUX schéma : ipv4 n'appartient PAS à ios_interfaces
ipv4:
  - address: 10.0.10.1/24
```

- **Cause** : confusion couche 2 (le port) / couche 3 (l’adresse).
- **Symptôme** : erreur de module, ou l’IP n’est jamais posée, et « ça marche en lab » seulement si tu as aussi collé l’IP ailleurs.
- **Correctif** : `cisco.ios.ios_l3_interfaces` :

```yaml
- name: IP LAN sur Gi0/0
  cisco.ios.ios_l3_interfaces:
    config:
      - name: GigabitEthernet0/0
        ipv4:
          - address: "{{ lan_ipv4 }}"
    state: merged
```

Sans IP **unique**, l’antenne n’a pas d’identité sur le LAN. Sans `enabled: true`, le port reste `shutdown`.

## Module 4 — `ansible.builtin.debug`

**Pourquoi** : ce n’est pas du réseau. C’est ton **instrument de bord**. Sur 50 hôtes, sans message, tu ne sais pas quelle cellule a fini.

```yaml
- name: Afficher un message de succès
  ansible.builtin.debug:
    msg: "Configuration du routeur {{ inventory_hostname }} terminée avec succès !"
```

`{{ inventory_hostname }}` = le nom dans l’inventaire (`ANTENNE-BOBO-017`), pas un texte figé.

## Tableau récap (à ressortir en entretien)

| Module | Tu déclares | Analogie CLI |
|---|---|---|
| `ios_config` | lignes | `conf t` + commandes |
| `ios_vlans` | objets VLAN | `vlan 10` / `name` |
| `ios_interfaces` | port (L2) | `description`, `no shutdown` |
| `ios_l3_interfaces` | IP (L3) | `ip address …` |
| `debug` | un message | `print` / journal d’exploit |
