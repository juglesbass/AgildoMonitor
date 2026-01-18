#!/usr/bin/env python3
import customtkinter as ctk
import os
import time
import threading
import subprocess

# Configuração Visual
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class GameBooster(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Modo Jogo - Agildo Systems")
        self.geometry("600x450")
        self.configure(fg_color="#0f0f0f") # Fundo preto
        
        # Título
        ctk.CTkLabel(self, text="🚀 PREPARANDO PARA COMBATE", 
                     font=("Roboto", 28, "bold"), text_color="#9b59b6").pack(pady=30)

        # Área de Log (Onde mostra o que está sendo fechado)
        self.log_text = ctk.CTkTextbox(self, width=500, height=200, font=("Consolas", 14), fg_color="#1a1a1a", text_color="#ddd")
        self.log_text.pack(pady=10)
        self.log_text.insert("0.0", "Iniciando protocolos de otimização...\n")

        # Barra de progresso
        self.progress = ctk.CTkProgressBar(self, width=400, progress_color="#9b59b6")
        self.progress.set(0)
        self.progress.pack(pady=20)

        # Inicia a mágica automaticamente
        threading.Thread(target=self.executar_otimizacao).start()

    def log(self, mensagem):
        self.log_text.insert("end", f"✅ {mensagem}\n")
        self.log_text.see("end")
        time.sleep(0.8) # Pausa para dar efeito visual

    def executar_otimizacao(self):
        self.progress.set(0.1)
        
        # 1. Definir CPU Governor para Performance
        # Isso faz seu Xeon rodar no clock máximo em todos os núcleos
        self.log("Xeon E5-2640: Forçando Performance Máxima...")
        try:
            os.system("echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null")
        except:
            self.log("Aviso: Não foi possível alterar governor CPU.")
        self.progress.set(0.3)

        # 2. Fechar Navegadores (Comem muita RAM)
        self.log("Fechando navegadores para liberar RAM...")
        navegadores = ["firefox", "chrome", "chromium", "brave", "edge", "opera"]
        for app in navegadores:
            os.system(f"killall {app} 2>/dev/null")
        self.progress.set(0.6)

        # 3. Limpar Cache de RAM e Swap
        self.log("Limpando Cache do Sistema (Drop Caches)...")
        os.system("sync; echo 3 > /proc/sys/vm/drop_caches")
        self.progress.set(0.8)

        # 4. Abrir Controle de Fan (Já que vai esquentar)
        self.log("Ativando Painel de Refrigeração (RX 6600)...")
        caminho_fan = "/home/agildo/ScriptsAgildo/controle_fan.py"
        if os.path.exists(caminho_fan):
            subprocess.Popen(['python3', caminho_fan])
        
        self.progress.set(1.0)
        self.log("OTIMIZAÇÃO CONCLUÍDA! ⚔️")
        self.log("Sistema pronto para Ghost of Tsushima.")
        
        # Botão para fechar
        self.btn_sair = ctk.CTkButton(self, text="FECHAR E JOGAR", command=self.destroy,
                                      fg_color="#9b59b6", hover_color="#8e44ad", 
                                      font=("Roboto", 16, "bold"), height=50)
        self.btn_sair.pack(pady=10)

if __name__ == "__main__":
    app = GameBooster()
    app.mainloop()
