import os

# Este é o código do MONITOR DE HARDWARE que será gravado
codigo_hardware = r"""#!/usr/bin/env python3
import customtkinter as ctk
import psutil
import threading
import time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class MonitorHardware(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Monitor Agildo - Xeon & RX 6600")
        self.geometry("800x600")
        self.configure(fg_color="#050505")

        # Título
        self.lbl_title = ctk.CTkLabel(self, text="📊 STATUS DO SISTEMA", font=("Roboto", 30, "bold"), text_color="#2ecc71")
        self.lbl_title.pack(pady=20)

        # Container CPU
        self.frame_cpu = ctk.CTkFrame(self, fg_color="#101010")
        self.frame_cpu.pack(fill="x", padx=20, pady=10)
        
        self.lbl_cpu = ctk.CTkLabel(self.frame_cpu, text="PROCESSADOR XEON E5-2640 v3", font=("Roboto", 18, "bold"))
        self.lbl_cpu.pack(anchor="w", padx=20, pady=(10,0))
        
        self.bar_cpu = ctk.CTkProgressBar(self.frame_cpu, width=600, height=30, progress_color="#3498db")
        self.bar_cpu.pack(pady=10)
        self.bar_cpu.set(0)
        
        self.val_cpu = ctk.CTkLabel(self.frame_cpu, text="0%", font=("Roboto", 24, "bold"), text_color="#3498db")
        self.val_cpu.pack(pady=(0,10))

        # Container RAM
        self.frame_ram = ctk.CTkFrame(self, fg_color="#101010")
        self.frame_ram.pack(fill="x", padx=20, pady=10)
        
        self.lbl_ram = ctk.CTkLabel(self.frame_ram, text="MEMÓRIA RAM (DDR4)", font=("Roboto", 18, "bold"))
        self.lbl_ram.pack(anchor="w", padx=20, pady=(10,0))
        
        self.bar_ram = ctk.CTkProgressBar(self.frame_ram, width=600, height=30, progress_color="#e67e22")
        self.bar_ram.pack(pady=10)
        self.bar_ram.set(0)
        
        self.val_ram = ctk.CTkLabel(self.frame_ram, text="0%", font=("Roboto", 24, "bold"), text_color="#e67e22")
        self.val_ram.pack(pady=(0,10))

        # Rodapé
        self.lbl_info = ctk.CTkLabel(self, text="Monitoramento em Tempo Real - Atualização: 1s", text_color="#555")
        self.lbl_info.pack(side="bottom", pady=20)

        # Iniciar loop de atualização
        self.atualizar_dados()

    def atualizar_dados(self):
        # Pega dados reais do PC
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        # Atualiza as barras
        self.bar_cpu.set(cpu / 100)
        self.val_cpu.configure(text=f"{cpu}%")

        self.bar_ram.set(ram / 100)
        self.val_ram.configure(text=f"{ram}%")

        # Repete a cada 1000ms (1 segundo)
        self.after(1000, self.atualizar_dados)

if __name__ == "__main__":
    app = MonitorHardware()
    app.mainloop()
"""

# Caminho do arquivo que está estragado
arquivo_destino = os.path.expanduser("~/ScriptsAgildo/central_hardware.py")

# Reescreve o arquivo com o código certo
with open(arquivo_destino, "w") as f:
    f.write(codigo_hardware)

print("✅ MONITOR DE HARDWARE RESTAURADO COM SUCESSO!")
"""

Salve (`Ctrl+S`) e Saia (`Ctrl+Q`).

### Passo 3: Executar a Correção
Rode este comando no terminal para consertar o arquivo:

```bash
python3 ~/ScriptsAgildo/restaurar_hardware.py
