#!/usr/bin/env python3
import sys
import psutil
import glob
import os
import time
import platform
import subprocess
import urllib.request
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
                             QLabel, QProgressBar, QFrame, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QMessageBox, QMenu, QLineEdit)
from PyQt6.QtCore import QTimer, Qt, QSettings, QThread, pyqtSignal, QPoint, QSize, QUrl
from PyQt6.QtGui import QColor, QCursor, QDesktopServices, QAction, QIcon, QPainter, QPainterPath, QPen

# VERSÃO ATUAL DO SOFTWARE
VERSAO_ATUAL = "1.1"
URL_VERSION = "https://raw.githubusercontent.com/juglesbass/AgildoMonitor/main/version.txt"

# ==========================================
# 🛠️ FUNÇÕES AUXILIARES
# ==========================================
def pegar_nome_cpu_real():
    try:
        with open("/proc/cpuinfo", "r") as f:
            for linha in f:
                if "model name" in linha:
                    nome = linha.split(":")[1].strip()
                    remover = ["Intel(R)", "Core(TM)", "CPU", "AMD", "Processor", "(R)", "(TM)"]
                    for item in remover:
                        nome = nome.replace(item, "")
                    return nome.strip()
    except:
        return "Processador"
    return "CPU Genérica"


def formatar_bytes(valor):
    try:
        valor = float(valor)
    except:
        return "0 B"
    unidades = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while valor >= 1024 and i < len(unidades) - 1:
        valor /= 1024
        i += 1
    return f"{valor:.1f} {unidades[i]}"


