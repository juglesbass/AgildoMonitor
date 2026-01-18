#!/usr/bin/env python3
import sys
import psutil
import glob
import os
import time
import platform
import subprocess
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
                             QLabel, QProgressBar, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QPushButton, QMessageBox)
from PyQt6.QtCore import QTimer, Qt, QSettings, QThread, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import QColor

# ==========================================
# 🛠️ FUNÇÕES AUXILIARES DE HARDWARE
# ==========================================
def pegar_nome_cpu_real():
    """Lê o arquivo /proc/cpuinfo para descobrir o nome exato do processador."""
    try:
        with open("/proc/cpuinfo", "r") as f:
            for linha in f:
                if "model name" in linha:
                    # Limpa o nome para não ficar gigante na tela
                    nome = linha.split(":")[1].strip()
                    remover = ["Intel(R)", "Core(TM)", "CPU", "AMD", "Processor", "(R)", "(TM)"]
                    for item in remover:
                        nome = nome.replace(item, "")
                    return nome.strip()
    except:
        return "Processador"
    return "CPU Genérica"

# ==========================================
# 🧠 O CÉREBRO (Worker Thread Universal)
# ==========================================
class WorkerThread(QThread):
    dados_atualizados = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.rodando = True
        # Detecta o nome da CPU apenas uma vez na inicialização
        self.nome_cpu = pegar_nome_cpu_real()

    def ler_arquivo(self, path):
        try: 
            with open(path) as f: return f.read().strip()
        except: return None

    def tentar_nvidia(self):
        """Tenta pegar dados usando driver proprietário da Nvidia"""
        try:
            # Requer nvidia-utils instalado
            temp = subprocess.check_output(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"])
            uso = subprocess.check_output(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"])
            return int(uso.strip()), int(temp.strip()), 0 # Nvidia não expõe hotspot fácil aqui
        except:
            return None # Não é Nvidia ou driver não instalado

    def run(self):
        while self.rodando:
            dados = {}
            
            # --- 1. GERAIS ---
            dados['hora'] = datetime.now().strftime("%H:%M:%S")
            dados['uptime'] = str(timedelta(seconds=int(time.time() - psutil.boot_time())))

            # --- 2. CPU (UNIVERSAL) ---
            temps = psutil.sensors_temperatures()
            cpu_temp = 0
            # Tenta drivers comuns de temperatura
            if 'coretemp' in temps: cpu_temp = temps['coretemp'][0].current      # Intel
            elif 'k10temp' in temps: cpu_temp = temps['k10temp'][0].current      # AMD Ryzen
            elif 'zenpower' in temps: cpu_temp = temps['zenpower'][0].current    # AMD Custom
            else:
                # Pega o primeiro que achar
                for name, entries in temps.items():
                    if len(entries) > 0:
                        cpu_temp = entries[0].current
                        break
            
            dados['cpu_nome'] = self.nome_cpu
            dados['cpu_temp'] = cpu_temp
            dados['cpu_pct'] = psutil.cpu_percent(interval=None)

            # --- 3. GPU (DETECÇÃO AUTOMÁTICA) ---
            uso=0; edge=0; hot=0
            nome_gpu = "GPU"

            # A. Tenta Nvidia Primeiro
            dados_nvidia = self.tentar_nvidia()
            if dados_nvidia:
                uso, edge, hot = dados_nvidia
                nome_gpu = "NVIDIA GeForce"
            else:
                # B. Tenta AMD (Arquivos do Sistema)
                caminho_gpu = ""
                # Procura uso
                for c in glob.glob("/sys/class/drm/card*"):
                    if os.path.exists(c+"/device/gpu_busy_percent"):
                        val = self.ler_arquivo(c+"/device/gpu_busy_percent")
                        if val: 
                            uso=int(val)
                            caminho_gpu = c
                            nome_gpu = "AMD Radeon" # Detectou AMD

                # Se achou AMD, procura temperatura
                if caminho_gpu:
                    for p in glob.glob("/sys/class/hwmon/hwmon*"):
                        if self.ler_arquivo(p+"/name") == "amdgpu":
                            t1=self.ler_arquivo(p+"/temp1_input")
                            if t1: edge=int(t1)/1000
                            t2=self.ler_arquivo(p+"/temp2_input"); t3=self.ler_arquivo(p+"/temp3_input")
                            hot = int(t2)/1000 if (t2 and int(t2)>0) else (int(t3)/1000 if t3 else 0)
                            break
                    if edge==0 and hot>0: edge=hot
            
            dados['gpu'] = {'nome': nome_gpu, 'uso': uso, 'edge': edge, 'hot': hot}

            # --- 4. MEMÓRIA, DISCO E REDE ---
            mem = psutil.virtual_memory()
            dados['ram'] = {'pct': mem.percent, 'usado': mem.used, 'total': mem.total}
            
            disk = psutil.disk_usage('/')
            dados['disk'] = {'pct': disk.percent, 'livre': disk.free, 'total': disk.total}
            
            net = psutil.net_io_counters()
            dados['net'] = {'recv': net.bytes_recv, 'sent': net.bytes_sent}

            # --- 5. PROCESSOS ---
            procs = []
            try:
                for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        p_info = p.info
                        if p_info['cpu_percent'] > 0 or p_info['memory_percent'] > 0.1:
                            procs.append(p_info)
                    except: pass
            except: pass
            dados['procs'] = procs

            # Envia e dorme picado (Zero Lag)
            self.dados_atualizados.emit(dados)
            for _ in range(20):
                if not self.rodando: return
                self.msleep(50)

    def parar(self):
        self.rodando = False

# ==========================================
# 🎨 CLASSES DE INTERFACE (VISUAL)
# ==========================================
class PainelHardware(QFrame):
    def __init__(self, titulo, icone, cor):
        super().__init__()
        self.setStyleSheet(f"QFrame {{ background-color: #1a1b26; border-radius: 15px; border: 1px solid #333; }} QLabel {{ border: none; background-color: transparent; }}")
        layout = QVBoxLayout(); self.setLayout(layout)
        lbl_tit = QLabel(f"{icone}  {titulo}"); lbl_tit.setStyleSheet(f"color: {cor}; font-size: 16px; font-weight: bold;")
        layout.addWidget(lbl_tit)
        self.lbl_info = QLabel("..."); self.lbl_info.setStyleSheet("color: white; font-size: 26px; font-weight: bold;") 
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter); self.lbl_info.setWordWrap(True)
        layout.addWidget(self.lbl_info)
        self.lbl_porc = QLabel("0%"); self.lbl_porc.setStyleSheet(f"color: {cor}; font-size: 18px; font-weight: bold;")
        self.lbl_porc.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.lbl_porc)
        self.barra = QProgressBar(); self.barra.setTextVisible(False); self.barra.setFixedHeight(8)
        self.barra.setStyleSheet(f"QProgressBar {{ background: #24283b; border-radius: 4px; }} QProgressBar::chunk {{ background: {cor}; border-radius: 4px; }}")
        layout.addWidget(self.barra)
    def atualizar(self, pct, texto):
        self.barra.setValue(int(pct)); self.lbl_porc.setText(f"{pct:.1f}%"); self.lbl_info.setText(texto)

