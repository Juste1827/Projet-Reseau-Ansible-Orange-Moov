# WHY ce script existe : Ansible n'est PAS un control node officiel sur Windows.
# Tu peux quand même DÉMONTRER l'IaC : YAML (vérité) -> template (CLI vendor) -> fichier .cfg.
# Exécuter 10 fois = 10 fichiers identiques (idempotence du rendu, sans aucun routeur).

"""Génère intended/*.cfg depuis l'inventaire YAML + templates Jinja2."""

from __future__ import annotations  # annotations modernes (list[str], etc.)

import hashlib  # pour prouver que 2 rendus sont binaires-identiques
import sys  # exit codes + import du filter plugin
from pathlib import Path  # chemins Windows-friendly (C:\...)

import yaml  # lire inventory/*.yml
from jinja2 import Environment, FileSystemLoader, StrictUndefined  # moteur des templates .j2

# Racine du dépôt = parent du dossier scripts/
ROOT = Path(__file__).resolve().parent.parent

# Permettre : from filter_plugins.cidr import ...
sys.path.insert(0, str(ROOT))
from filter_plugins.cidr import cidr_to_address, cidr_to_netmask  # même conversion qu'Ansible


def load_yaml(path: Path) -> dict:
    # WHY : un fichier YAML = un dict Python. Si le fichier manque, on veut une erreur CLAIRE.
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)  # safe_load : refuse les objets Python arbitraires (sécurité)
    return data or {}  # fichier vide => dict vide, pas None


def deep_merge(base: dict, extra: dict) -> dict:
    # WHY : Ansible fusionne all < group < host. On reproduit ça : host_vars gagne toujours.
    merged = dict(base)  # copie pour ne pas muter l'original
    for key, value in extra.items():
        merged[key] = value  # remplacement simple (suffisant pour ce lab)
    return merged


def iter_hosts(inventory: dict):
    # WHY : on parcourt all.children.<groupe>.hosts pour coller au vrai inventaire Ansible.
    children = inventory.get("all", {}).get("children", {})
    for group_name, group_body in children.items():
        hosts = (group_body or {}).get("hosts") or {}
        for host_name, host_inline in hosts.items():
            yield group_name, host_name, host_inline or {}


def build_host_context(group_name: str, host_name: str, host_inline: dict) -> dict:
    # 1) group_vars/all.yml = politique commune (VLAN métier, live, site)
    ctx = load_yaml(ROOT / "inventory" / "group_vars" / "all.yml")
    # 2) group_vars/<cisco|huawei>.yml = dialecte constructeur
    group_file = ROOT / "inventory" / "group_vars" / f"{group_name}.yml"
    if group_file.exists():
        ctx = deep_merge(ctx, load_yaml(group_file))
    # 3) IP inline dans hosts.yml (ansible_host)
    ctx = deep_merge(ctx, host_inline)
    # 4) host_vars/<hostname>.yml = vérité de CET équipement
    host_file = ROOT / "inventory" / "host_vars" / f"{host_name}.yml"
    if host_file.exists():
        ctx = deep_merge(ctx, load_yaml(host_file))
    ctx["inventory_hostname"] = host_name  # comme Ansible
    return ctx


def make_jinja_env() -> Environment:
    # WHY StrictUndefined : une variable oubliée = erreur, pas un champ vide poussé en prod.
    env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        undefined=StrictUndefined,
        trim_blocks=True,  # évite des lignes vides parasites (aide l'idempotence du fichier)
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["cidr_to_address"] = cidr_to_address  # mêmes filtres que filter_plugins/cidr.py
    env.filters["cidr_to_netmask"] = cidr_to_netmask
    return env


def template_for_vendor(vendor: str) -> str:
    # WHY : un vendor = un template. Ajouter Nokia = ajouter un .j2, pas un if dans 200 lignes.
    mapping = {
        "cisco": "cisco_ios_base.j2",
        "huawei": "huawei_vrp_base.j2",
    }
    if vendor not in mapping:
        raise ValueError(f"Vendor inconnu {vendor!r}. Attendu : cisco|huawei")
    return mapping[vendor]


def iter_all_inventory_hosts():
    # WHY deux fichiers : PE lab (hosts.yml) + campagne 4G (antennes.yml), sans tout mélanger.
    files = [
        ROOT / "inventory" / "hosts.yml",
        ROOT / "inventory" / "antennes.yml",
    ]
    for path in files:
        if path.exists():  # antennes.yml n'existe qu'après generate_antennes.py
            yield from iter_hosts(load_yaml(path))


def render_all() -> list[Path]:
    env = make_jinja_env()
    out_dir = ROOT / "intended"
    out_dir.mkdir(exist_ok=True)  # crée le dossier si besoin (Windows OK)
    written: list[Path] = []
    for group_name, host_name, host_inline in iter_all_inventory_hosts():
        ctx = build_host_context(group_name, host_name, host_inline)
        vendor = ctx.get("vendor")
        # WHY intended_template : une antenne 4G n'est PAS un PE (pas de VLAN voix / P2P).
        tpl_name = ctx.get("intended_template") or template_for_vendor(vendor)
        rendered = env.get_template(tpl_name).render(**ctx)
        dest = out_dir / f"{host_name}.cfg"
        dest.write_text(rendered, encoding="utf-8", newline="\n")  # newline=\n : même hash Windows/Linux
        written.append(dest)
        digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:12]
        print(f"OK  {host_name:20}  vendor={vendor:6}  sha256={digest}  -> {dest.relative_to(ROOT)}")
    return written


if __name__ == "__main__":
    # WHY : python scripts/render_intended.py depuis la racine OU n'importe où (ROOT est absolu)
    render_all()
