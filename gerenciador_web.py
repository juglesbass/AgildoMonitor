#!/usr/bin/env python3
import customtkinter as ctk
import webbrowser
import json
import os
from tkinter import messagebox

# Configuração Visual
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Arquivo onde os sites ficam salvos
ARQUIVO_DB = os.path.expanduser("~/ScriptsAgildo/meus_sites.json")

class WebManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Geometria para TV 55"
        self.title("Agildo Web Commander")
        self.geometry("1400x900")
        self.configure(fg_color="#0a0a0a")

        # --- TÍTULO ---
        self.lbl_titulo = ctk.CTkLabel(self, text="🌐 MEUS SITES FAVORITOS", 
                                       font=("Roboto", 40, "bold"), text_color="#3498db")
        self.lbl_titulo.pack(pady=(30, 10))

        # --- ÁREA DE ROLAGEM (ONDE FICAM OS SITES) ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=800, height=500, corner_radius=15, fg_color="#141414")
        self.scroll_frame.pack(pady=20, fill="both", expand=True, padx=50)

        # --- BOTÃO ADICIONAR ---
        self.btn_add = ctk.CTkButton(self, text="+ ADICIONAR NOVO SITE", 
                                     font=("Roboto", 20, "bold"),
                                     height=60, width=300,
                                     fg_color="#2ecc71", hover_color="#27ae60",
                                     command=self.janela_adicionar)
        self.btn_add.pack(pady=20)

        # Carrega os sites salvos ao iniciar
        self.sites = self.carregar_dados()
        self.atualizar_lista()

    def carregar_dados(self):
        # Tenta ler o arquivo JSON. Se não existir, retorna lista vazia.
        if os.path.exists(ARQUIVO_DB):
            try:
                with open(ARQUIVO_DB, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def salvar_dados(self):
        # Escreve a lista no arquivo JSON
        with open(ARQUIVO_DB, "w") as f:
            json.dump(self.sites, f, indent=4)

    def atualizar_lista(self):
        # 1. Limpa a tela (remove os botões antigos)
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # 2. Recria os botões baseados na lista atualizada
        for i, site in enumerate(self.sites):
            self.criar_card_site(site, i)

    def criar_card_site(self, site, index):
        # Cria um "cartão" para cada site
        card = ctk.CTkFrame(self.scroll_frame, fg_color="#1f1f1f", corner_radius=10)
        card.pack(pady=10, fill="x", padx=10)

        # Nome do Site
        lbl_nome = ctk.CTkLabel(card, text=site['nome'], font=("Roboto", 24, "bold"), text_color="white")
        lbl_nome.pack(side="left", padx=20, pady=20)

        # Link (Pequeno)
        lbl_link = ctk.CTkLabel(card, text=site['url'], font=("Roboto", 14), text_color="gray")
        lbl_link.pack(side="left", padx=10)

        # Botão EXCLUIR (Vermelho)
        btn_del = ctk.CTkButton(card, text="🗑️", width=50, fg_color="#e74c3c", hover_color="#c0392b",
                                command=lambda: self.deletar_site(index))
        btn_del.pack(side="right", padx=10)

        # Botão ABRIR (Azul)
        btn_abrir = ctk.CTkButton(card, text="ABRIR ↗️", width=120, fg_color="#3498db", hover_color="#2980b9",
                                  command=lambda: self.abrir_site(site['url']))
        btn_abrir.pack(side="right", padx=10)

    def abrir_site(self, url):
        # Garante que tem https://
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)

    def deletar_site(self, index):
        # Remove da lista e salva
        del self.sites[index]
        self.salvar_dados()
        self.atualizar_lista()

    def janela_adicionar(self):
        # Cria uma janelinha flutuante (Pop-up)
        janela = ctk.CTkToplevel(self)
        janela.title("Novo Site")
        janela.geometry("500x400")
        
        # Garante que a janela fique no topo
        janela.attributes("-topmost", True)

        ctk.CTkLabel(janela, text="Nome do Site (Ex: YouTube):", font=("Roboto", 18)).pack(pady=20)
        entry_nome = ctk.CTkEntry(janela, width=400, height=40)
        entry_nome.pack()

        ctk.CTkLabel(janela, text="Link / URL (Ex: youtube.com):", font=("Roboto", 18)).pack(pady=20)
        entry_url = ctk.CTkEntry(janela, width=400, height=40)
        entry_url.pack()

        def confirmar():
            nome = entry_nome.get()
            url = entry_url.get()
            
            if nome and url:
                # Adiciona na memória
                self.sites.append({"nome": nome, "url": url})
                # Salva no disco
                self.salvar_dados()
                # Atualiza a tela
                self.atualizar_lista()
                janela.destroy() # Fecha o popup
            else:
                messagebox.showwarning("Atenção", "Preencha o nome e o link!")

        ctk.CTkButton(janela, text="SALVAR SITE", fg_color="#2ecc71", 
                      height=50, command=confirmar).pack(pady=40)

if __name__ == "__main__":
    app = WebManager()
    app.mainloop()