class PainelRede(QFrame):
    def __init__(self, titulo, icone, cor):
        super().__init__()
        self.setStyleSheet(f"QFrame {{ background-color: #1a1b26; border-radius: 15px; border: 1px solid #333; }}")
        layout = QVBoxLayout(); self.setLayout(layout)
        lbl_tit = QLabel(f"{icone}  {titulo}"); lbl_tit.setStyleSheet(f"color: {cor}; font-size: 16px; font-weight: bold;")
        layout.addWidget(lbl_tit)
        self.lbl_velocidade = QLabel("0 KB/s"); self.lbl_velocidade.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        self.lbl_velocidade.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(self.lbl_velocidade)
        self.ultimo_valor = 0
    def atualizar_velocidade(self, valor_atual_bytes):
        if self.ultimo_valor == 0: self.ultimo_valor = valor_atual_bytes; return
        diferenca = valor_atual_bytes - self.ultimo_valor; self.ultimo_valor = valor_atual_bytes
        velocidade = diferenca / 1024 
        if velocidade > 1024: texto = f"{velocidade/1024:.1f} MB/s"; cor = "#2ecc71"
        else: texto = f"{velocidade:.1f} KB/s"; cor = "white"
        self.lbl_velocidade.setText(texto); self.lbl_velocidade.setStyleSheet(f"color: {cor}; font-size: 32px; font-weight: bold;")

