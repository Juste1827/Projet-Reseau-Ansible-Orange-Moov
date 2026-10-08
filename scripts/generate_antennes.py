# WHY ce script : tu ne tapes PAS 50 blocs YAML à la main (c'est exactement l'erreur
# que l'IaC doit supprimer). Une boucle produit l'inventaire depuis un plan d'adressage.
# Relancer 10 fois = le même CSV + le même YAML (idempotence du générateur).

"""Génère data/antennes-bobo.csv et inventory/antennes.yml (50 sites ruraux)."""

from __future__ import annotations  # list[dict] etc.

import csv  # format "fichier d'ingénierie" que les équipes IPAM comprennent
from pathlib import Path  # chemins Windows

ROOT = Path(__file__).resolve().parent.parent  # racine du dépôt
NB_SITES = 50  # le volume du scénario Orange/Moov (campagne 4G rurale)
ZONE = "BOBO"  # Bobo-Dioulasso — hostname ANTENNE-BOBO-001


def plan_sites() -> list[dict]:
    # WHY une liste de dict : une ligne = une antenne = une vérité.
    # ERREUR MÉTIER à ne PAS copier : mettre 10.0.10.1/24 sur les 50 routeurs.
    # Cause racine : collision d'IP = pas de routage, blackhole, ticket incident.
    # Correctif : 10.10.<id>.1/24 unique par site (LAN antenne).
    sites = []  # accumulateur
    for idx in range(1, NB_SITES + 1):  # 1..50 inclus
        sites.append(
            {
                "id": idx,  # numéro d'ingénierie
                "hostname": f"ANTENNE-{ZONE}-{idx:03d}",  # :03d = 001, 002, ... 050
                "ansible_host": f"192.0.2.{100 + idx}",  # mgmt doc RFC 5737 : .101 .. .150
                "lan_interface": "GigabitEthernet0/0",  # port vers l'eNodeB / antenne
                "lan_ipv4": f"10.10.{idx}.1/24",  # SVI/LAN unique par village
            }
        )
    return sites


def write_csv(sites: list[dict]) -> Path:
    # WHY CSV : en entretien tu dis "le plan vient de l'Excel IPAM, Ansible n'invente pas les IP".
    dest = ROOT / "data" / "antennes-bobo.csv"
    dest.parent.mkdir(exist_ok=True)  # crée data/ si besoin
    fieldnames = ["id", "hostname", "ansible_host", "lan_interface", "lan_ipv4"]
    with dest.open("w", encoding="utf-8", newline="\n") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()  # première ligne = noms de colonnes
        writer.writerows(sites)  # 50 lignes métier
    return dest


def write_inventory(sites: list[dict]) -> Path:
    # WHY on écrit le YAML "à la main" (pas yaml.dump) : commentaires pédagogiques + Git diff lisible.
    dest = ROOT / "inventory" / "antennes.yml"
    lines = [
        "---",
        "# FICHIER GÉNÉRÉ par scripts/generate_antennes.py — ne pas éditer à la main.",
        "# Source de vérité : data/antennes-bobo.csv (plan d'adressage campagne 4G).",
        "# WHY un groupe dédié antennes_4g (PAS cisco) : le playbook PE (01-deploy-base)",
        "# ne doit JAMAIS configurer une antenne avec la conf d'un routeur de cœur.",
        "",
        "all:",
        "  children:",
        "    antennes_4g:",
        "      hosts:",
    ]
    for site in sites:
        # 4 espaces d'indent YAML sous hosts:  (ansible inventory)
        lines.append(f"        {site['hostname']}:")
        lines.append(f"          ansible_host: {site['ansible_host']}")
        lines.append(f"          hostname: {site['hostname']}")
        lines.append(f"          lan_interface: {site['lan_interface']}")
        lines.append(f"          lan_ipv4: {site['lan_ipv4']}")
    lines.append("")  # newline finale = diffs Git stables
    dest.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return dest


def generate() -> tuple[Path, Path]:
    sites = plan_sites()  # calcule le plan
    csv_path = write_csv(sites)  # fichier d'ingénierie
    yml_path = write_inventory(sites)  # fichier qu'Ansible lit
    print(f"OK  {len(sites)} sites -> {csv_path.relative_to(ROOT)} + {yml_path.relative_to(ROOT)}")
    return csv_path, yml_path


if __name__ == "__main__":
    generate()
