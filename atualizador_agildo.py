#!/usr/bin/env python3
import customtkinter as ctk
import subprocess
import threading
import os
import sys

# Configuração Visual
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green") 

class AtualizadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuração para TV 55"
        self.title("Atualizador Universal CachyOS")
        self.geometry("1700x1200")
        self.configure(fg_color="#0a0a0a")

        # --- CABEÇALHO ---
        self.lbl_titulo = ctk.CTkLabel(self, text="🔄 ATUALIZADOR DE SISTEMA", 
                                       font=("Roboto", 40, "bold"), text_color="#2ecc71")
        self.lbl_titulo.pack(pady=(30, 10))

        self.lbl_sub = ctk.CTkLabel(self, text="CachyOS • Pacman • Flatpak • Limpeza", 
                                    font=("Roboto", 18), text_color="gray")
        self.lbl_sub.pack(pady=(0, 20))

        # --- TERMINAL DE LOG ---
        # AQUI MUDOU: state="normal" para não precisar destravar toda hora
        self.log_box = ctk.CTkTextbox(self, width=1400, height=750, font=("Consolas", 14))
        self.log_box.pack(pady=10)
        self.log_box.insert("0.0", ">>> Aguardando comando para iniciar...\n")
        self.log_box.configure(state="disabled") # Começa travado

        # --- BOTÃO ---
        self.btn_atualizar = ctk.CTkButton(self, text="ATUALIZAR TUDO AGORA", 
                                           font=("Roboto", 24, "bold"),
                                           height=80, width=400,
                                           fg_color="#2ecc71", hover_color="#27ae60",
                                           command=self.iniciar_atualizacao)
        self.btn_atualizar.pack(pady=30)

        if os.geteuid() != 0:
            self.log_sistema("⚠️ AVISO: Execute este programa como ROOT (kdesu) para funcionar!", "red")
            self.btn_atualizar.configure(state="disabled", fg_color="#555")

    # Função simplificada para escrever sem piscar
    def log_sistema(self, texto, cor=None):
        # Apenas insere. O controle de travar/destravar fica no processo principal
        self.log_box.insert("end", texto + "\n")
        self.log_box.see("end") 

    def iniciar_atualizacao(self):
        self.btn_atualizar.configure(state="disabled", text="TRABALHANDO...")
        
        # DESTRAVA O TERMINAL UMA VEZ SÓ
        self.log_box.configure(state="normal")
        
        threading.Thread(target=self.processo_completo).start()

    def rodar_comando(self, comando, descricao):
        self.log_sistema(f"\n--- {descricao} ---")
        self.log_sistema(f"Executando: {comando}")
        
        try:
            # Bufsize=1 ajuda a linha aparecer assim que é gerada
            processo = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            
            for linha in processo.stdout:
                self.log_sistema(linha.strip())
            
            processo.wait()
            
            if processo.returncode == 0:
                self.log_sistema(f"✅ {descricao} CONCLUÍDO!", "green")
                return True
            else:
                self.log_sistema(f"❌ ERRO em {descricao}.", "red")
                return False
        except Exception as e:
            self.log_sistema(f"Erro Crítico: {e}")
            return False

    def processo_completo(self):
        # 1. Atualizar banco de dados
        self.rodar_comando("pacman -Sy", "Sincronizando Repositórios")

        # 2. Atualizar Sistema
        sucesso_sys = self.rodar_comando("pacman -Su --noconfirm", "Atualizando Pacotes (CachyOS)")

        # 3. Atualizar Flatpaks
        self.rodar_comando("flatpak update -y", "Atualizando Aplicativos (Flatpak)")

        # 4. Limpeza
        self.rodar_comando("paccache -rk1", "Limpando Cache Antigo")

        self.log_sistema("\n=========================================")
        if sucesso_sys:
            self.log_sistema("✨ PROCESSO FINALIZADO COM SUCESSO! ✨")
            self.btn_atualizar.configure(text="SISTEMA ATUALIZADO (Pode Fechar)", fg_color="#333")
        else:
            self.log_sistema("⚠️ HOUVE ERROS. Verifique o log acima.")
            self.btn_atualizar.configure(state="normal", text="TENTAR NOVAMENTE")
        
        # TRAVA O TERMINAL NO FINAL (Para ninguém digitar sem querer)
        self.log_box.configure(state="disabled")

if __name__ == "__main__":
    app = AtualizadorApp()
    app.mainloop()