class MonitorProcessos(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #1a1b26; border-radius: 15px; border: 1px solid #333;")
        self.ordenar_por = 'ram'
        layout = QVBoxLayout(); self.setLayout(layout)
        topo = QHBoxLayout()
        topo.addWidget(QLabel("GERENCIADOR DE TAREFAS", styleSheet="color: #a9b1d6; font-weight: bold;"))
        topo.addStretch()
        self.btn_cpu = QPushButton("CPU"); self.btn_cpu.clicked.connect(lambda: self.mudar('cpu'))
        self.btn_ram = QPushButton("RAM"); self.btn_ram.clicked.connect(lambda: self.mudar('ram'))
        self.estilo_btn(self.btn_cpu); self.estilo_btn(self.btn_ram)
        topo.addWidget(self.btn_cpu); topo.addWidget(self.btn_ram)
        layout.addLayout(topo)
        self.tabela = QTableWidget(); self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["PROCESSO", "CPU", "RAM", "KILL"])
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabela.setStyleSheet("QTableWidget { background: #16161e; color: white; border: none; } QHeaderView::section { background: #24283b; color: #7aa2f7; }")
        layout.addWidget(self.tabela)
    def estilo_btn(self, btn): btn.setFixedSize(80, 25); btn.setStyleSheet("background: #24283b; color: white; border-radius: 4px;")
    def mudar(self, tipo): self.ordenar_por = tipo; self.atualizar_botoes()
    def atualizar_botoes(self):
        if self.ordenar_por == 'cpu': self.btn_cpu.setStyleSheet("background: #3498db; color: white;"); self.btn_ram.setStyleSheet("background: #24283b; color: white;")
        else: self.btn_cpu.setStyleSheet("background: #24283b; color: white;"); self.btn_ram.setStyleSheet("background: #3498db; color: white;")
    def matar(self, pid):
        try: psutil.Process(pid).kill()
        except: pass
    def receber_dados(self, procs):
        key = 'cpu_percent' if self.ordenar_por == 'cpu' else 'memory_percent'
        procs.sort(key=lambda x: x[key], reverse=True)
        self.tabela.setRowCount(len(procs[:6]))
        for i, p in enumerate(procs[:6]):
            self.tabela.setItem(i, 0, QTableWidgetItem(str(p['name'])))
            self.tabela.setItem(i, 1, QTableWidgetItem(f"{p['cpu_percent']:.1f}%"))
            self.tabela.setItem(i, 2, QTableWidgetItem(f"{p['memory_percent']:.1f}%"))
            cor = QColor("#ff5555") if p['cpu_percent'] > 20 or p['memory_percent'] > 10 else QColor("white")
            for c in range(3): self.tabela.item(i, c).setForeground(cor)
            btn = QPushButton("💀"); btn.setFixedSize(30, 20); btn.setStyleSheet("background: #c0392b; border: none;")
            btn.clicked.connect(lambda ch, pid=p['pid']: self.matar(pid))
            self.tabela.setCellWidget(i, 3, btn)

