#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de test de connexion au robot NAO
Teste differents ports et methodes
"""

import socket
import sys

NAO_IP = "169.254.201.219"

print("=" * 60)
print("         TEST DE CONNEXION AU ROBOT NAO")
print("=" * 60)
print()

# Test de ping
print(f"1. Test de connectivite reseau vers {NAO_IP}...")
try:
    import subprocess
    result = subprocess.run(["ping", "-n", "1", NAO_IP], capture_output=True, timeout=5)
    if result.returncode == 0:
        print("   ✓ Le robot repond au ping")
    else:
        print("   ✗ Le robot ne repond pas au ping")
except Exception as e:
    print(f"   ✗ Erreur: {e}")

print()

# Test des ports communs de NAOqi
ports_to_test = [9559, 9503, 80, 443, 22]

print("2. Test des ports NAOqi courants...")
for port in ports_to_test:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((NAO_IP, port))
        if result == 0:
            print(f"   ✓ Port {port} OUVERT")
        else:
            print(f"   ✗ Port {port} ferme")
    except Exception as e:
        print(f"   ✗ Port {port} erreur: {e}")
    finally:
        sock.close()

print()
print("=" * 60)
print("INFORMATIONS:")
print("- Port 9559: NAOqi (service principal)")
print("- Port 9503: NAOqi (ancien port)")
print("- Port 80: Interface web")
print("- Port 22: SSH")
print()
print("Si aucun port n'est ouvert:")
print("1. Verifiez que le robot est allume (yeux bleus)")
print("2. Appuyez sur le bouton poitrine pour verifier l'etat")
print("3. Redemarrez le robot si necessaire")
print("4. Verifiez l'IP avec Choregraphe (Connection > Connect to...)")
print("=" * 60)
