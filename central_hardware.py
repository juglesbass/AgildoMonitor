#!/usr/bin/env python3
import customtkinter as ctk
import os
import glob

ctk.set_appearance_mode("dark")

class CentralAgildo(ctk.CTk):
    def __init__(self):
        super().__init__()

        # AUMENTO DA ESCALA DA JANELA PARA NÃO CORTAR (1200x800)
        self.title("Central Agildo - Hardware")
        self.geometry("1600x1100") 
        self.configure(fg_color="#121212")

        # --- SEÇÃO INTEL XEON (Mantida) ---
        self.frame_cpu = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=15)
        self.frame_cpu.pack(pady=20, padx=40, fill="x")
        
        ctk.CTkLabel(self.frame_cpu, text="💻 INTEL XEON E5-2640 V3", 
                     font=("Roboto", 24, "bold"), text_color="#3498db").pack(pady=10)
        
        self.lbl_cpu = ctk.CTkLabel(self.frame_cpu, text="1.3%  |  36°C", 
                                    font=("Roboto", 46, "bold"), text_color="#e67e22")
        self.lbl_cpu.pack(pady=15)

        # --- SEÇÃO AMD RADEON (Ajustada) ---
        self.frame_gpu = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=15)
        self.frame_gpu.pack(pady=20, padx=40, fill="x")
        
        ctk.CTkLabel(self.frame_gpu, text="🎮 AMD RADEON RX 6600", 
                     font=("Roboto", 24, "bold"), text_color="#2ecc71").pack(pady=10)

        # Grid interno com mais espaço (Padding)
        self.gpu_grid = ctk.CTkFrame(self.frame_gpu, fg_color="transparent")
        self.gpu_grid.pack(pady=20, padx=30, fill="both")

        # Organização em 2 colunas e 2 linhas para dar espaço à escala 2.5x
        self.gpu_grid.columnconfigure((0, 1), weight=1)

        # Temperaturas (Core e Junction)
        self.lbl_gpu_temp = ctk.CTkLabel(self.gpu_grid, text="Core: --°C", font=("Roboto", 38, "bold"))
        self.lbl_gpu_temp.grid(row=0, column=0, pady=15)

        self.lbl_gpu_junc = ctk.CTkLabel(self.gpu_grid, text="Junc: --°C", font=("Roboto", 38, "bold"), text_color="#f1c40f")
        self.lbl_gpu_junc.grid(row=1, column=0, pady=15)

        # Uso e VRAM
        self.lbl_gpu_uso = ctk.CTkLabel(self.gpu_grid, text="Uso: --%", font=("Roboto", 38, "bold"), text_color="#3498db")
        self.lbl_gpu_uso.grid(row=0, column=1, pady=15)

        self.lbl_gpu_vram = ctk.CTkLabel(self.gpu_grid, text="VRAM: -- GB", font=("Roboto", 38, "bold"), text_color="#9b59b6")
        self.lbl_gpu_vram.grid(row=1, column=1, pady=15)

        self.atualizar_dados()

    def ler_valor(self, caminho):
        try:
            with open(caminho, 'r') as f: return f.read().strip()
        except: return "0"

    def atualizar_dados(self):
        # Lógica CPU (Xeon)
        t_cpu = int(self.ler_valor("/sys/class/thermal/thermal_zone0/temp")) / 1000
        self.lbl_cpu.configure(text=f"1.3%  |  {t_cpu:.0f}°C")

        # Lógica GPU (RX 6600)
        base = "/sys/class/drm/card1/device/"
        hw = glob.glob(base + "hwmon/hwmon*")[0]
        
        t_edge = int(self.ler_valor(f"{hw}/temp1_input")) / 1000
        t_junc = int(self.ler_valor(f"{hw}/temp2_input")) / 1000
        uso    = self.ler_valor(base + "gpu_busy_percent")
        v_uso  = int(self.ler_valor(base + "mem_info_vram_used")) / (1024**3)

        # Atualizando os labels separados
        self.lbl_gpu_temp.configure(text=f"🔥 Core: {t_edge:.0f}°C")
        self.lbl_gpu_junc.configure(text=f"📍 Junc: {t_junc:.0f}°C")
        self.lbl_gpu_uso.configure(text=f"📊 Uso: {uso}%")
        self.lbl_gpu_vram.configure(text=f"🧠 {v_uso:.2f} GB")

        self.after(1000, self.atualizar_dados)

if __name__ == "__main__":
    app = CentralAgildo()
    app.mainloop()
