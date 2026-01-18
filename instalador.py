import os

# O código PERFEITO da sua Central está guardado dentro desta variável
codigo_da_central = r"""#!/usr/bin/env python3
import customtkinter as ctk
import subprocess
import os
import shutil
from datetime import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class CentralAgildoUltimate(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Agildo Systems - Command Center")
        self.geometry("1500x1300") 
        self.configure(fg_color="#050505")
        self.script_dir = "/home/agildo/ScriptsAgildo"

        self.header = ctk.CTkFrame(self, fg_color="#0a0a0a", height=180, corner_radius=0)
        self.header.pack(fill="x", pady=(0, 30))

        self.lbl_title = ctk.CTkLabel(self.header, text="🚀 CENTRAL DE COMANDO", 
                                      font=("Roboto", 48, "bold"), text_color="#3498db")
        self.lbl_title.place(relx=0.5, rely=0.4, anchor="center")
        
        self.lbl_subtitle = ctk.CTkLabel(self.header, text="AGILDO SYSTEMS  •  CACHYOS  •  MANAUS", 
                                      font=("Roboto", 18, "bold"), text_color="#666")
        self.lbl_subtitle.place(relx=0.5, rely=0.75, anchor="center")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(pady=10, padx=80, fill="both", expand=True)

        self.criar_smart_card("📊", "MONITOR DE HARDWARE", "Vigiar Xeon E5-2640 e RX 6600", "#2ecc71", self.abrir_hardware)
        self.criar_smart_card("💨", "CONTROLE DE VENTOINHA", "Curvas Térmicas e Modo Turbo", "#e74c3c", self.abrir_fan)
        self.criar_smart_card("🚑", "FAXINA DE BOOT (UEFI)", "Reparar Entradas de Inicialização", "#e67e22", self.abrir_boot)
        self.criar_smart_card("🧹", "LIMPEZA DO SISTEMA", "Otimizar NVMe e Cache (Terminal)", "#f1c40f", self.abrir_limpeza)
        self.criar_smart_card("🎮", "GAME BOOSTER (PROTON)", "Lançador de Jogos Windows/Steam", "#9b59b6", self.abrir_proton)
        self.criar_smart_card("💾", "BACKUP DE SEGURANÇA", "Salvar Scripts em ZIP na Área de Trabalho", "#3498db", self.fazer_backup)

        self.lbl_footer = ctk.CTkLabel(self, text="SISTEMA PRONTO PARA JOGAR | TV TCL 55\"", 
                                       text_color="#333", font=("Roboto", 14, "bold"))
        self.lbl_footer.pack(side="bottom", pady=20)

    def criar_smart_card(self, icone, titulo, sub, cor_destaque, comando):
        card = ctk.CTkFrame(self.container, fg_color="#181818", height=120, corner_radius=15, border_width=2, border_color="#222")
        card.pack(pady=12, fill="x")
        card.pack_propagate(False) 

        ctk.CTkLabel(card, text=icone, font=("Roboto", 45)).pack(side="left", padx=(30, 20)) 
        
        frame_texto = ctk.CTkFrame(card, fg_color="transparent")
        frame_texto.pack(side="left", fill="y", pady=20)
        ctk.CTkLabel(frame_texto, text=titulo, font=("Roboto", 26, "bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(frame_texto, text=sub, font=("Roboto", 16), text_color="#AAAAAA").pack(anchor="w")
        
        lbl_seta = ctk.CTkLabel(card, text="▶", font=("Roboto", 20), text_color="#333")
        lbl_seta.pack(side="right", padx=30)

        def ao_entrar(e):
            card.configure(border_color=cor_destaque, fg_color="#202020")
            lbl_seta.configure(text_color=cor_destaque)
        def ao_sair(e):
            card.configure(border_color="#222", fg_color="#181818")
            lbl_seta.configure(text_color="#333")
        def ao_clicar(e):
            comando()

        for widget in card.winfo_children() + [card]:
            widget.bind("<Enter>", ao_entrar)
            widget.bind("<Leave>", ao_sair)
            widget.bind("<Button-1>", ao_clicar)

    def rodar_script(self, nome_arquivo, em_terminal=False):
        caminho = os.path.join(self.script_dir, nome_arquivo)
        if os.path.exists(caminho):
            if em_terminal:
                subprocess.Popen(['konsole', '-e', 'python3', caminho])
            else:
                subprocess.Popen(['python3', caminho])
        else:
            self.msg_aviso("Erro", f"Arquivo não encontrado:\n{nome_arquivo}")

    def fazer_backup(self):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            pastas = ["~/Área de trabalho", "~/Desktop", "~/Área de Trabalho", "~"]
            caminho_final = "~"
            for p in pastas:
                real = os.path.expanduser(p)
                if os.path.exists(real):
                    caminho_final = real
                    break
            
            arquivo = os.path.join(caminho_final, f"Backup_Scripts_{timestamp}")
            shutil.make_archive(arquivo, 'zip', self.script_dir)
            self.msg_aviso("Sucesso!", f"Backup salvo em:\n{caminho_final}")
        except Exception as e:
            self.msg_aviso("Erro", str(e))

    def msg_aviso(self, titulo, texto):
        win = ctk.CTkToplevel(self)
        win.geometry("500x300")
        win.title(titulo)
        ctk.CTkLabel(win, text=texto, font=("Roboto", 18), wraplength=450).pack(pady=50)
        ctk.CTkButton(win, text="OK", command=win.destroy, height=50, width=100).pack()

    def abrir_hardware(self): self.rodar_script("central_hardware.py")
    def abrir_fan(self): self.rodar_script("controle_fan.py")
    def abrir_boot(self): self.rodar_script("faxina_gui.py")
    def abrir_limpeza(self): self.rodar_script("limpeza_agildo.py", em_terminal=True)
    def abrir_proton(self): self.rodar_script("game_booster.py")

if __name__ == "__main__":
    app = CentralAgildoUltimate()
    app.mainloop()
"""

# Caminho onde vamos salvar
arquivo_destino = os.path.expanduser("~/ScriptsAgildo/central_unificada.py")

# Escrevendo o arquivo limpo
with open(arquivo_destino, "w") as f:
    f.write(codigo_da_central)

print("✅ SUCESSO! A Central foi recriada sem erros.")
print(f"Agora rode: python3 {arquivo_destino}")
