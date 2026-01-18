#!/usr/bin/env python3
import subprocess
import re
import os
import sys

def executar_comando(comando):
    resultado = subprocess.run(comando, capture_output=True, text=True)
    return resultado.stdout

def restaurar_e_limpar_perfeito():
    if os.geteuid() != 0:
        print("❌ Rode como SUDO!")
        sys.exit(1)

    print("🛠️ Iniciando Faxina Geral no Boot do Xeon...")

    # 1. Limpeza Profunda: Procura genéricos E nomes antigos nossos
    saida_atual = executar_comando(["efibootmgr"])
    
    # Este padrão agora busca por UEFI OS, CachyOS ou Hackintosh
    padrao = r"Boot([0-9a-fA-F]{4})\*? (UEFI OS|CachyOS|Hackintosh)"
    entradas_para_remover = re.findall(padrao, saida_atual)

    for id_boot, nome in entradas_para_remover:
        print(f"🗑️ Removendo {nome}: Boot{id_boot}")
        subprocess.run(["efibootmgr", "-b", id_boot, "-B"], capture_output=True)

    # 2. Criação Única
    print("⌛ Configurando entradas oficiais no NVMe...")
    # CachyOS
    subprocess.run(["efibootmgr", "-c", "-d", "/dev/nvme0n1", "-p", "2", "-L", "CachyOS", "-l", "\\EFI\\systemd\\systemd-bootx64.efi"], capture_output=True)
    # Hackintosh
    subprocess.run(["efibootmgr", "-c", "-d", "/dev/nvme0n1", "-p", "4", "-L", "Hackintosh", "-l", "\\EFI\\BOOT\\BOOTX64.EFI"], capture_output=True)

    print("\n✅ Setup finalizado! Agora sua lista está 100% limpa.")
    print(executar_comando(["efibootmgr"]))

if __name__ == "__main__":
    restaurar_e_limpar_perfeito()
