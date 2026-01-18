#!/usr/bin/env python3
import customtkinter as ctk
import subprocess
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class FaxinaBootGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Largura extra para a escala de 2.5x na TV de 50"
        self.title("Gerenciador de Boot EFI - Xeon X99")
        self.geometry("1200x800")
        self.configure(fg_color="#121212")

        # Título
        self.label_titulo = ctk.CTkLabel(self, text="Faxina Profunda de Boot", 
                                         font=("Roboto", 32, "bold"), text_color="#2ecc71")
        self.label_titulo.pack(pady=(40, 20))

        # Caixa de texto onde aparece a lista de boot
        self.textbox = ctk.CTkTextbox(self, width=1000, height=350, font=("Courier New", 18))
        self.textbox.pack(pady=10)

        # Botão para listar o que tem no menu do Xeon
        self.btn_listar = ctk.CTkButton(self, text="🔍 Listar Entradas do Sistema", 
                                         command=self.listar_boot, width=500, height=60, font=("Roboto", 20))
        self.btn_listar.pack(pady=15)

        # Botão de Limpeza - Agora usando o Konsole para evitar o loop de senha
        self.btn_limpar = ctk.CTkButton(self, text="🧹 Executar Limpeza no Terminal", 
                                         command=self.executar_limpeza_segura, 
                                         fg_color="#c0392b", hover_color="#a93226",
                                         width=500, height=60, font=("Roboto", 20))
        self.btn_limpar.pack(pady=15)

        self.label_status = ctk.CTkLabel(self, text="Pronto para iniciar.", font=("Roboto", 18))
        self.label_status.pack(pady=20)

    def listar_boot(self):
        try:
            # Mostra o status atual do efibootmgr
            resultado = subprocess.check_output(['efibootmgr'], text=True)
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", resultado)
            self.label_status.configure(text="Lista atualizada com sucesso!", text_color="#2ecc71")
        except Exception as e:
            self.label_status.configure(text=f"Erro ao ler boot: {e}", text_color="red")

    def executar_limpeza_segura(self):
        # A FORMA MAIS SEGURA: Abre um terminal Konsole que pede o sudo
        # Assim você vê a limpeza acontecendo e a senha não entra em loop
        try:
            subprocess.Popen(['konsole', '-e', 'sudo', 'python3', '/home/agildo/Imagens/recupera_e_limpa_boot.py'])
            self.label_status.configure(text="Terminal de limpeza aberto!", text_color="yellow")
        except Exception as e:
            self.label_status.configure(text=f"Erro ao abrir terminal: {e}", text_color="red")

if __name__ == "__main__":
    app = FaxinaBootGUI()
    app.mainloop()
