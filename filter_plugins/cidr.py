# WHY un filter plugin : le YAML stocke 10.10.10.1/24 (lisible, unique).
# Le CLI Cisco/Huawei veut "10.10.10.1 255.255.255.0".
# On convertit AU RENDU, on ne duplique pas masque + CIDR dans l'inventaire (anti-DRY, source d'erreur).

"""Filtres Jinja : CIDR -> adresse / masque décimal."""

import ipaddress  # stdlib Python : pas de pip supplémentaire


def cidr_to_address(value):
    # WHY: "10.10.10.1/24" -> "10.10.10.1" (ce que "ip address" attend)
    network = ipaddress.ip_interface(str(value))  # ip_interface accepte host+prefix
    return str(network.ip)


def cidr_to_netmask(value):
    # WHY: "10.10.10.1/24" -> "255.255.255.0" (forme running-config Cisco/VRP)
    network = ipaddress.ip_interface(str(value))
    return str(network.network.netmask)


class FilterModule(object):
    # WHY: Ansible charge cette classe automatiquement depuis filter_plugins/
    def filters(self):
        return {
            "cidr_to_address": cidr_to_address,
            "cidr_to_netmask": cidr_to_netmask,
        }
