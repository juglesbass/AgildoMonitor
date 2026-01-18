#!/usr/bin/env python3
import customtkinter as ctk
import os
import glob
import threading
import time

# --- CONFIGURAÇÃO VISUAL ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FanController(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ventilador Agildo - RX 6600 (V3)")
        self.geometry("1920x1080")
        self.configure(fg_color="#101010")

        self.caminho_hwmon = self.encontrar_gpu_amd()
        self.monitorar = True
        self.modo_atual = "AUTO_BIOS" # Começa no automático

        # --- TÍTULO ---
        ctk.CTkLabel(self, text="💨 CONTROLE TOTAL RX 6600", 
                     font=("Roboto", 32, "bold"), text_color="#3498db").pack(pady=15)

        # --- MONITORAMENTO ---
        self.frame_info = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=15)
        self.frame_info.pack(pady=10, padx=30, fill="x")

        self.lbl_temp = ctk.CTkLabel(self.frame_info, text="Temp: --°C", 
                                     font=("Roboto", 42, "bold"), text_color="#e74c3c")
        self.lbl_temp.pack(side="left", padx=40, pady=20)

        self.lbl_rpm = ctk.CTkLabel(self.frame_info, text="RPM: --", 
                                    font=("Roboto", 30, "bold"), text_color="#2ecc71")
        self.lbl_rpm.pack(side="right", padx=40, pady=20)

        # --- STATUS E RESET (Novidade Aqui!) ---
        self.frame_status = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_status.pack(pady=5)

        self.lbl_status = ctk.CTkLabel(self.frame_status, text="Modo Atual: AUTOMÁTICO (Fábrica)", 
                                       font=("Roboto", 20, "bold"), text_color="gray")
        self.lbl_status.pack()

        # Botão para cancelar tudo e voltar ao padrão
        self.btn_reset = ctk.CTkButton(self, text="🔄 DESATIVAR E VOLTAR AO PADRÃO", 
                                       command=self.desativar_controle,
                                       font=("Roboto", 16, "bold"),
                                       fg_color="transparent", border_width=2, 
                                       border_color="gray", text_color="gray",
                                       hover_color="#222", width=300)
        self.btn_reset.pack(pady=10)

        # --- ABAS DE CONTROLE ---
        self.tabview = ctk.CTkTabview(self, width=900, height=400)
        self.tabview.pack(pady=10)
        self.tabview.add("🎛️ Manual")
        self.tabview.add("📈 Curva Inteligente")

        # === ABA MANUAL ===
        self.tab_manual = self.tabview.tab("🎛️ Manual")
        
        self.btn_manual = ctk.CTkButton(self.tab_manual, text="ATIVAR MODO MANUAL", 
                                        command=self.ativar_manual, height=50, 
                                        font=("Roboto", 18, "bold"), fg_color="#444")
        self.btn_manual.pack(pady=20, fill="x", padx=50)

        ctk.CTkLabel(self.tab_manual, text="Velocidade Fixa:", font=("Roboto", 18)).pack(pady=5)
        self.slider = ctk.CTkSlider(self.tab_manual, from_=0, to=100, command=self.atualizar_slider, width=600)
        self.slider.set(50)
        self.slider.pack(pady=10)
        self.lbl_slider_val = ctk.CTkLabel(self.tab_manual, text="50%", font=("Roboto", 24, "bold"))
        self.lbl_slider_val.pack(pady=5)

        self.btn_turbo = ctk.CTkButton(self.tab_manual, text="🔥 TURBO MÁXIMO (100%)", 
                                       command=self.ativar_turbo, height=60, 
                                       fg_color="#c0392b", hover_color="#e74c3c", font=("Roboto", 20, "bold"))
        self.btn_turbo.pack(pady=30, padx=50, fill="x")

        # === ABA CURVA ===
        self.tab_curva = self.tabview.tab("📈 Curva Inteligente")
        
        self.btn_curva = ctk.CTkButton(self.tab_curva, text="ATIVAR MODO CURVA", 
                                       command=self.ativar_curva, height=50, 
                                       font=("Roboto", 18, "bold"), fg_color="#444")
        self.btn_curva.pack(pady=20, fill="x", padx=50)

        self.frame_pontos = ctk.CTkFrame(self.tab_curva, fg_color="transparent")
        self.frame_pontos.pack(pady=10)

        self.entradas_curva = []
        pontos_padrao = [(45, 0), (60, 40), (70, 60), (80, 80)] 
        
        for t, p in pontos_padrao:
            f = ctk.CTkFrame(self.frame_pontos, fg_color="transparent")
            f.pack(pady=5)
            ctk.CTkLabel(f, text="Se Temp > ", font=("Roboto", 16)).pack(side="left")
            e_t = ctk.CTkEntry(f, width=60, font=("Roboto", 16)); e_t.insert(0, str(t)); e_t.pack(side="left", padx=5)
            ctk.CTkLabel(f, text="°C  então Fan = ", font=("Roboto", 16)).pack(side="left")
            e_p = ctk.CTkEntry(f, width=60, font=("Roboto", 16)); e_p.insert(0, str(p)); e_p.pack(side="left", padx=5)
            ctk.CTkLabel(f, text="%", font=("Roboto", 16)).pack(side="left")
            self.entradas_curva.append((e_t, e_p))

        # --- AVISO ---
        if os.geteuid() != 0:
             ctk.CTkLabel(self, text="⚠️ SEM PERMISSÃO DE ADMIN (SUDO)", text_color="red").pack(side="bottom", pady=10)

        self.protocol("WM_DELETE_WINDOW", self.ao_fechar)
        threading.Thread(target=self.loop_controle, daemon=True).start()

    def encontrar_gpu_amd(self):
        try:
            for c in glob.glob("/sys/class/drm/card*/device/hwmon/hwmon*"):
                if os.path.exists(os.path.join(c, "pwm1")): return c
        except: pass
        return None

    def rw_arquivo(self, arquivo, valor=None):
        path = os.path.join(self.caminho_hwmon, arquivo)
        try:
            if valor is not None:
                with open(path, 'w') as f: f.write(str(valor))
            else:
                with open(path, 'r') as f: return f.read().strip()
        except: return "0"

    # --- FUNÇÃO NOVA: RESET ---
    def desativar_controle(self):
        self.modo_atual = "AUTO_BIOS"
        self.rw_arquivo("pwm1_enable", "2") # 2 = Automático
        
        # Reset visual
        self.lbl_status.configure(text="Modo Atual: AUTOMÁTICO (Fábrica)", text_color="gray")
        self.btn_manual.configure(fg_color="#444", text="ATIVAR MODO MANUAL")
        self.btn_curva.configure(fg_color="#444", text="ATIVAR MODO CURVA")
        self.btn_reset.configure(state="disabled", text_color="gray", border_color="#333")

    def ativar_manual(self):
        self.modo_atual = "MANUAL"
        self.rw_arquivo("pwm1_enable", "1")
        
        self.lbl_status.configure(text="Modo Atual: MANUAL (Fixo)", text_color="#3498db")
        self.btn_manual.configure(fg_color="#3498db", text="✅ MODO MANUAL ATIVO")
        self.btn_curva.configure(fg_color="#444", text="ATIVAR MODO CURVA")
        self.btn_reset.configure(state="normal", text_color="white", border_color="gray")
        
        self.atualizar_slider(self.slider.get())

    def ativar_turbo(self):
        self.ativar_manual()
        self.slider.set(100)
        self.atualizar_slider(100)

    def ativar_curva(self):
        self.modo_atual = "CURVA"
        self.rw_arquivo("pwm1_enable", "1")
        
        self.lbl_status.configure(text="Modo Atual: CURVA INTELIGENTE", text_color="#2ecc71")
        self.btn_curva.configure(fg_color="#2ecc71", text="✅ MODO CURVA ATIVO")
        self.btn_manual.configure(fg_color="#444", text="ATIVAR MODO MANUAL")
        self.btn_reset.configure(state="normal", text_color="white", border_color="gray")

    def atualizar_slider(self, val):
        self.lbl_slider_val.configure(text=f"{int(val)}%")
        if self.modo_atual == "MANUAL":
            pwm = int((val / 100) * 255)
            self.rw_arquivo("pwm1", pwm)

    def loop_controle(self):
        while self.monitorar:
            if self.caminho_hwmon:
                temp = int(self.rw_arquivo("temp1_input") or 0) / 1000
                rpm = self.rw_arquivo("fan1_input")
                self.lbl_temp.configure(text=f"Temp: {temp:.0f}°C")
                self.lbl_rpm.configure(text=f"RPM: {rpm}")

                if self.modo_atual == "CURVA":
                    target = 0
                    pontos = []
                    try:
                        for et, ep in self.entradas_curva:
                            pontos.append((int(et.get()), int(ep.get())))
                        pontos.sort()
                        
                        for t_gatilho, p_fan in pontos:
                            if temp >= t_gatilho: target = p_fan
                            else: break
                        if temp > 90: target = 100 
                    except: target = 50

                    pwm = int((target / 100) * 255)
                    self.rw_arquivo("pwm1", pwm)
            time.sleep(2)

    def ao_fechar(self):
        if self.caminho_hwmon:
            self.rw_arquivo("pwm1_enable", "2")
        self.monitorar = False
        self.destroy()

if __name__ == "__main__":
    app = FanController()
    app.mainloop()
