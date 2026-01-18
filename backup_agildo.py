#!/usr/bin/env python3
import customtkinter as ctk
import shutil
import os
import threading
import time
from datetime import datetime
from tkinter import messagebox

# Configuração Visual
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class BackupApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema de Backup Agildo - Modo Seguro")
        self.geometry("1400x900")
        self.configure(fg_color="#0f0f0f")

        # --- TENTATIVA DE DESCOBRIR A PASTA CORRETA ---
        self.pasta_origem = "/home/agildo/ScriptsAgildo"
        self.pasta_destino = self.definir_destino_correto()

        # --- TÍTULO ---
        self.lbl_titulo = ctk.CTkLabel(self, text="💾 BACKUP BLINDADO", 
                                       font=("Roboto", 40, "bold"), text_color="#3498db")
        self.lbl_titulo.pack(pady=(40, 10))

        # Mostra na tela para conferência
        self.lbl_origem = ctk.CTkLabel(self, text=f"Origem: {self.pasta_origem}", font=("Roboto", 16))
        self.lbl_origem.pack()
        
        self.lbl_destino = ctk.CTkLabel(self, text=f"Destino: {self.pasta_destino}", font=("Roboto", 16), text_color="#2ecc71")
        self.lbl_destino.pack(pady=(0, 40))

        # --- STATUS ---
        self.frame_status = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=15, width=800, height=150)
        self.frame_status.pack(pady=20)

        self.lbl_status = ctk.CTkLabel(self.frame_status, text="Aguardando...", 
                                       font=("Roboto", 24), text_color="white")
        self.lbl_status.place(relx=0.5, rely=0.3, anchor="center")

        self.barra = ctk.CTkProgressBar(self.frame_status, width=600)
        self.barra.set(0)
        self.barra.place(relx=0.5, rely=0.6, anchor="center")

        # --- BOTÃO ---
        self.btn_backup = ctk.CTkButton(self, text="INICIAR BACKUP", 
                                        font=("Roboto", 24, "bold"),
                                        fg_color="#2ecc71", hover_color="#27ae60",
                                        height=80, width=400,
                                        command=self.iniciar_backup)
        self.btn_backup.pack(pady=50)

    def definir_destino_correto(self):
        # Lista de tentativas manuais
        possibilidades = [
            "/home/agildo/Área de trabalho",  # Com 't' minúsculo (O CORRETO)
            "/home/agildo/Área de Trabalho",  # Com 'T' maiúsculo
            "/home/agildo/Desktop",           # Inglês
            "/home/agildo"                    # Último caso: pasta pessoal
        ]
        
        for p in possibilidades:
            if os.path.exists(p):
                return p
        
        return "/tmp" # Se nada existir (muito difícil)

    def iniciar_backup(self):
        if not os.path.exists(self.pasta_origem):
            messagebox.showerror("Erro Fatal", f"A pasta de scripts não existe:\n{self.pasta_origem}")
            return

        self.btn_backup.configure(state="disabled", text="TRABALHANDO...")
        self.barra.set(0)
        threading.Thread(target=self.processo_backup).start()

    def processo_backup(self):
        try:
            # Animação
            for i in range(1, 80):
                self.lbl_status.configure(text=f"Compactando... {i}%")
                self.barra.set(i/100)
                time.sleep(0.01)

            data_hora = datetime.now().strftime("%d-%m-%Y_%H-%M")
            # Define o caminho completo do arquivo zip
            nome_arquivo_base = os.path.join(self.pasta_destino, f"Backup_Agildo_{data_hora}")

            # CRIA O ZIP
            shutil.make_archive(nome_arquivo_base, 'zip', self.pasta_origem)

            # SUCESSO
            self.barra.set(1)
            self.lbl_status.configure(text="✅ SUCESSO!", text_color="#2ecc71")
            self.btn_backup.configure(text="FEITO (Pode Fechar)", fg_color="#333")
            
            messagebox.showinfo("Sucesso", f"Backup salvo em:\n{self.pasta_destino}\n\nConfira se o arquivo ZIP apareceu lá!")

        except PermissionError:
            self.lbl_status.configure(text="❌ ERRO DE PERMISSÃO!", text_color="red")
            self.btn_backup.configure(state="normal", text="TENTAR NOVAMENTE")
            messagebox.showerror("Atenção", "Erro: PERMISSION DENIED\n\nVocê precisa rodar este comando no terminal para liberar os arquivos:\n\nsudo chown -R agildo:agildo /home/agildo/ScriptsAgildo")

        except Exception as e:
            self.lbl_status.configure(text="❌ ERRO!", text_color="red")
            self.btn_backup.configure(state="normal", text="TENTAR NOVAMENTE")
            messagebox.showerror("Detalhe do Erro", str(e))

if __name__ == "__main__":
    app = BackupApp()
    app.mainloop()
