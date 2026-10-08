# WHY ces tests : en entretien on te croit sur l'idempotence SI tu la PROUVES.
# Ici : 10 rendus = même SHA256. Et les CLI générés contiennent hostname/sysname + VLAN + IP.

from pathlib import Path
import hashlib
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from generate_antennes import generate  # noqa: E402
from render_intended import render_all  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_ten_renders_are_identical():
    generate()  # 50 antennes + 2 PE dans le même moteur de rendu
    # Premier rendu = référence
    files = render_all()
    first = {path.name: sha(path) for path in files}
    # Neuf autres : doivent matcher
    for _ in range(9):
        again = render_all()
        now = {path.name: sha(path) for path in again}
        assert now == first, "Idempotence cassée : le YAML a produit un CLI différent"


def test_cisco_cli_has_hostname_vlan_and_ip():
    render_all()
    text = (ROOT / "intended" / "R1-PE-ABJ.cfg").read_text(encoding="utf-8")
    assert "hostname R1-PE-ABJ" in text
    assert "vlan 10" in text
    assert "name DATA" in text
    assert "ip address 10.10.10.1 255.255.255.0" in text
    assert "ip address 10.0.0.1 255.255.255.252" in text


def test_huawei_cli_has_sysname_vlanif_and_ip():
    render_all()
    text = (ROOT / "intended" / "R2-PE-ABJ.cfg").read_text(encoding="utf-8")
    assert "sysname R2-PE-ABJ" in text
    assert "vlan 20" in text
    assert "interface Vlanif10" in text
    assert "ip address 10.10.10.2 255.255.255.0" in text
    assert "undo shutdown" in text


def test_generator_is_idempotent_and_has_50_unique_ips():
    first_csv, first_yml = generate()
    h1 = sha(first_csv) + sha(first_yml)
    generate()
    generate()
    assert sha(first_csv) + sha(first_yml) == h1
    rows = (ROOT / "data" / "antennes-bobo.csv").read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 51  # 1 header + 50 sites
    text = (ROOT / "inventory" / "antennes.yml").read_text(encoding="utf-8")
    assert text.count("lan_ipv4:") == 50  # une IP LAN déclarée par site (pas 50 fois la même)
    ips = [line.split(",")[-1] for line in rows[1:]]
    assert len(set(ips)) == 50  # cause racine évitée : pas d'IP LAN en double
    assert "10.0.10.1/24" not in text  # le /24 "exemple unique" n'est PAS recopié x50


def test_antenne_001_cli_has_ssh_vlan_and_unique_ip():
    generate()
    render_all()
    text = (ROOT / "intended" / "ANTENNE-BOBO-001.cfg").read_text(encoding="utf-8")
    assert "hostname ANTENNE-BOBO-001" in text
    assert "vlan 10" in text
    assert "name DATA_TRAFFIC" in text
    assert "interface GigabitEthernet0/0" in text
    assert "ip address 10.10.1.1 255.255.255.0" in text
    assert "ip ssh version 2" in text
    assert "transport input ssh" in text
