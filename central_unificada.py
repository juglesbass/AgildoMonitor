#!/usr/bin/env python3
import customtkinter as ctk
import subprocess
import os
import shutil
from datetime import datetime

# --- CONFIGURAÇÃO VISUAL ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class CentralAgildoUltimate(ctk.CTk):
    def __init__(self):
        super().__init__()

        # GEOMETRIA: Otimizada para TV 55" (4K com escala)
        self.title("Agildo Systems - Command Center")
        self.geometry("1600x1400") 
        self.configure(fg_color="#050505")

        self.script_dir = "/home/agildo/ScriptsAgildo"

        # --- CABEÇALHO ---
        self.header = ctk.CTkFrame(self, fg_color="#0a0a0a", height=160, corner_radius=0)
        self.header.pack(fill="x", pady=(0, 30))

        self.lbl_title = ctk.CTkLabel(self.header, text="🚀 CENTRAL DE COMANDO", 
                                      font=("Roboto", 40, "bold"), text_color="#3498db")
        self.lbl_title.place(relx=0.5, rely=0.4, anchor="center")
        
        self.lbl_subtitle = ctk.CTkLabel(self.header, text="AGILDO SYSTEMS  •  CACHYOS  •  MANAUS", 
                                      font=("Roboto", 17, "bold"), text_color="#666")
        self.lbl_subtitle.place(relx=0.5, rely=0.85, anchor="center")

        # --- CONTAINER DOS CARDS ---
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(pady=10, padx=60, fill="both", expand=True)

        # 1. HARDWARE (Verde)
        self.criar_smart_card("📊", "MONITOR DE HARDWARE", "Vigiar Xeon E5-2640 e RX 6600", "#2ecc71", self.abrir_hardware)

        # 2. VENTOINHA (Vermelho)
        self.criar_smart_card("💨", "CONTROLE DE VENTOINHA", "Curvas Térmicas e Modo Turbo", "#e74c3c", self.abrir_fan)

        # 3. BOOT (Laranja)
        self.criar_smart_card("🚑", "FAXINA DE BOOT (UEFI)", "Reparar Entradas de Inicialização", "#e67e22", self.abrir_boot)

        # 4. LIMPEZA (Amarelo)
        self.criar_smart_card("🧹", "LIMPEZA DO SISTEMA", "Otimizar NVMe e Cache (Terminal)", "#f1c40f", self.abrir_limpeza)
        
        # 5. GAME BOOSTER (Roxo)
        self.criar_smart_card("🎮", "GAME BOOSTER (PROTON)", "Lançador de Jogos Windows/Steam", "#9b59b6", self.abrir_proton)

        # 6. BACKUP (Azul)
        self.criar_smart_card("💾", "BACKUP DE SEGURANÇA", "Salvar Scripts em ZIP na Área de Trabalho", "#3498db", self.fazer_backup)

        # --- RODAPÉ ---
        self.lbl_footer = ctk.CTkLabel(self, text="SISTEMA PRONTO PARA JOGAR | TV TCL 55\"", 
                                       text_color="#333", font=("Roboto", 14, "bold"))
        self.lbl_footer.pack(side="bottom", pady=20)

    def criar_smart_card(self, icone, titulo, sub, cor_destaque, comando):
        # 1. O FRAME DO CARTÃO (O fundo)
        card = ctk.CTkFrame(self.container, fg_color="#181818", height=110, corner_radius=15, border_width=2, border_color="#222")
        card.pack(pady=10, fill="x")
        
        # Impede que o frame encolha, mantendo a altura de 110px
        card.pack_propagate(False) 

        # 2. O ÍCONE (Esquerda)
        lbl_ico = ctk.CTkLabel(card, text=icone, font=("Roboto",35))
        lbl_ico.pack(side="left", padx=(30, 20)) # Margem esquerda 30, direita 20

        # 3. BLOCO DE TEXTO (Meio)
        frame_texto = ctk.CTkFrame(card, fg_color="transparent")
        frame_texto.pack(side="left", fill="y", pady=20)

        lbl_tit = ctk.CTkLabel(frame_texto, text=titulo, font=("Roboto", 16, "bold"), text_color="white")
        lbl_tit.pack(anchor="w") # Alinha a esquerda dentro do bloco

        lbl_sub = ctk.CTkLabel(frame_texto, text=sub, font=("Roboto", 12), text_color="#AAAAAA")
        lbl_sub.pack(anchor="w")

        # 4. SETA INDICATIVA (Direita - Decorativa)
        lbl_seta = ctk.CTkLabel(card, text="▶", font=("Roboto", 20), text_color="#333")
        lbl_seta.pack(side="right", padx=30)

        # --- A MÁGICA DA INTERATIVIDADE ---
        # Fazemos TODOS os elementos responderem ao clique e ao mouse passando
        elementos = [card, lbl_ico, frame_texto, lbl_tit, lbl_sub, lbl_seta]

        def ao_entrar(e):
            card.configure(border_color=cor_destaque, fg_color="#202020")
            lbl_seta.configure(text_color=cor_destaque)

        def ao_sair(e):
            card.configure(border_color="#222", fg_color="#181818")
            lbl_seta.configure(text_color="#333")

        def ao_clicar(e):
            comando()

        for widget in elementos:
            widget.bind("<Enter>", ao_entrar) # Mouse entra
            widget.bind("<Leave>", ao_sair)   # Mouse sai
            widget.bind("<Button-1>", ao_clicar) # Clique esquerdo

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
            nome_zip = f"/home/agildo/Área de Trabalho/Backup_Scripts_{timestamp}"
            shutil.make_archive(nome_zip, 'zip', self.script_dir)
            self.msg_aviso("Sucesso", "Backup criado na Área de Trabalho!")
        except Exception as e:
            self.msg_aviso("Erro", str(e))

    def msg_aviso(self, titulo, texto):
        win = ctk.CTkToplevel(self)
        win.geometry("400x200")
        win.title(titulo)
        ctk.CTkLabel(win, text=texto, font=("Roboto", 16)).pack(pady=40)
        ctk.CTkButton(win, text="OK", command=win.destroy).pack()

    # Ligações
    def abrir_hardware(self): self.rodar_script("central_hardware.py")
    def abrir_fan(self): self.rodar_script("controle_fan.py")
    def abrir_boot(self): self.rodar_script("faxina_gui.py")
    def abrir_limpeza(self): self.rodar_script("limpeza_agildo.py", em_terminal=True)
    def abrir_proton(self): self.rodar_script("game_booster.py")

if __name__ == "__main__":
    app = CentralAgildoUltimate()
    app.mainloop()