def ler_sysfs(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except:
        return None


def eh_gpu_amd(caminho_drm):
    vendor = ler_sysfs(caminho_drm + "/device/vendor")
    return vendor == "0x1002"


def pegar_nome_gpu_amd(caminho_drm):
    # Em AMD normalmente o nome bonito vem via lspci; se falhar, usa genérico.
    try:
        pci_id = os.path.basename(os.path.realpath(caminho_drm + "/device"))
        out = subprocess.check_output(["lspci", "-s", pci_id], stderr=subprocess.DEVNULL).decode()
        if "AMD" in out or "ATI" in out:
            nome = out.split(": ", 1)[-1].strip()
            nome = nome.replace("Advanced Micro Devices, Inc. [AMD/ATI]", "AMD")
            return nome
    except:
        pass
    return "AMD Radeon"


def pegar_temperaturas_nvme():
    resultados = []
    for hw in glob.glob("/sys/class/hwmon/hwmon*"):
        nome = ler_sysfs(hw + "/name")
        if not nome:
            continue
        if "nvme" not in nome.lower():
            continue
        melhor = None
        for temp_input in glob.glob(hw + "/temp*_input"):
            bruto = ler_sysfs(temp_input)
            if not bruto:
                continue
            try:
                valor = int(bruto) / 1000
            except:
                continue
            # ignora leituras absurdas
            if 0 < valor < 120:
                melhor = valor if melhor is None else max(melhor, valor)
        if melhor is not None:
            resultados.append(melhor)
    return resultados


def encurtar_nome_hardware(nome, limite=24):
    """Encurta nomes longos de hardware para caber melhor nos cards."""
    if not nome:
        return "Hardware"

    limpo = str(nome).strip()

    substituicoes = [
        ("Advanced Micro Devices, Inc. [AMD/ATI]", "AMD"),
        ("Advanced Micro Devices, Inc.", "AMD"),
        ("[AMD/ATI]", ""),
        ("AMD Radeon RX", "RX"),
        ("Radeon RX", "RX"),
        ("Radeon", ""),
        ("NVIDIA Corporation", "NVIDIA"),
        ("NVIDIA GeForce", "GeForce"),
        ("Intel(R)", "Intel"),
        ("Core(TM)", "Core"),
        ("Processor", ""),
        ("CPU", ""),
        ("(R)", ""),
        ("(TM)", ""),
        ("Discrete", ""),
        ("Graphics", ""),
    ]

    for antigo, novo in substituicoes:
        limpo = limpo.replace(antigo, novo)

    limpo = " ".join(limpo.split())
    partes = limpo.split()

    if len(partes) > 4:
        limpo = " ".join(partes[:4])

    if len(limpo) <= limite:
        return limpo

    return limpo[:limite - 1].rstrip() + "…"


def encurtar_nome_gpu(nome, limite=24):
    return encurtar_nome_hardware(nome, limite)


def formatar_vram_curta(usado, total):
    try:
        usado_gb = usado / (1024 ** 3)
        total_gb = total / (1024 ** 3)
        return f"VRAM {usado_gb:.1f}/{total_gb:.0f}G"
    except:
        return ""


# ==========================================
# 🧠 O CÉREBRO (Worker Thread)
# ==========================================
class WorkerThread(QThread):
    dados_atualizados = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.rodando = True
        self.nome_cpu = pegar_nome_cpu_real()
        self.tick = 0
        self.procs_cache = []

    def ler_arquivo(self, path):
        try:
            with open(path) as f:
                return f.read().strip()
        except:
            return None

    def ler_vram_amd(self, caminho):
        try:
            usado = int(self.ler_arquivo(caminho + "/device/mem_info_vram_used"))
            total = int(self.ler_arquivo(caminho + "/device/mem_info_vram_total"))
            return usado, total
        except:
            return 0, 0

    def tentar_nvidia(self):
        try:
            temp = subprocess.check_output(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"])
            uso = subprocess.check_output(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"])
            mem = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"])
            mem_u, mem_t = [int(x.strip()) for x in mem.decode().split(',')]
            return int(uso.strip()), int(temp.strip()), 0, mem_u * 1024*1024, mem_t * 1024*1024
        except:
            return None

    def run(self):
        while self.rodando:
            dados = {}
            dados['hora'] = datetime.now().strftime("%H:%M:%S")
            dados['uptime'] = str(timedelta(seconds=int(time.time() - psutil.boot_time())))

            # CPU Temp
            temps = psutil.sensors_temperatures()
            cpu_temp = 0
            if 'coretemp' in temps: cpu_temp = temps['coretemp'][0].current
            elif 'k10temp' in temps: cpu_temp = temps['k10temp'][0].current
            elif 'zenpower' in temps: cpu_temp = temps['zenpower'][0].current
            else:
                for name, entries in temps.items():
                    if len(entries) > 0:
                        cpu_temp = entries[0].current
                        break

            dados['cpu_nome'] = self.nome_cpu
            dados['cpu_temp'] = cpu_temp
            dados['cpu_pct'] = psutil.cpu_percent(interval=None)
            dados['cpu_cores'] = psutil.cpu_percent(interval=None, percpu=True)

            # GPU Logic & VRAM
            uso=0; edge=0; hot=0; vram_u=0; vram_t=0; nome_gpu = "GPU"
            dados_nvidia = self.tentar_nvidia()

            if dados_nvidia:
                uso, edge, hot, vram_u, vram_t = dados_nvidia
                nome_gpu = "NVIDIA GeForce"
            else:
                caminho_gpu = ""
                for c in glob.glob("/sys/class/drm/card[0-9]*"):
                    if not eh_gpu_amd(c):
                        continue
                    if os.path.exists(c + "/device/gpu_busy_percent"):
                        val = self.ler_arquivo(c + "/device/gpu_busy_percent")
                        if val is not None:
                            try:
                                uso = int(val)
                            except:
                                uso = 0
                            caminho_gpu = c
                            nome_gpu = pegar_nome_gpu_amd(c)
                            break

                if caminho_gpu:
                    vram_u, vram_t = self.ler_vram_amd(caminho_gpu)

                    # Primeiro tenta o hwmon ligado diretamente ao device da GPU correta.
                    hwmons = glob.glob(caminho_gpu + "/device/hwmon/hwmon*")
                    # Fallback para sistemas onde o link direto não aparece.
                    if not hwmons:
                        hwmons = [p for p in glob.glob("/sys/class/hwmon/hwmon*") if self.ler_arquivo(p + "/name") == "amdgpu"]

                    for p in hwmons:
                        if self.ler_arquivo(p + "/name") != "amdgpu":
                            continue
                        t1 = self.ler_arquivo(p + "/temp1_input")
                        if t1:
                            edge = int(t1) / 1000
                        t2 = self.ler_arquivo(p + "/temp2_input")
                        t3 = self.ler_arquivo(p + "/temp3_input")
                        hot = int(t2) / 1000 if (t2 and int(t2) > 0) else (int(t3) / 1000 if t3 else 0)
                        break

                    if edge == 0 and hot > 0:
                        edge = hot

            dados['gpu'] = {'nome': nome_gpu, 'uso': uso, 'edge': edge, 'hot': hot, 'vram_u': vram_u, 'vram_t': vram_t}

            # RAM/Disk/Net
            mem = psutil.virtual_memory()
            dados['ram'] = {'pct': mem.percent, 'usado': mem.used, 'total': mem.total}

            disk = psutil.disk_usage('/')
            nvme_temps = pegar_temperaturas_nvme()
            dados['disk'] = {
                'pct': disk.percent,
                'livre': disk.free,
                'total': disk.total,
                'nvme_temp': max(nvme_temps) if nvme_temps else 0
            }

            net = psutil.net_io_counters()
            dados['net'] = {'recv': net.bytes_recv, 'sent': net.bytes_sent}

            # Processos
            # Atualiza a lista completa com menos frequência para reduzir uso de CPU.
            if self.tick % 3 == 0:
                procs = []
                try:
                    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                        try:
                            p_info = p.info
                            nome = p_info.get('name') or ""
                            if not nome:
                                continue
                            if p_info.get('cpu_percent', 0) > 0 or p_info.get('memory_percent', 0) > 0.1:
                                procs.append(p_info)
                        except:
                            pass
                except:
                    pass
                self.procs_cache = procs

            dados['procs'] = self.procs_cache
            self.tick += 1

            self.dados_atualizados.emit(dados)
            for _ in range(20):
                if not self.rodando: return
                self.msleep(50)

    def parar(self):
        self.rodando = False

# ==========================================
# 📈 CLASSE DO GRÁFICO
# ==========================================
class MiniGrafico(QWidget):
    def __init__(self, cor, dinamico=False):
        super().__init__()
        self.cor = QColor(cor)
        self.dinamico = dinamico
        self.historico = [0] * 50
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def adicionar_valor(self, valor):
        self.historico.pop(0)
        self.historico.append(valor)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        if w == 0 or h == 0: return

        max_val = max(self.historico) * 1.1 if self.dinamico else 100.0
        if max_val <= 0: max_val = 1.0

        path = QPainterPath()
        step = w / (len(self.historico) - 1)

        for i, val in enumerate(self.historico):
            x = i * step
            y = h - (val / max_val) * h
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        fill_path = QPainterPath(path)
        fill_path.lineTo(w, h)
        fill_path.lineTo(0, h)
        fill_path.closeSubpath()

        cor_fundo = QColor(self.cor)
        cor_fundo.setAlpha(40)
        painter.fillPath(fill_path, cor_fundo)

        pen = QPen(self.cor, 2)
        painter.setPen(pen)
        painter.drawPath(path)

# ==========================================
# 🎨 CLASSES DE INTERFACE
# ==========================================
class PainelHardware(QFrame):
    def __init__(self, titulo, icone, cor, info_font_size=17):
        super().__init__()
        self.setStyleSheet(
            f"QFrame {{ background-color: #1a1b26; border-radius: 12px; border: 1px solid #333; }}"
            "QLabel { border: none; background-color: transparent; }"
        )

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Layout limpo: removi o mini gráfico interno dos cards de hardware.
        # Isso evita o texto ser espremido/ocultado.
        self.setMinimumHeight(155)
        self.setMaximumHeight(185)

        lbl_tit = QLabel(f"{icone}  {titulo}")
        lbl_tit.setStyleSheet(f"color: {cor}; font-size: 13px; font-weight: bold;")
        lbl_tit.setFixedHeight(22)
        layout.addWidget(lbl_tit)

        self.lbl_info = QLabel("...")
        self.lbl_info.setStyleSheet(
            f"color: white; font-size: {info_font_size}px; font-weight: bold;"
        )
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setTextFormat(Qt.TextFormat.PlainText)
        self.lbl_info.setMinimumHeight(76)
        self.lbl_info.setMaximumHeight(92)
        layout.addWidget(self.lbl_info, 1)

        self.lbl_porc = QLabel("0%")
        self.lbl_porc.setStyleSheet(f"color: {cor}; font-size: 13px; font-weight: bold;")
        self.lbl_porc.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_porc.setFixedHeight(18)
        layout.addWidget(self.lbl_porc)

        self.barra = QProgressBar()
        self.barra.setTextVisible(False)
        self.barra.setFixedHeight(8)
        self.barra.setStyleSheet(
            f"QProgressBar {{ background: #24283b; border-radius: 4px; }}"
            f"QProgressBar::chunk {{ background: {cor}; border-radius: 4px; }}"
        )
        layout.addWidget(self.barra)

    def atualizar(self, pct, texto):
        self.barra.setValue(int(pct))
        self.lbl_porc.setText(f"{pct:.1f}%")
        self.lbl_info.setText(texto)

class PainelRede(QFrame):
    def __init__(self, titulo, icone, cor):
        super().__init__()
        self.setStyleSheet(f"QFrame {{ background-color: #1a1b26; border-radius: 12px; border: 1px solid #333; }}")
        layout = QVBoxLayout(); self.setLayout(layout)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        self.setMinimumHeight(118)
        self.setMaximumHeight(150)

        lbl_tit = QLabel(f"{icone}  {titulo}")
        lbl_tit.setStyleSheet(f"color: {cor}; font-size: 13px; font-weight: bold;")
        layout.addWidget(lbl_tit)

        self.lbl_velocidade = QLabel("0 KB/s")
        self.lbl_velocidade.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        self.lbl_velocidade.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_velocidade)
        self.ultimo_valor = 0

        self.grafico = MiniGrafico(cor, dinamico=True)
        self.grafico.setFixedHeight(22)
        layout.addWidget(self.grafico)

    def atualizar_velocidade(self, valor_atual_bytes):
        if self.ultimo_valor == 0:
            self.ultimo_valor = valor_atual_bytes
            return

        diferenca = valor_atual_bytes - self.ultimo_valor
        self.ultimo_valor = valor_atual_bytes
        velocidade = diferenca / 1024

        if velocidade > 1024:
            texto = f"{velocidade/1024:.1f} MB/s"
            cor = "#2ecc71"
        else:
            texto = f"{velocidade:.1f} KB/s"
            cor = "white"

        self.lbl_velocidade.setText(texto)
        self.lbl_velocidade.setStyleSheet(f"color: {cor}; font-size: 22px; font-weight: bold;")
        self.grafico.adicionar_valor(velocidade)


class PainelCores(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("QFrame { background-color: #1a1b26; border-radius: 15px; border: 1px solid #333; } QLabel { border: none; background-color: transparent; }")
        self.layout_principal = QVBoxLayout()
        self.setLayout(self.layout_principal)

        titulo = QLabel("🧩  USO POR NÚCLEO")
        titulo.setStyleSheet("color: #7dcfff; font-size: 16px; font-weight: bold;")
        self.layout_principal.addWidget(titulo)

        self.grid_cores = QGridLayout()
        self.grid_cores.setSpacing(6)
        self.layout_principal.addLayout(self.grid_cores)

        self.barras = []

    def garantir_barras(self, total):
        if len(self.barras) == total:
            return

        while self.grid_cores.count():
            item = self.grid_cores.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.barras = []
        for i in range(total):
            lbl = QLabel(f"{i+1:02d}")
            lbl.setStyleSheet("color: #a9b1d6; font-size: 10px;")
            barra = QProgressBar()
            barra.setRange(0, 100)
            barra.setTextVisible(False)
            barra.setFixedHeight(8)
            barra.setStyleSheet("QProgressBar { background: #24283b; border-radius: 4px; } QProgressBar::chunk { background: #7dcfff; border-radius: 4px; }")
            col = i % 8
            row = (i // 8) * 2
            self.grid_cores.addWidget(lbl, row, col)
            self.grid_cores.addWidget(barra, row + 1, col)
            self.barras.append(barra)

    def atualizar(self, valores):
        if not valores:
            return
        self.garantir_barras(len(valores))
        for barra, valor in zip(self.barras, valores):
            barra.setValue(int(valor))

class MonitorProcessos(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #1a1b26; border-radius: 15px; border: 1px solid #333;")
        self.filtro_texto = ""

        layout = QVBoxLayout()
        self.setLayout(layout)

        topo = QHBoxLayout()
        titulo = QLabel("GERENCIADOR DE TAREFAS")
        titulo.setStyleSheet("color: #a9b1d6; font-weight: bold;")
        topo.addWidget(titulo)
        topo.addStretch()

        self.barra_busca = QLineEdit()
        self.barra_busca.setPlaceholderText("Buscar processo...")
        self.barra_busca.setFixedWidth(220)
        self.barra_busca.setStyleSheet("QLineEdit { background: #24283b; color: white; border: 1px solid #414868; border-radius: 6px; padding: 4px; }")
        self.barra_busca.textChanged.connect(self.atualizar_filtro)
        topo.addWidget(self.barra_busca)

        layout.addLayout(topo)

        corpo = QHBoxLayout()
        corpo.setSpacing(10)
        layout.addLayout(corpo)

        self.tabela_cpu = self.criar_tabela("PROCESSADOR")
        self.tabela_ram = self.criar_tabela("MEMÓRIA RAM")

        corpo.addWidget(self.tabela_cpu)
        corpo.addWidget(self.tabela_ram)

    def criar_tabela(self, titulo):
        tabela = QTableWidget()
        tabela.setColumnCount(3)
        tabela.setHorizontalHeaderLabels([titulo, "USO", "KILL"])
        tabela.verticalHeader().setVisible(False)
        tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        tabela.setStyleSheet("""
            QTableWidget {
                background: #16161e;
                color: white;
                border: 1px solid #24283b;
                border-radius: 8px;
                gridline-color: #24283b;
            }
            QHeaderView::section {
                background: #24283b;
                color: #7aa2f7;
                font-weight: bold;
                padding: 4px;
                border: none;
            }
        """)
        return tabela

    def atualizar_filtro(self, texto):
        self.filtro_texto = texto.lower()

    def matar(self, pid):
        try:
            proc = psutil.Process(pid)
            resp = QMessageBox.question(
                self,
                "Finalizar processo",
                f"Deseja finalizar o processo?\\n\\n{proc.name()} (PID {pid})",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resp == QMessageBox.StandardButton.Yes:
                proc.kill()
        except:
            pass

    def preencher_tabela(self, tabela, procs, tipo):
        limite = 6
        tabela.setRowCount(len(procs[:limite]))

        for i, p in enumerate(procs[:limite]):
            nome = str(p.get('name', ''))
            pid = int(p.get('pid', 0))
            cpu = float(p.get('cpu_percent', 0))
            ram = float(p.get('memory_percent', 0))

            uso = cpu if tipo == "cpu" else ram

            tabela.setItem(i, 0, QTableWidgetItem(nome))
            tabela.setItem(i, 1, QTableWidgetItem(f"{uso:.1f}%"))

            cor = QColor("#ff5555") if (cpu > 20 or ram > 10) else QColor("white")
            for c in range(2):
                item = tabela.item(i, c)
                if item:
                    item.setForeground(cor)

            btn = QPushButton("💀")
            btn.setFixedSize(30, 20)
            btn.setStyleSheet("background: #c0392b; border: none; border-radius: 4px;")
            btn.clicked.connect(lambda ch, pid=pid: self.matar(pid))
            tabela.setCellWidget(i, 2, btn)

    def receber_dados(self, procs):
        if self.filtro_texto:
            procs = [p for p in procs if self.filtro_texto in str(p.get('name', '')).lower()]

        procs_cpu = sorted(procs, key=lambda x: x.get('cpu_percent', 0), reverse=True)
        procs_ram = sorted(procs, key=lambda x: x.get('memory_percent', 0), reverse=True)

        self.preencher_tabela(self.tabela_cpu, procs_cpu, "cpu")
        self.preencher_tabela(self.tabela_ram, procs_ram, "ram")

# ==========================================
# 🖥️ JANELA PRINCIPAL
# ==========================================
class DashboardFinal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agildo Monitor Ultimate")
        self.modo_compacto = False
        self.setStyleSheet("""
            QWidget { background-color: #131313; }
            QMenu { background-color: #1a1b26; border: 1px solid #414868; }
            QMenu::item { padding: 8px 20px; color: #c0caf5; }
            QMenu::item:selected { background-color: #7aa2f7; color: #15161e; }
        """)

        # Alterado para V14 para forçar o reset do tamanho bugado
        self.settings = QSettings("AgildoSystems", "MonitorUniversal_V14")
        self.tamanho_normal = self.settings.value("size", QSize(1000, 620))

        self.resize(self.tamanho_normal)
        self.move(self.settings.value("pos", QPoint(50, 50)))

        self.is_on_top = self.settings.value("ontop", False, type=bool)
        if self.is_on_top:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        QTimer.singleShot(100, self.forcar_posicao)

        self.main_layout = QVBoxLayout(); self.setLayout(self.main_layout)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(8)

        # Barra Superior
        self.status_bar = QFrame()
        self.status_bar.setStyleSheet("background-color: #1a1b26; border-radius: 10px; border: 1px solid #333;")
        self.status_bar.setFixedHeight(42)
        status_layout = QHBoxLayout(self.status_bar)

        k = platform.release().split('-')[0]
        self.lbl_sys = QLabel(f"🐧 CachyOS Linux • Kernel {k}")
        self.lbl_sys.setStyleSheet("color: #7aa2f7; font-size: 13px; font-weight: bold; border: none;")
        status_layout.addWidget(self.lbl_sys)
        status_layout.addStretch()

        self.lbl_uptime = QLabel("Ligado há: ...")
        self.lbl_uptime.setStyleSheet("color: #e0af68; font-size: 13px; font-weight: bold; border: none;")
        status_layout.addWidget(self.lbl_uptime)
        status_layout.addStretch()

        # Botão MODO COMPACTO
        self.btn_compacto = QPushButton("🔽")
        self.btn_compacto.setToolTip("Alternar Modo Overlay")
        self.btn_compacto.setFixedSize(34, 28)
        self.btn_compacto.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_compacto.setStyleSheet("QPushButton { background-color: #24283b; color: #9ece6a; font-size: 20px; border-radius: 5px; } QPushButton:hover { background-color: #414868; }")
        self.btn_compacto.clicked.connect(self.alternar_modo_compacto)
        status_layout.addWidget(self.btn_compacto)

        status_layout.addSpacing(5)

        # Botão MENU
        self.btn_menu = QPushButton("☰")
        self.btn_menu.setFixedSize(34, 28)
        self.btn_menu.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_menu.setStyleSheet("QPushButton { background-color: transparent; color: #c0caf5; font-size: 24px; border: none; } QPushButton:hover { color: #7aa2f7; }")
        self.btn_menu.clicked.connect(self.mostrar_menu)
        status_layout.addWidget(self.btn_menu)

        status_layout.addSpacing(10)
        self.lbl_clock = QLabel("00:00:00")
        self.lbl_clock.setStyleSheet("color: #2ecc71; font-size: 20px; font-weight: bold; border: none;")
        status_layout.addWidget(self.lbl_clock)
        self.main_layout.addWidget(self.status_bar)

        # Grid
        self.grid = QGridLayout()
        self.grid.setSpacing(7)
        self.main_layout.addLayout(self.grid)

        self.card_cpu = PainelHardware("PROCESSADOR", "🧠", "#7aa2f7", info_font_size=17); self.grid.addWidget(self.card_cpu, 0, 0)
        self.card_gpu = PainelHardware("PLACA DE VÍDEO", "🎮", "#bb9af7", info_font_size=15); self.grid.addWidget(self.card_gpu, 0, 1)
        self.card_ram = PainelHardware("MEMÓRIA RAM", "⚡", "#e0af68"); self.grid.addWidget(self.card_ram, 0, 2)
        self.card_disk = PainelHardware("DISCO (SSD)", "💾", "#9ece6a"); self.grid.addWidget(self.card_disk, 1, 0)
        self.card_down = PainelRede("DOWNLOAD", "⬇️", "#2ecc71"); self.grid.addWidget(self.card_down, 1, 1)
        self.card_up = PainelRede("UPLOAD", "⬆️", "#3498db"); self.grid.addWidget(self.card_up, 1, 2)

        self.card_cores = PainelCores()
        self.card_cores.setMinimumHeight(58)
        self.grid.addWidget(self.card_cores, 2, 0, 1, 3)

        self.painel_proc = MonitorProcessos()
        # DEIXOU DE SER FIXO: Agora ele tem altura mínima e pode esticar ou encolher
        self.painel_proc.setMinimumHeight(175)
        self.main_layout.addWidget(self.painel_proc, 0)

        self.thread = WorkerThread()
        self.thread.dados_atualizados.connect(self.atualizar_interface)
        self.thread.start()

    # ==============================================
    # 🍔 LÓGICA DO MENU E MODO COMPACTO
    # ==============================================
    def alternar_modo_compacto(self):
        self.modo_compacto = not self.modo_compacto

        visivel = not self.modo_compacto

        self.card_disk.setVisible(visivel)
        self.card_down.setVisible(visivel)
        self.card_up.setVisible(visivel)
        self.painel_proc.setVisible(visivel)

        self.card_cpu.grafico.setVisible(visivel)
        self.card_gpu.grafico.setVisible(visivel)
        self.card_ram.grafico.setVisible(visivel)
        self.card_cores.setVisible(visivel)

        if self.modo_compacto:
            self.tamanho_normal = self.size() # Salva o tamanho atual antes de encolher
            self.btn_compacto.setText("🔼")
            self.lbl_uptime.hide()
            self.lbl_sys.hide()
            self.setMinimumSize(0, 0)
            self.resize(560, 135)
        else:
            self.btn_compacto.setText("🔽")
            self.lbl_uptime.show()
            self.lbl_sys.show()
            self.resize(self.tamanho_normal) # Restaura para o tamanho que estava antes

    def mostrar_menu(self):
        menu = QMenu(self)

        acao_update = QAction("🔄  Verificar Atualizações", self)
        acao_update.triggered.connect(self.checar_updates)
        menu.addAction(acao_update)

        acao_topo = QAction("📌  Sempre no Topo (Ideal para Jogos)", self)
        acao_topo.setCheckable(True)
        acao_topo.setChecked(self.is_on_top)
        acao_topo.triggered.connect(self.toggle_topo)
        menu.addAction(acao_topo)

        menu.addSeparator()

        acao_sobre = QAction("ℹ️  Sobre", self)
        acao_sobre.triggered.connect(self.abrir_sobre)
        menu.addAction(acao_sobre)

        acao_sair = QAction("❌  Sair", self)
        acao_sair.triggered.connect(self.close)
        menu.addAction(acao_sair)

        menu.exec(self.btn_menu.mapToGlobal(QPoint(0, self.btn_menu.height())))

    def toggle_topo(self, checked):
        self.is_on_top = checked
        if checked: self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        else: self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self.show()
        self.settings.setValue("ontop", checked)

    def checar_updates(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            with urllib.request.urlopen(URL_VERSION) as response:
                versao_remota = response.read().decode('utf-8').strip()
            QApplication.restoreOverrideCursor()
            if versao_remota != VERSAO_ATUAL:
                res = QMessageBox.question(self, "Atualização Disponível!",
                                     f"Nova versão: {versao_remota}\nSua versão: {VERSAO_ATUAL}\n\nDeseja ir para a página de download?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if res == QMessageBox.StandardButton.Yes:
                    QDesktopServices.openUrl(QUrl("https://github.com/juglesbass/AgildoMonitor/releases"))
            else:
                QMessageBox.information(self, "Tudo Certo", f"Você já tem a versão mais recente ({VERSAO_ATUAL}).")
        except:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "Erro de Conexão", "Não foi possível verificar. Cheque sua internet.")

    def abrir_sobre(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Sobre")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet("QMessageBox { background-color: #1a1b26; color: white; } QLabel { color: white; } QPushButton { background-color: #7aa2f7; color: #1a1b26; font-weight: bold; border-radius: 5px; padding: 5px; }")

        texto = f"""
        <h3 style='color: #7aa2f7;'>Agildo Monitor Ultimate</h3>
        <p><b>Versão {VERSAO_ATUAL}</b> - CachyOS Edition</p>
        <p>Desenvolvido por: <b style='color: #e0af68;'>Agildo Gomes</b></p>
        <p><a href='https://github.com/juglesbass/AgildoMonitor' style='color: #bb9af7;'>Visite o GitHub</a></p>
        """
        msg.setText(texto)
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        msg.exec()

    def forcar_posicao(self):
        pos = self.settings.value("pos")
        if pos: self.move(pos)

    def closeEvent(self, event):
        self.thread.parar()
        self.thread.wait(100)
        if not self.modo_compacto:
            self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        event.accept()

    def atualizar_interface(self, dados):
        self.lbl_clock.setText(dados['hora'])
        self.lbl_uptime.setText(f"Ligado há: {dados['uptime']}")
        self.card_cpu.atualizar(dados['cpu_pct'], f"{encurtar_nome_hardware(dados['cpu_nome'], 32)}\n{dados['cpu_temp']:.0f}°C")
        self.card_cores.atualizar(dados.get('cpu_cores', []))

        texto_gpu = "GPU Desconhecida\nSem Driver"
        if dados['gpu']['nome'] != "GPU":
            nome_gpu_curto = encurtar_nome_gpu(dados['gpu']['nome'], 34)
            self.card_gpu.setToolTip(dados['gpu']['nome'])

            temp_txt = f"{dados['gpu']['edge']:.0f}°C"
            vram_txt = ""
            if dados['gpu'].get('vram_t', 0) > 0:
                vram_txt = "  " + formatar_vram_curta(dados['gpu']['vram_u'], dados['gpu']['vram_t'])

            if vram_txt:
                texto_gpu = f"{nome_gpu_curto}\n{temp_txt}\n{vram_txt.strip()}"
            else:
                texto_gpu = f"{nome_gpu_curto}\n{temp_txt}"

        self.card_gpu.atualizar(dados['gpu']['uso'] if dados['gpu']['nome'] != "GPU" else 0, texto_gpu)

        self.card_ram.atualizar(dados['ram']['pct'], f"Uso: {dados['ram']['usado']/1024**3:.1f} GB\nTotal: {dados['ram']['total']/1024**3:.1f} GB")
        nvme_extra = f"\nNVMe: {dados['disk']['nvme_temp']:.0f}°C" if dados['disk'].get('nvme_temp', 0) else ""
        self.card_disk.atualizar(dados['disk']['pct'], f"Livre: {dados['disk']['livre']/1024**3:.0f} GB\nTotal: {dados['disk']['total']/1024**3:.0f} GB{nvme_extra}")
        self.card_down.atualizar_velocidade(dados['net']['recv'])
        self.card_up.atualizar_velocidade(dados['net']['sent'])
        self.painel_proc.receber_dados(dados['procs'])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setDesktopFileName("AgildoMonitor")
    app.setApplicationName("AgildoMonitor")
    if os.path.exists("icone.png"):
        app.setWindowIcon(QIcon("icone.png"))

    janela = DashboardFinal()
    janela.show()
    sys.exit(app.exec())