# ==========================================
# 🖥️ JANELA PRINCIPAL
# ==========================================
class DashboardFinal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agildo Monitor Ultimate")
        self.setStyleSheet("background-color: #131313;")

        # --- SISTEMA DE MEMÓRIA DE JANELA ---
        self.settings = QSettings("AgildoSystems", "MonitorUniversal_V12")
        
        # Carrega tamanho (Padrão 1200x950 se for a primeira vez)
        tamanho = self.settings.value("size", QSize(1200, 950))
        self.resize(tamanho)
        
        # Carrega posição
        posicao = self.settings.value("pos", QPoint(50, 50))
        self.move(posicao)

        # Força a posição logo após abrir (Hack para Linux/Wayland)
        QTimer.singleShot(100, self.forcar_posicao)

        main_layout = QVBoxLayout(); self.setLayout(main_layout)

        # Barra Superior
        status_bar = QFrame(); status_bar.setStyleSheet("background-color: #1a1b26; border-radius: 10px; border: 1px solid #333;"); status_bar.setFixedHeight(60)
        status_layout = QHBoxLayout(status_bar)
        k = platform.release().split('-')[0]
        self.lbl_sys = QLabel(f"🐧 CachyOS Linux • Kernel {k}"); self.lbl_sys.setStyleSheet("color: #7aa2f7; font-size: 16px; font-weight: bold; border: none;")
        status_layout.addWidget(self.lbl_sys); status_layout.addStretch()
        self.lbl_uptime = QLabel("Ligado há: ..."); self.lbl_uptime.setStyleSheet("color: #e0af68; font-size: 16px; font-weight: bold; border: none;")
        status_layout.addWidget(self.lbl_uptime); status_layout.addStretch()
        self.lbl_clock = QLabel("00:00:00"); self.lbl_clock.setStyleSheet("color: #2ecc71; font-size: 24px; font-weight: bold; border: none;")
        status_layout.addWidget(self.lbl_clock); main_layout.addWidget(status_bar)

        # Grid de Hardware
        grid = QGridLayout(); grid.setSpacing(15); main_layout.addLayout(grid)
        self.card_cpu = PainelHardware("PROCESSADOR", "🧠", "#7aa2f7"); grid.addWidget(self.card_cpu, 0, 0)
        self.card_gpu = PainelHardware("PLACA DE VÍDEO", "🎮", "#bb9af7"); grid.addWidget(self.card_gpu, 0, 1)
        self.card_ram = PainelHardware("MEMÓRIA RAM", "⚡", "#e0af68"); grid.addWidget(self.card_ram, 0, 2)
        self.card_disk = PainelHardware("DISCO (SSD)", "💾", "#9ece6a"); grid.addWidget(self.card_disk, 1, 0)
        self.card_down = PainelRede("DOWNLOAD", "⬇️", "#2ecc71"); grid.addWidget(self.card_down, 1, 1)
        self.card_up = PainelRede("UPLOAD", "⬆️", "#3498db"); grid.addWidget(self.card_up, 1, 2)
        
        # Tabela de Processos
        self.painel_proc = MonitorProcessos(); self.painel_proc.setFixedHeight(300); main_layout.addWidget(self.painel_proc)

        # Thread
        self.thread = WorkerThread()
        self.thread.dados_atualizados.connect(self.atualizar_interface)
        self.thread.start()

    def forcar_posicao(self):
        pos = self.settings.value("pos")
        if pos: self.move(pos)

    def closeEvent(self, event):
        self.thread.parar()
        self.thread.wait(100) # Espera rápida
        # Salva tudo manualmente
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        event.accept()

    def atualizar_interface(self, dados):
        # Atualiza Status
        self.lbl_clock.setText(dados['hora'])
        self.lbl_uptime.setText(f"Ligado há: {dados['uptime']}")
        
        # Atualiza Cards com Nomes DETECTADOS (Não fixos)
        self.card_cpu.atualizar(dados['cpu_pct'], f"{dados['cpu_nome']}\n{dados['cpu_temp']:.0f}°C")
        
        # GPU (Mostra Nvidia ou AMD automaticamente)
        if dados['gpu']['nome'] == "GPU": # Se não achou nada
             self.card_gpu.atualizar(0, "GPU Desconhecida\nSem Driver")
        else:
             self.card_gpu.atualizar(dados['gpu']['uso'], f"{dados['gpu']['nome']} • {dados['gpu']['edge']:.0f}°C\nHotspot: {dados['gpu']['hot']:.0f}°C")

        self.card_ram.atualizar(dados['ram']['pct'], f"Uso: {dados['ram']['usado']/1024**3:.1f} GB\nTotal: {dados['ram']['total']/1024**3:.1f} GB")
        self.card_disk.atualizar(dados['disk']['pct'], f"Livre: {dados['disk']['livre']/1024**3:.0f} GB\nTotal: {dados['disk']['total']/1024**3:.0f} GB")
        self.card_down.atualizar_velocidade(dados['net']['recv'])
        self.card_up.atualizar_velocidade(dados['net']['sent'])
        self.painel_proc.receber_dados(dados['procs'])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = DashboardFinal()
    janela.show()
    sys.exit(app.exec())
