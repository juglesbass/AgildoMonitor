#!/usr/bin/env python3
import os
import subprocess

def limpar_sistema():
    print("🚀 Iniciando a Faxina no seu CachyOS...\n")

    # 1. Limpando cache de pacotes (mantém apenas as 2 últimas versões por segurança)
    print("📦 Organizando o cache de pacotes (Pacman)...")
    subprocess.run(['sudo', 'paccache', '-r', '-k', '2'])

    # 2. Limpando logs do sistema (mantém apenas os últimos 2 dias)
    print("\n📜 Diminuindo o tamanho dos logs do sistema...")
    subprocess.run(['sudo', 'journalctl', '--vacuum-time=2d'])

    # 3. Limpando lixo da pasta .cache do usuário
    print("\n📂 Removendo arquivos temporários da sua conta...")
    os.system('rm -rf ~/.cache/*')

    print("\n✅ Faxina concluída! Seu sistema está mais leve agora.")

if __name__ == "__main__":
    limpar_sistema()
