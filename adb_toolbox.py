import os
import io
import re
import sys
import json
import time
import shlex
import shutil
import socket
import tempfile
import threading
import subprocess
import datetime
import posixpath
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

APP_NAME = "ADB Toolbox"
APP_VERSION = "1.1"
APP_VENDOR = "keesp"

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".adb_toolbox")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

FILA_CARGANDO = "~cargando"

XML_MAX = 1024 * 1024

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

COLOR_BG = "#28282C"
COLOR_CARD = "#1E1E22"
COLOR_CHROME = "#2C2C31"
COLOR_BISEL = "#37373E"
COLOR_BISEL_HOVER = "#43434C"
COLOR_RAISED = "#3A3A42"
COLOR_BORDER = "#45454E"
COLOR_BORDER_SOFT = "#32323A"

COLOR_TEXT = "#F2F2F5"
COLOR_MUTED = "#A0A0A9"
COLOR_FAINT = "#76767F"

COLOR_ACCENT = "#0A84FF"
COLOR_ACCENT_HOVER = "#2E97FF"
COLOR_ACCENT_SOFT = "#1C3A5E"
COLOR_GREEN = "#2E9E4F"
COLOR_GREEN_HOVER = "#37B25B"
COLOR_RED = "#D0342C"
COLOR_RED_HOVER = "#E24A40"
COLOR_AMBER = "#E9A23B"
COLOR_AMBER_HOVER = "#F0B457"
COLOR_OK = "#30D158"
COLOR_FAIL = "#FF453A"

RADIO_BOTON = 8
RADIO_TARJETA = 12

FAMILIAS_UI = ("SF Pro Text", "SF Pro Display", "Helvetica Neue", "Segoe UI",
               "Roboto")
FAMILIAS_MONO = ("SF Mono", "Menlo", "Cascadia Mono", "Consolas")
FUENTE = "Segoe UI"
FUENTE_MONO = "Consolas"

TIPO = {
    "titulo": (18, "bold"),
    "seccion": (12, "bold"),
    "cuerpo": (13, "normal"),
    "dato": (12, "normal"),
    "menudo": (11, "normal"),
    "mono": (12, "normal"),
}

BUTTON_COLORS = {
    "accent": (COLOR_BISEL, COLOR_BISEL_HOVER, COLOR_TEXT, COLOR_BORDER),
    "green": (COLOR_GREEN, COLOR_GREEN_HOVER, "#ffffff", None),
    "amber": (COLOR_BISEL, "#443A29", COLOR_AMBER, "#4E4433"),
    "red": (COLOR_BISEL, "#452C2B", "#FF6B60", "#503534"),
    "muted": ("transparent", COLOR_BISEL, COLOR_MUTED, COLOR_BORDER),
    "record": ("transparent", COLOR_RAISED, COLOR_TEXT, None),
    "primary": (COLOR_ACCENT, COLOR_ACCENT_HOVER, "#ffffff", None),
}

_ICONO_CACHE = {}
_LIENZO = 96
_TRAZO = 6

def _ico_camara(d):
    d.rounded_rectangle((8, 26, 88, 84), 10, outline=255, width=_TRAZO)
    d.line((34, 26, 40, 14), fill=255, width=_TRAZO)
    d.line((62, 26, 56, 14), fill=255, width=_TRAZO)
    d.line((40, 14, 56, 14), fill=255, width=_TRAZO)
    d.ellipse((33, 40, 63, 70), outline=255, width=_TRAZO)

def _ico_panel(d):
    d.rounded_rectangle((10, 12, 86, 84), 10, outline=255, width=_TRAZO)
    d.line((30, 64, 30, 44), fill=255, width=_TRAZO)
    d.line((48, 64, 48, 30), fill=255, width=_TRAZO)
    d.line((66, 64, 66, 52), fill=255, width=_TRAZO)

def _ico_ajustes(d):
    for y in (28, 68):
        d.line((12, y, 84, y), fill=255, width=_TRAZO)
    d.ellipse((28, 14, 56, 42), outline=255, width=_TRAZO)
    d.ellipse((48, 54, 76, 82), outline=255, width=_TRAZO)

def _ico_paquete(d):
    d.rounded_rectangle((12, 26, 84, 84), 8, outline=255, width=_TRAZO)
    d.line((12, 44, 84, 44), fill=255, width=_TRAZO)
    d.line((48, 26, 48, 44), fill=255, width=_TRAZO)
    d.line((26, 12, 70, 12), fill=255, width=_TRAZO)
    d.line((26, 12, 14, 26), fill=255, width=_TRAZO)
    d.line((70, 12, 82, 26), fill=255, width=_TRAZO)

def _ico_carpeta(d):
    d.line((10, 78, 10, 22), fill=255, width=_TRAZO)
    d.line((10, 22, 40, 22), fill=255, width=_TRAZO)
    d.line((40, 22, 48, 34), fill=255, width=_TRAZO)
    d.line((48, 34, 86, 34), fill=255, width=_TRAZO)
    d.line((86, 34, 86, 78), fill=255, width=_TRAZO)
    d.line((10, 78, 86, 78), fill=255, width=_TRAZO)

def _ico_documento(d):
    d.line((20, 10, 60, 10), fill=255, width=_TRAZO)
    d.line((60, 10, 78, 30), fill=255, width=_TRAZO)
    d.line((78, 30, 78, 86), fill=255, width=_TRAZO)
    d.line((20, 10, 20, 86), fill=255, width=_TRAZO)
    d.line((20, 86, 78, 86), fill=255, width=_TRAZO)
    for y in (44, 58, 72):
        d.line((34, y, 64, y), fill=255, width=_TRAZO - 1)

def _ico_energia(d):
    d.arc((16, 20, 80, 84), 305, 235, fill=255, width=_TRAZO)
    d.line((48, 8, 48, 44), fill=255, width=_TRAZO)

def _ico_wifi(d):
    for caja, ancho in (((6, 18, 90, 102), _TRAZO), ((22, 34, 74, 86), _TRAZO)):
        d.arc(caja, 200, 340, fill=255, width=ancho)
    d.ellipse((41, 68, 55, 82), fill=255)

def _ico_tv(d):
    d.rounded_rectangle((8, 20, 88, 72), 8, outline=255, width=_TRAZO)
    d.line((32, 86, 64, 86), fill=255, width=_TRAZO)
    d.line((48, 72, 48, 86), fill=255, width=_TRAZO)

def _ico_mando(d):
    d.rounded_rectangle((6, 30, 90, 76), 16, outline=255, width=_TRAZO)
    d.line((22, 53, 42, 53), fill=255, width=_TRAZO - 1)
    d.line((32, 43, 32, 63), fill=255, width=_TRAZO - 1)
    d.ellipse((60, 46, 72, 58), fill=255)
    d.ellipse((72, 58, 84, 70), fill=255)

def _ico_refrescar(d):
    import math
    centro, radio, fin = 48, 33, 310
    d.arc((centro - radio, centro - radio, centro + radio, centro + radio),
          10, fin, fill=255, width=_TRAZO)
    a = math.radians(fin)
    x, y = centro + radio * math.cos(a), centro + radio * math.sin(a)
    t = a + math.pi / 2
    d.polygon([(x + 16 * math.cos(t), y + 16 * math.sin(t)),
               (x + 14 * math.cos(t + 2.3), y + 14 * math.sin(t + 2.3)),
               (x + 14 * math.cos(t - 2.3), y + 14 * math.sin(t - 2.3))], fill=255)

def _ico_engranaje(d):
    import math
    for i in range(8):
        a = math.radians(i * 45)
        d.line((48 + 24 * math.cos(a), 48 + 24 * math.sin(a),
                48 + 43 * math.cos(a), 48 + 43 * math.sin(a)),
               fill=255, width=14)
    d.ellipse((18, 18, 78, 78), fill=255)
    d.ellipse((36, 36, 60, 60), fill=0)

def _ico_chevron(d):
    d.line((22, 36, 48, 62), fill=255, width=_TRAZO + 1)
    d.line((48, 62, 74, 36), fill=255, width=_TRAZO + 1)

def _ico_chevron_arriba(d):
    d.line((22, 60, 48, 34), fill=255, width=_TRAZO + 1)
    d.line((48, 34, 74, 60), fill=255, width=_TRAZO + 1)

def _ico_copiar(d):
    d.rounded_rectangle((10, 10, 62, 62), 8, outline=255, width=_TRAZO)
    d.rounded_rectangle((34, 34, 86, 86), 8, outline=255, width=_TRAZO)

def _ico_papelera(d):
    d.line((14, 26, 82, 26), fill=255, width=_TRAZO)
    d.rounded_rectangle((24, 26, 72, 86), 6, outline=255, width=_TRAZO)
    d.line((38, 14, 58, 14), fill=255, width=_TRAZO)

def _ico_conectar(d):
    d.ellipse((10, 40, 34, 64), outline=255, width=_TRAZO)
    d.ellipse((62, 40, 86, 64), outline=255, width=_TRAZO)
    d.line((34, 52, 62, 52), fill=255, width=_TRAZO)

ICONOS = {
    "camara": _ico_camara, "panel": _ico_panel, "ajustes": _ico_ajustes,
    "paquete": _ico_paquete, "carpeta": _ico_carpeta, "documento": _ico_documento,
    "energia": _ico_energia, "wifi": _ico_wifi, "tv": _ico_tv, "mando": _ico_mando,
    "refrescar": _ico_refrescar, "engranaje": _ico_engranaje,
    "chevron": _ico_chevron, "chevron_arriba": _ico_chevron_arriba,
    "copiar": _ico_copiar, "papelera": _ico_papelera, "conectar": _ico_conectar,
}

def _elegir_fuentes(raiz):
    global FUENTE, FUENTE_MONO
    from tkinter import font as tkfont
    try:
        hay = set(tkfont.families(raiz))
    except Exception:
        return
    FUENTE = next((f for f in FAMILIAS_UI if f in hay), FUENTE)
    FUENTE_MONO = next((f for f in FAMILIAS_MONO if f in hay), FUENTE_MONO)

def icono(nombre, tam=18, color=COLOR_TEXT):
    clave = (nombre, tam, color)
    if clave in _ICONO_CACHE:
        return _ICONO_CACHE[clave]
    from PIL import Image, ImageDraw
    mascara = Image.new("L", (_LIENZO, _LIENZO), 0)
    ICONOS[nombre](ImageDraw.Draw(mascara))
    mascara = mascara.resize((tam, tam), Image.LANCZOS)
    img = Image.new("RGBA", (tam, tam), color)
    img.putalpha(mascara)
    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(tam, tam))
    _ICONO_CACHE[clave] = ctk_img
    return ctk_img

TVBOX_PKG = "com.keesp.signage"
TVBOX_NTP = "time.google.com"
TVBOX_MODE = "1080p60hz"
TVBOX_FB = "1920x1080"
TVBOX_DENSITY = "320"
TVBOX_MAX_DESFASE = 300

TVBOX_MODES = ["1080p60hz", "1080p50hz", "720p60hz", "720p50hz",
               "2160p60hz", "2160p30hz", "576p50hz", "480p60hz"]

SYS_DISPLAY_MODE = "/sys/class/display/mode"
SYS_DISP_CAP = "/sys/class/amhdmitx/amhdmitx0/disp_cap"

CMD_VERSIONES = ("for p in $(pm list packages %s | cut -d: -f2); do "
                 "echo PKG:$p; "
                 "dumpsys package $p | grep -m2 -e versionCode= -e versionName=; "
                 "done")

PROPS_SERIE = ("persist.sys.serialno", "persist.sys.sn", "ro.serialno",
               "ro.boot.serialno", "ro.boot.sn", "ril.serialnumber", "gsm.serial")
PROPS_COMPILACION = ("ro.build.display.id", "ro.build.id",
                     "ro.build.version.incremental")
PROPS_FIRMWARE = ("ro.build.software.version", "ro.vendor.build.version",
                  "ro.fota.version", "ro.build.version.custom", "ro.imagename")
PROPS_CID = ("ro.cid", "ro.boot.cid", "persist.sys.cid", "ro.vendor.cid",
             "persist.vendor.cid", "ro.product.cid", "ro.config.cid")

OCUPACION_AVISO = 0.70
OCUPACION_CRITICA = 0.90

LOG_VENDOR_DIRS = ("/data/Syslog", "/sdcard/ylog")
TMP_EQUIPO = "/data/local/tmp"

BATERIA_ESTADO = {"1": "desconocido", "2": "cargando", "3": "descargando",
                  "4": "sin cargar", "5": "llena"}
BATERIA_SALUD = {"1": "desconocida", "2": "buena", "3": "sobrecalentada",
                 "4": "muerta", "5": "sobretensión", "6": "fallo", "7": "fría"}

SDK_A_ANDROID = {
    "21": "5.0", "22": "5.1", "23": "6.0", "24": "7.0", "25": "7.1",
    "26": "8.0", "27": "8.1", "28": "9", "29": "10", "30": "11",
    "31": "12", "32": "12", "33": "13", "34": "14", "35": "15",
}

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

def find_adb(configured=None):
    candidates = []
    if configured:
        candidates.append(configured)

    on_path = shutil.which("adb")
    if on_path:
        candidates.append(on_path)

    local = os.environ.get("LOCALAPPDATA", "")
    userprofile = os.environ.get("USERPROFILE", "")
    common = [
        os.path.join(local, "Android", "Sdk", "platform-tools", "adb.exe"),
        os.path.join(userprofile, "AppData", "Local", "Android", "Sdk",
                     "platform-tools", "adb.exe"),
        r"C:\Android\platform-tools\adb.exe",
        r"C:\platform-tools\adb.exe",
        os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                     "platform-tools", "adb.exe"),
        os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "adb.exe"),
    ]
    candidates.extend(common)

    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None

def find_scrcpy(configured=None):
    candidates = []
    if configured:
        candidates.append(configured)

    on_path = shutil.which("scrcpy")
    if on_path:
        candidates.append(on_path)

    local = os.environ.get("LOCALAPPDATA", "")
    userprofile = os.environ.get("USERPROFILE", "")
    appdir = os.path.dirname(os.path.abspath(sys.argv[0]))
    common = [
        os.path.join(appdir, "scrcpy.exe"),
        os.path.join(appdir, "scrcpy", "scrcpy.exe"),
        os.path.join(appdir, "platform-tools", "scrcpy.exe"),
        r"C:\scrcpy\scrcpy.exe",
        os.path.join(local, "scrcpy", "scrcpy.exe"),
        os.path.join(userprofile, "scoop", "apps", "scrcpy", "current", "scrcpy.exe"),
        r"C:\ProgramData\chocolatey\bin\scrcpy.exe",
    ]
    candidates.extend(common)

    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None

def image_to_clipboard(pil_image):
    import ctypes
    from ctypes import wintypes

    output = io.BytesIO()
    pil_image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    CF_DIB = 8
    GMEM_MOVEABLE = 0x0002

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32

    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [wintypes.UINT, ctypes.c_void_p]

    h_global = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not h_global:
        raise RuntimeError("GlobalAlloc falló")
    ptr = kernel32.GlobalLock(h_global)
    ctypes.memmove(ptr, data, len(data))
    kernel32.GlobalUnlock(h_global)

    if not user32.OpenClipboard(None):
        raise RuntimeError("No se pudo abrir el portapapeles")
    try:
        user32.EmptyClipboard()
        user32.SetClipboardData(CF_DIB, h_global)
    finally:
        user32.CloseClipboard()

class ADBToolbox(ctk.CTk):
    def __init__(self):
        super().__init__()

        _ICONO_CACHE.clear()
        self._fuentes = {}
        self.cfg = load_config()
        self.consola_abierta = self.cfg.get("consola_abierta", True)
        self.adb_path = find_adb(self.cfg.get("adb_path"))
        self.scrcpy_path = find_scrcpy(self.cfg.get("scrcpy_path"))
        self.selected_serial = None
        self.device_map = {}

        self.recording = False
        self._rec_proc = None
        self._rec_remote = "/sdcard/adbtoolbox_rec.mp4"
        self._rec_timer = None

        self.current_path = "/sdcard/"
        self._files_carga = 0

        self.cmd_hist = []
        self.cmd_hist_idx = 0

        self.tvbox_pkg = self.cfg.get("tvbox_pkg", TVBOX_PKG)
        self._tv_busy = False

        default_shots = os.path.join(
            os.path.expanduser("~"), "Pictures", "ADB_Toolbox")
        self.screenshot_dir = self.cfg.get("screenshot_dir", default_shots)

        default_logs = os.path.join(
            os.path.expanduser("~"), "Documents", "ADB_Toolbox", "registros")
        self.log_dir = self.cfg.get("log_dir", default_logs)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self._aplicar_tema()
        self.title(f"{APP_NAME} — {APP_VENDOR}")
        self.geometry("940x760")
        self.minsize(820, 640)
        self.configure(fg_color=COLOR_BG)
        self.after(30, self._cromo_windows)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._build_log()

        self.log(f"{APP_NAME} v{APP_VERSION} de {APP_VENDOR} iniciado.")
        if self.adb_path:
            self.log(f"ADB encontrado: {self.adb_path}")
            self.refresh_devices()
        else:
            self.log("ADB no encontrado. Usa 'Configurar ADB' para localizar adb.exe.")
            self.after(400, self.prompt_configure_adb)

    def _cromo_windows(self, ventana=None):
        if os.name != "nt":
            return
        ventana = ventana or self
        ventana.update_idletasks()
        try:
            import ctypes
            from ctypes import wintypes

            def colorref(hexa):
                r, g, b = (int(hexa[i:i + 2], 16) for i in (1, 3, 5))
                return ctypes.c_int((b << 16) | (g << 8) | r)

            hwnd = (ctypes.windll.user32.GetParent(ventana.winfo_id())
                    or ventana.winfo_id())
            poner = ctypes.windll.dwmapi.DwmSetWindowAttribute
            for atributo, valor in ((20, ctypes.c_int(1)),
                                    (33, ctypes.c_int(2)),
                                    (35, colorref(COLOR_CHROME)),
                                    (36, colorref(COLOR_TEXT)),
                                    (34, colorref(COLOR_BORDER))):
                poner(wintypes.HWND(hwnd), atributo, ctypes.byref(valor), 4)
        except Exception:
            pass

    def _boton_icono(self, parent, ico, command, ayuda=None, color=None, tam=34):
        boton = ctk.CTkButton(
            parent, text="", width=tam, height=tam, corner_radius=RADIO_BOTON,
            image=icono(ico, 17, color or COLOR_MUTED),
            fg_color=COLOR_BISEL, hover_color=COLOR_BISEL_HOVER,
            border_width=1, border_color=COLOR_BORDER, command=command)
        if ayuda:
            self._ayuda(boton, ayuda)
        return boton

    def _ayuda(self, widget, texto):
        estado = {"win": None}

        def mostrar(_=None):
            if estado["win"]:
                return
            win = tk.Toplevel(widget)
            win.wm_overrideredirect(True)
            win.configure(background=COLOR_BORDER)
            tk.Label(win, text=texto, background=COLOR_BISEL, foreground=COLOR_TEXT,
                     font=(FUENTE, 9), padx=9, pady=5, bd=0).pack(padx=1, pady=1)
            win.update_idletasks()
            x = widget.winfo_rootx() + widget.winfo_width() // 2 - win.winfo_width() // 2
            win.wm_geometry("+%d+%d" % (x, widget.winfo_rooty() +
                                        widget.winfo_height() + 6))
            estado["win"] = win

        def ocultar(_=None):
            if estado["win"]:
                estado["win"].destroy()
                estado["win"] = None

        widget.bind("<Enter>", mostrar, add="+")
        widget.bind("<Leave>", ocultar, add="+")
        widget.bind("<ButtonPress>", ocultar, add="+")

    def _separador(self, parent, color=COLOR_BORDER, **grid):
        linea = tk.Frame(parent, height=1, bg=color, bd=0, highlightthickness=0)
        linea.grid(**grid)
        return linea

    def _dato_copiable(self, parent, texto="—"):
        campo = ctk.CTkEntry(parent, height=20, width=40, border_width=0,
                             corner_radius=0, fg_color="transparent",
                             text_color=COLOR_TEXT, font=self._fuente("dato"))
        campo._entry.configure(selectbackground=COLOR_ACCENT,
                               selectforeground="#ffffff")
        self._poner_dato(campo, texto)
        return campo

    @staticmethod
    def _poner_dato(campo, texto):
        campo.configure(state="normal")
        campo.delete(0, "end")
        campo.insert(0, texto)
        campo.configure(state="readonly")

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=COLOR_CHROME, corner_radius=0,
                              height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        marca = ctk.CTkFrame(header, fg_color="transparent")
        marca.grid(row=0, column=0, padx=(18, 0), pady=10, sticky="w")
        ctk.CTkLabel(marca, text="", image=icono("tv", 22, COLOR_ACCENT)
                     ).grid(row=0, column=0, rowspan=2, padx=(0, 11))
        ctk.CTkLabel(marca, text=APP_NAME, text_color=COLOR_TEXT, height=19,
                     anchor="w", font=ctk.CTkFont(size=15, weight="bold")
                     ).grid(row=0, column=1, sticky="sw")
        ctk.CTkLabel(marca, text=f"{APP_VENDOR}   ·   v{APP_VERSION}", height=15,
                     anchor="w", text_color=COLOR_FAINT, font=ctk.CTkFont(size=10)
                     ).grid(row=1, column=1, sticky="nw")

        derecha = ctk.CTkFrame(header, fg_color="transparent")
        derecha.grid(row=0, column=2, sticky="e", padx=16)

        chip = ctk.CTkFrame(derecha, fg_color=COLOR_BISEL,
                            corner_radius=RADIO_BOTON,
                            border_width=1, border_color=COLOR_BORDER)
        chip.pack(side="left", padx=(0, 8))
        self.status_dot = ctk.CTkLabel(chip, text="●", text_color=COLOR_FAIL,
                                       font=ctk.CTkFont(size=13), width=14)
        self.status_dot.pack(side="left", padx=(11, 0))
        self.device_menu = ctk.CTkOptionMenu(
            chip, values=["Sin dispositivos"], width=250, height=32,
            command=self.on_device_selected, font=self._fuente("cuerpo"),
            corner_radius=RADIO_BOTON, fg_color=COLOR_BISEL,
            button_color=COLOR_BISEL, button_hover_color=COLOR_BISEL_HOVER,
            text_color=COLOR_TEXT, dropdown_fg_color=COLOR_CHROME,
            dropdown_hover_color=COLOR_RAISED, dropdown_text_color=COLOR_TEXT,
            dropdown_font=self._fuente("cuerpo"))
        self.device_menu.pack(side="left")

        self.btn_refresh = self._boton_icono(
            derecha, "refrescar", self.refresh_devices, "Buscar dispositivos")
        self.btn_refresh.pack(side="left", padx=4)
        self.btn_config = self._boton_icono(
            derecha, "engranaje", lambda: self.show_page("Ajustes"), "Ajustes")
        self.btn_config.pack(side="left", padx=(4, 0))

        self._separador(header, row=1, column=0, columnspan=3, sticky="ew")
    def _build_body(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=0, sticky="nsew", padx=14, pady=(12, 6))
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkScrollableFrame(
            main, fg_color=COLOR_CHROME, corner_radius=RADIO_TARJETA, width=206,
            border_width=1, border_color=COLOR_BORDER,
            scrollbar_button_color=COLOR_CHROME,
            scrollbar_button_hover_color=COLOR_RAISED)
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 12))

        self.content = ctk.CTkFrame(main, fg_color=COLOR_CARD,
                                    corner_radius=RADIO_TARJETA,
                                    border_width=1, border_color=COLOR_BORDER)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        A, AM, RD, GR, MU = "accent", "amber", "red", "green", "muted"
        grupos = [
            ("Dispositivo", [
                ("panel", "Información", "info"),
                ("camara", "Capturas", [
                    ("Captura de pantalla", self.action_screenshot, A),
                    ("Grabar pantalla", self.toggle_record, "record"),
                    ("Espejar en tiempo real (scrcpy)", self.action_scrcpy, GR),
                    ("Abrir carpeta de capturas", self.action_open_shots, MU),
                ]),
                ("carpeta", "Archivos", "files"),
                ("mando", "Control remoto", "remote"),
            ]),
            ("Software", [
                ("paquete", "Aplicaciones", [
                    ("Desinstalar app (APK)", self.action_uninstall, RD),
                    ("Instalar APK", self.action_install, GR),
                    ("Extraer APK instalado", self.action_extract_apk, A),
                    ("Abrir app", self.action_open_app, A),
                    ("Permisos de una app", self.action_permissions, A),
                    ("Listar apps y versiones", self.action_list_packages, A),
                    ("Listar TODAS (incluye sistema)",
                     self.action_list_system_packages, MU),
                    ("Forzar detención", self.action_force_stop, AM),
                    ("Borrar datos de app", self.action_clear_data, RD),
                ]),
                ("documento", "Registros", [
                    ("Log completo del dispositivo", self.action_log_full, A),
                    ("Log de una app…", self.action_log_app, A),
                    ("Sólo errores y cuelgues", self.action_log_errors, AM),
                    ("Registros del fabricante…", self.action_log_vendor, GR),
                    ("Bugreport completo (zip)", self.action_bugreport, GR),
                    ("Limpiar el registro del equipo", self.action_log_clear, RD),
                    ("Abrir carpeta de registros", self.action_open_logs, MU),
                ]),
                ("ajustes", "Desarrollador", [
                    ("Límites de diseño ⇄", self.action_layout_bounds, AM),
                    ("Overdraw GPU ⇄", self.action_overdraw, AM),
                    ("Mostrar toques ⇄", self.action_show_touches, AM),
                    ("Ubicación del puntero ⇄", self.action_pointer, AM),
                    ("Animaciones ⇄", self.action_animations, AM),
                    ("No mantener actividades ⇄",
                     self.action_dont_keep_activities, AM),
                    ("Permanecer activo al cargar ⇄", self.action_stay_awake, AM),
                    ("Perfil de renderizado GPU ⇄", self.action_gpu_profile, AM),
                ]),
            ]),
            ("Sistema", [
                ("energia", "Energía", [
                    ("Reiniciar", self.action_reboot, AM),
                    ("Reiniciar a Recovery",
                     lambda: self.action_reboot("recovery"), AM),
                    ("Reiniciar a Bootloader",
                     lambda: self.action_reboot("bootloader"), AM),
                    ("Apagar", self.action_poweroff, RD),
                    ("Pantalla ON", lambda: self.action_screen_power(True), A),
                    ("Pantalla OFF", lambda: self.action_screen_power(False), A),
                ]),
                ("wifi", "Red / WiFi", [
                    ("Habilitar ADB por WiFi (5555)", self.action_wifi_enable, A),
                    ("Conectar por IP...", self.action_wifi_connect, A),
                    ("Buscar dispositivos en la red...", self.action_wifi_scan, A),
                    ("Emparejar por WiFi (Android 11+)...", self.action_wifi_pair, GR),
                ]),
                ("tv", "TV Box", "tvbox"),
            ]),
        ]

        self.pages = {}
        self.nav_buttons = {}
        self.nav_iconos = {}
        self.sidebar.grid_columnconfigure(0, weight=1)
        fila = 0
        for grupo, secciones in grupos:
            ctk.CTkLabel(self.sidebar, text=grupo.upper(), anchor="w", height=16,
                         text_color=COLOR_FAINT, font=self._fuente("menudo")
                         ).grid(row=fila, column=0, sticky="ew", padx=(14, 8),
                                pady=(13 if fila else 9, 3))
            fila += 1
            for icon, name, buttons in secciones:
                nav = ctk.CTkButton(
                    self.sidebar, text="  " + name, anchor="w", height=32,
                    image=icono(icon, 16, COLOR_MUTED), compound="left",
                    font=self._fuente("cuerpo"), corner_radius=7,
                    fg_color="transparent", hover_color=COLOR_RAISED,
                    text_color=COLOR_TEXT,
                    command=lambda n=name: self.show_page(n))
                nav.grid(row=fila, column=0, sticky="ew", padx=7, pady=1)
                self.nav_buttons[name] = nav
                self.nav_iconos[name] = icon
                fila += 1
                if buttons == "files":
                    self.pages[name] = self._build_files_page(icon, name)
                elif buttons == "info":
                    self.pages[name] = self._build_info_page(icon, name)
                elif buttons == "remote":
                    self.pages[name] = self._build_remote_page(icon, name)
                elif buttons == "tvbox":
                    self.pages[name] = self._build_tvbox_page(icon, name)
                else:
                    self.pages[name] = self._build_page(icon, name, buttons)

        self.pages["Ajustes"] = self._build_ajustes_page()
        self.show_page(grupos[0][1][0][1])

    def _build_page(self, icon, name, buttons):
        marco = ctk.CTkFrame(self.content, fg_color="transparent")
        marco.grid(row=0, column=0, sticky="nsew", padx=22, pady=16)
        marco.grid_columnconfigure(0, weight=1)
        marco.grid_rowconfigure(0, weight=1)
        page = self._scroll_autohide(
            ctk.CTkScrollableFrame(marco, fg_color="transparent"))
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure((0, 1), weight=1)

        self._cabecera_pagina(page, icon, name).grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        destacados = [b for b in buttons if b[2] in ("green", "primary")][:1]
        filas = [b for b in buttons if b not in destacados]

        for texto, orden, clave in destacados:
            self._styled_button(page, texto, orden, clave, height=42).grid(
                row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        if filas:
            self._lista_agrupada(page, filas).grid(
                row=2, column=0, columnspan=2, sticky="ew")
        return marco

    def _lista_agrupada(self, parent, filas):
        tarjeta = ctk.CTkFrame(parent, fg_color=COLOR_BG,
                               corner_radius=RADIO_TARJETA,
                               border_width=1, border_color=COLOR_BORDER_SOFT)
        tarjeta.grid_columnconfigure(0, weight=1)
        ultima = len(filas) - 1
        for i, (texto, orden, clave) in enumerate(filas):
            _, _, color_texto, _ = BUTTON_COLORS[clave]
            if clave in ("green", "primary"):
                color_texto = COLOR_TEXT
            fila = ctk.CTkButton(
                tarjeta, text=texto, command=orden, anchor="w", height=36,
                font=self._fuente("cuerpo"), corner_radius=7, border_width=0,
                fg_color="transparent", hover_color=COLOR_RAISED,
                text_color=color_texto)
            fila.grid(row=i * 2, column=0, sticky="ew", padx=5,
                      pady=(5 if i == 0 else 0, 5 if i == ultima else 0))
            if clave == "record":
                self.record_btn = fila
            if i != ultima:
                tarjeta.grid_rowconfigure(i * 2 + 1, minsize=1)
                self._separador(tarjeta, color=COLOR_BORDER, row=i * 2 + 1,
                                column=0, sticky="ew", padx=14)
        return tarjeta

    @staticmethod
    def _scroll_autohide(marco):
        def _ajustar(event=None):
            try:
                lienzo = marco._parent_canvas
                caja = lienzo.bbox("all")
                if caja and (caja[3] - caja[1]) > lienzo.winfo_height() + 2:
                    marco._scrollbar.grid()
                else:
                    marco._scrollbar.grid_remove()
            except Exception:
                pass
        marco.bind("<Configure>", _ajustar, add="+")
        marco._parent_canvas.bind("<Configure>", _ajustar, add="+")
        marco.after(300, _ajustar)
        return marco

    def _aplicar_tema(self):
        _elegir_fuentes(self)
        t = ctk.ThemeManager.theme
        par = lambda c: [c, c]
        t["CTkFont"].update({"family": FUENTE, "size": TIPO["cuerpo"][0]})
        t["CTk"].update({"fg_color": par(COLOR_BG)})
        t["CTkToplevel"].update({"fg_color": par(COLOR_BG)})
        t["CTkFrame"].update({
            "fg_color": par(COLOR_CARD), "top_fg_color": par(COLOR_BG),
            "border_color": par(COLOR_BORDER), "corner_radius": RADIO_TARJETA})
        t["CTkLabel"].update({"text_color": par(COLOR_TEXT)})
        t["CTkButton"].update({
            "fg_color": par(COLOR_BISEL), "hover_color": par(COLOR_BISEL_HOVER),
            "border_color": par(COLOR_BORDER), "text_color": par(COLOR_TEXT),
            "text_color_disabled": par(COLOR_FAINT),
            "corner_radius": RADIO_BOTON})
        t["CTkEntry"].update({
            "fg_color": par(COLOR_CARD), "border_color": par(COLOR_BORDER),
            "text_color": par(COLOR_TEXT), "placeholder_text_color": par(COLOR_FAINT),
            "corner_radius": RADIO_BOTON, "border_width": 1})
        t["CTkOptionMenu"].update({
            "fg_color": par(COLOR_BISEL), "button_color": par(COLOR_ACCENT),
            "button_hover_color": par(COLOR_ACCENT_HOVER),
            "text_color": par(COLOR_TEXT), "corner_radius": RADIO_BOTON})
        t["DropdownMenu"].update({
            "fg_color": par(COLOR_CHROME), "hover_color": par(COLOR_ACCENT_SOFT),
            "text_color": par(COLOR_TEXT)})
        t["CTkCheckBox"].update({
            "fg_color": par(COLOR_ACCENT), "border_color": par(COLOR_BORDER),
            "hover_color": par(COLOR_ACCENT_HOVER), "text_color": par(COLOR_TEXT),
            "checkmark_color": par("#ffffff"), "corner_radius": 5})
        t["CTkSwitch"].update({
            "fg_color": par(COLOR_BISEL), "progress_color": par(COLOR_ACCENT),
            "button_color": par("#ffffff"), "button_hover_color": par("#ffffff"),
            "text_color": par(COLOR_TEXT)})
        t["CTkTextbox"].update({
            "fg_color": par(COLOR_CARD), "border_color": par(COLOR_BORDER),
            "text_color": par(COLOR_TEXT),
            "scrollbar_button_color": par(COLOR_RAISED),
            "scrollbar_button_hover_color": par(COLOR_BORDER)})
        t["CTkProgressBar"].update({
            "fg_color": par(COLOR_BISEL), "progress_color": par(COLOR_ACCENT),
            "border_color": par(COLOR_BORDER)})
        t["CTkScrollbar"].update({
            "fg_color": "transparent", "button_color": par(COLOR_BISEL_HOVER),
            "button_hover_color": par(COLOR_FAINT)})
    def _fuente(self, estilo):
        if estilo not in self._fuentes:
            tam, peso = TIPO[estilo]
            self._fuentes[estilo] = ctk.CTkFont(size=tam, weight=peso)
        return self._fuentes[estilo]

    def _cabecera_pagina(self, parent, ico, titulo, subtitulo=None):
        marco = ctk.CTkFrame(parent, fg_color="transparent")
        marco.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(marco, text="", image=icono(ico, 21, COLOR_ACCENT)
                     ).grid(row=0, column=0, rowspan=2 if subtitulo else 1,
                            padx=(0, 12), pady=(3, 0) if subtitulo else 0,
                            sticky="nw" if subtitulo else "w")
        ctk.CTkLabel(marco, text=titulo, font=self._fuente("titulo"),
                     text_color=COLOR_TEXT, anchor="w"
                     ).grid(row=0, column=1, sticky="w")
        if subtitulo:
            ctk.CTkLabel(marco, text=subtitulo, font=self._fuente("menudo"),
                         text_color=COLOR_MUTED, anchor="w", justify="left",
                         wraplength=600).grid(row=1, column=1, sticky="w",
                                              pady=(2, 0))
        return marco

    def _styled_button(self, parent, text, command, key, height=44, ico=None):
        fondo, hover, color_texto, borde = BUTTON_COLORS[key]
        return ctk.CTkButton(
            parent, text=text, command=command, height=height,
            font=self._fuente("cuerpo"), corner_radius=RADIO_BOTON,
            fg_color=fondo, hover_color=hover, text_color=color_texto,
            border_width=1 if borde else 0, border_color=borde,
            image=icono(ico, 16, color_texto) if ico else None, compound="left")

    def show_page(self, name):
        for n, page in self.pages.items():
            activa = n == name
            if activa:
                page.grid()
            else:
                page.grid_remove()
            boton = self.nav_buttons.get(n)
            if boton is None:
                continue
            boton.configure(
                fg_color=COLOR_ACCENT if activa else "transparent",
                hover_color=COLOR_ACCENT_HOVER if activa else COLOR_RAISED,
                text_color="#ffffff" if activa else COLOR_TEXT,
                image=icono(self.nav_iconos[n], 16,
                            "#ffffff" if activa else COLOR_MUTED))
        self.btn_config.configure(
            fg_color=COLOR_ACCENT_SOFT if name == "Ajustes" else COLOR_BISEL,
            image=icono("engranaje", 17,
                        COLOR_ACCENT if name == "Ajustes" else COLOR_MUTED))
        if name == "Archivos" and self.selected_serial and not self.tree.get_children():
            self._files_refresh()
        if (name == "Información" and self.selected_serial
                and self.info_labels["Modelo"].get() == "—"):
            self.action_info_refresh()

    def _build_files_page(self, icon, name):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew", padx=18, pady=14)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        self._cabecera_pagina(page, icon, "Archivos del dispositivo").grid(
            row=0, column=0, sticky="ew", pady=(0, 10))

        bar = ctk.CTkFrame(page, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        bar.grid_columnconfigure(1, weight=1)

        self._styled_button(bar, "Subir", self._files_up, "accent", height=34
                            ).grid(row=0, column=0, padx=(0, 8))

        self.path_var = tk.StringVar(value=self.current_path)
        path_entry = ctk.CTkEntry(bar, textvariable=self.path_var, height=34,
                                  font=ctk.CTkFont(family=FUENTE_MONO, size=12))
        path_entry.grid(row=0, column=1, sticky="ew")
        path_entry.bind("<Return>", lambda e: self._files_goto(self.path_var.get()))

        boton_ir = self._styled_button(
            bar, "Ir", lambda: self._files_goto(self.path_var.get()),
            "accent", height=34)
        boton_ir.configure(width=54)
        boton_ir.grid(row=0, column=2, padx=8)
        self._boton_icono(bar, "refrescar", self._files_refresh,
                          "Volver a leer la carpeta").grid(row=0, column=3)

        tree_wrap = ctk.CTkFrame(page, fg_color=COLOR_BG, corner_radius=RADIO_BOTON)
        tree_wrap.grid(row=2, column=0, sticky="nsew")
        tree_wrap.grid_columnconfigure(0, weight=1)
        tree_wrap.grid_rowconfigure(0, weight=1)

        self._estilo_tabla()

        self.tree = ttk.Treeview(tree_wrap, style="Device.Treeview",
                                 columns=("tipo",), show="tree headings",
                                 selectmode="browse", height=5)
        self.tree.heading("#0", text="Nombre", anchor="w")
        self.tree.heading("tipo", text="Tipo", anchor="w")
        self.tree.column("#0", width=430, anchor="w")
        self.tree.column("tipo", width=110, anchor="w", stretch=False)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.tree.bind("<Double-1>", self._files_on_double)

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview,
                            style="Aqua.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns", pady=6)

        actions = ctk.CTkFrame(page, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self._styled_button(actions, "Traer al PC", self._files_pull, "primary",
                            height=40).pack(side="left", padx=(0, 8))
        self._styled_button(actions, "Enviar archivo aquí", self._files_push,
                            "accent", height=40).pack(side="left", padx=(0, 8))
        self._styled_button(actions, "Editar XML", self._files_editar_xml,
                            "accent", height=40).pack(side="left", padx=(0, 8))
        self._styled_button(actions, "Eliminar", self._files_delete, "red",
                            height=40, ico="papelera").pack(side="left")
        return page

    def _iconos_arbol(self):
        if getattr(self, "_arbol_img", None):
            return self._arbol_img
        from PIL import Image, ImageDraw, ImageTk
        imgs = {}
        for clave, nombre, color in (("dir", "carpeta", COLOR_ACCENT),
                                     ("file", "documento", COLOR_MUTED)):
            mascara = Image.new("L", (_LIENZO, _LIENZO), 0)
            ICONOS[nombre](ImageDraw.Draw(mascara))
            mascara = mascara.resize((15, 15), Image.LANCZOS)
            capa = Image.new("RGBA", (15, 15), color)
            capa.putalpha(mascara)
            imgs[clave] = ImageTk.PhotoImage(capa)
        self._arbol_img = imgs
        return imgs

    def _shq(self, path):
        return "'" + path.replace("'", "'\\''") + "'"

    def _ls(self, path):
        code, out, err = self.run_adb(
            ["shell", f"ls -Ap {self._shq(path)}"], timeout=25)
        entries = []
        for raw in out.splitlines():
            name = raw.rstrip("\r")
            if not name:
                continue
            is_dir = name.endswith("/")
            if is_dir:
                name = name[:-1]
            entries.append((name, is_dir))
        entries.sort(key=lambda x: (not x[1], x[0].lower()))
        return entries, err

    def _files_refresh(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        path = self.current_path
        if not path.endswith("/"):
            path += "/"
        self.current_path = path
        self.path_var.set(path)
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.tree.insert("", "end", iid=FILA_CARGANDO, text="  Cargando…",
                         values=("",))
        self._files_carga += 1
        self.threaded(lambda ficha=self._files_carga: self._files_load(path, ficha))

    def _files_load(self, path, ficha):
        entries, err = self._ls(path)

        def _fill():
            if ficha != self._files_carga:
                return
            for iid in self.tree.get_children():
                self.tree.delete(iid)
            imgs = self._iconos_arbol()
            if path.strip("/"):
                self.tree.insert("", "end", iid="..", text="  ..",
                                 image=imgs["dir"], values=("(subir)",))
            for nombre, is_dir in entries:
                iid = ("D:" if is_dir else "F:") + nombre
                self.tree.insert("", "end", iid=iid, text="  " + nombre,
                                 image=imgs["dir" if is_dir else "file"],
                                 values=(self._tipo_archivo(nombre, is_dir),))
            if err and err.strip():
                self.log("⚠ " + err.strip().splitlines()[0])
        self.after(0, _fill)

    @staticmethod
    def _tipo_archivo(nombre, es_dir):
        if es_dir:
            return "Carpeta"
        return "XML" if nombre.lower().endswith(".xml") else "Archivo"

    def _files_up(self):
        parent = posixpath.dirname(self.current_path.rstrip("/"))
        if not parent:
            parent = "/"
        self.current_path = parent if parent.endswith("/") else parent + "/"
        self._files_refresh()

    def _files_goto(self, path):
        path = path.strip()
        if not path:
            return
        self.current_path = path if path.endswith("/") else path + "/"
        self._files_refresh()

    def _files_on_double(self, event):
        iid = self.tree.identify_row(event.y) if event else self.tree.focus()
        if not iid or iid == FILA_CARGANDO:
            return
        if iid == "..":
            self._files_up()
        elif iid.startswith("D:"):
            name = iid[2:]
            self.current_path = self.current_path + name + "/"
            self._files_refresh()
        elif iid.lower().endswith(".xml"):
            self._abrir_editor_xml(self.current_path + iid[2:], iid[2:])

    def _files_editar_xml(self):
        nombre, es_dir = self._files_selected_name()
        if not nombre or es_dir:
            self.log("⚠ Selecciona en la lista el XML que quieras editar.")
            return
        if not nombre.lower().endswith(".xml"):
            self.log(f"⚠ «{nombre}» no es un XML; el editor sólo abre .xml.")
            return
        self._abrir_editor_xml(self.current_path + nombre, nombre)

    def _abrir_editor_xml(self, ruta, nombre):
        if not (self.ensure_adb() and self.ensure_device()):
            return

        def _w():
            self.log(f"Abriendo {ruta}…")
            code, datos, err = self.run_adb_binary(
                ["exec-out", "cat", ruta], timeout=60)
            fallo = (err or b"").decode("utf-8", "replace").strip()
            if code != 0 or fallo:
                self.log(f"✗ No se pudo leer {nombre}: "
                         f"{fallo or 'adb devolvió ' + str(code)}")
                return
            if len(datos) > XML_MAX:
                self.log(f"✗ {nombre} ocupa {len(datos) / 1024:.0f} KB y el editor "
                         f"llega a {XML_MAX // 1024} KB. Tráelo al PC.")
                return
            for codec in ("utf-8-sig", "utf-8", "latin-1"):
                try:
                    texto = datos.decode(codec)
                    break
                except UnicodeDecodeError:
                    continue
            crlf = "\r\n" in texto
            texto = texto.replace("\r\n", "\n")
            self.log(f"✓ {nombre}: {len(datos)} bytes, {codec}.")
            self.after(0, lambda: self._ventana_xml(ruta, nombre, texto,
                                                    codec, crlf))
        self.threaded(_w)

    @staticmethod
    def _xml_valido(texto, codec):
        from xml.etree import ElementTree
        try:
            ElementTree.fromstring(texto.encode(codec, "replace"))
            return True, ""
        except ElementTree.ParseError as e:
            return False, f"XML mal formado — {e}"
        except Exception as e:
            return False, str(e)

    def _ventana_xml(self, ruta, nombre, original, codec, crlf=False):
        win = ctk.CTkToplevel(self)
        win.title(nombre)
        win.geometry("900x660")
        win.minsize(620, 420)
        win.configure(fg_color=COLOR_BG)
        win.transient(self)
        self._cromo_windows(win)
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(win, text=nombre, font=self._fuente("titulo"), height=24,
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w",
                                                 padx=18, pady=(16, 0))
        ctk.CTkLabel(win, height=18, anchor="w", font=self._fuente("menudo"),
                     text_color=COLOR_MUTED,
                     text=f"{ruta}      ·      {len(original)} caracteres"
                          f"      ·      {codec}"
                     ).grid(row=1, column=0, sticky="w", padx=18, pady=(2, 10))

        caja = ctk.CTkTextbox(
            win, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER,
            corner_radius=RADIO_TARJETA, wrap="none", undo=True,
            font=ctk.CTkFont(family=FUENTE_MONO, size=TIPO["mono"][0]))
        caja.grid(row=2, column=0, sticky="nsew", padx=18)
        caja.insert("1.0", original)

        pie = ctk.CTkFrame(win, fg_color="transparent")
        pie.grid(row=3, column=0, sticky="ew", padx=20, pady=(8, 0))
        pie.grid_columnconfigure(0, weight=1)
        aviso = ctk.CTkLabel(pie, text="", anchor="w", height=18,
                             font=self._fuente("menudo"), text_color=COLOR_MUTED)
        aviso.grid(row=0, column=0, sticky="ew")

        ajustar = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            pie, text="Ajustar al ancho", variable=ajustar, checkbox_width=17,
            checkbox_height=17, font=self._fuente("menudo"),
            command=lambda: caja.configure(wrap="word" if ajustar.get() else "none")
        ).grid(row=0, column=1, sticky="e", padx=(12, 0))

        estado = {"original": original}

        def comprobar():
            ok, problema = self._xml_valido(caja.get("1.0", "end-1c"), codec)
            aviso.configure(text="✓ El XML está bien formado." if ok else "✗ " + problema,
                            text_color=COLOR_OK if ok else COLOR_FAIL)
            return ok

        def deshacer():
            caja.delete("1.0", "end")
            caja.insert("1.0", estado["original"])
            aviso.configure(text="Vuelto al contenido que hay en el equipo.",
                            text_color=COLOR_MUTED)

        def guardar():
            texto = caja.get("1.0", "end-1c")
            if texto == estado["original"]:
                aviso.configure(text="No has cambiado nada.", text_color=COLOR_MUTED)
                return
            if not comprobar() and not messagebox.askyesno(
                    "XML mal formado",
                    "El XML no está bien formado. Si lo guardas así, la app que "
                    "lo lee puede dejar de arrancar.\n\n¿Guardarlo de todas formas?",
                    parent=win):
                return
            if not messagebox.askyesno(
                    "Guardar en el equipo",
                    f"Se va a sobrescribir en el dispositivo:\n\n{ruta}\n\n¿Seguir?",
                    parent=win):
                return
            datos = (texto.replace("\n", "\r\n") if crlf else texto).encode(
                codec, "replace")

            def _w():
                carpeta = tempfile.mkdtemp(prefix="adbtoolbox_xml_")
                local = os.path.join(carpeta, nombre)
                with open(local, "wb") as f:
                    f.write(datos)
                code, salida = self.run_adb_transfer(["push", local, ruta],
                                                     f"Guardando {nombre}")
                shutil.rmtree(carpeta, ignore_errors=True)
                if code == 0:
                    estado["original"] = texto
                    self.log(f"✓ {nombre} guardado en el equipo ({len(datos)} bytes).")
                    self.after(0, lambda: aviso.configure(
                        text="✓ Guardado en el equipo.", text_color=COLOR_OK))
                else:
                    self.log(f"✗ No se pudo guardar {nombre}: "
                             f"{salida or 'sin detalle'}")
                    self.after(0, lambda: aviso.configure(
                        text="✗ No se pudo guardar; el motivo está en la consola.",
                        text_color=COLOR_FAIL))
            self.threaded(_w)

        barra = ctk.CTkFrame(win, fg_color="transparent")
        barra.grid(row=4, column=0, sticky="ew", padx=18, pady=14)
        barra.grid_columnconfigure(2, weight=1)
        self._styled_button(barra, "Comprobar XML", comprobar, "accent",
                            height=38).grid(row=0, column=0, padx=(0, 8))
        self._styled_button(barra, "Deshacer cambios", deshacer, "muted",
                            height=38).grid(row=0, column=1)
        self._styled_button(barra, "Guardar en el equipo", guardar, "primary",
                            height=38).grid(row=0, column=3)
        comprobar()
        caja.focus_set()
        return win

    def _files_selected_name(self):
        iid = self.tree.focus()
        if not iid or iid == ".." or iid == FILA_CARGANDO:
            return None, None
        return iid[2:], iid.startswith("D:")

    def _files_pull(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        name, is_dir = self._files_selected_name()
        if not name:
            self.log("⚠ Selecciona un archivo o carpeta en la lista.")
            return
        remote = self.current_path + name
        dest = filedialog.askdirectory(title="Carpeta destino en el PC")
        if not dest:
            return

        def _w():
            self.log(f"Trayendo {remote} → {dest}")
            code, salida = self.run_adb_transfer(["pull", remote, dest],
                                                 f"Trayendo {name}")
            self.log(("✓ " if code == 0 else "✗ ") + (salida or "sin detalle"))
        self.threaded(_w)

    def _files_push(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        path = filedialog.askopenfilename(title="Archivo a enviar al dispositivo")
        if not path:
            return
        remote = self.current_path + os.path.basename(path)

        def _w():
            nombre = os.path.basename(path)
            self.log(f"Enviando {nombre} → {remote}")
            code, salida = self.run_adb_transfer(["push", path, remote],
                                                 f"Enviando {nombre}")
            if code == 0:
                self.log("✓ " + (salida or "enviado."))
                self.after(200, self._files_refresh)
            else:
                self.log(f"✗ {salida or 'no se pudo enviar'}")
        self.threaded(_w)

    def _files_delete(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        name, is_dir = self._files_selected_name()
        if not name:
            self.log("⚠ Selecciona un archivo o carpeta para eliminar.")
            return
        remote = self.current_path + name
        if not messagebox.askyesno("Confirmar eliminación",
                                    f"¿Eliminar del dispositivo?\n\n{remote}"):
            return

        def _w():
            args = ["shell", f"rm -rf {self._shq(remote)}"]
            code, out, err = self.run_adb(args, timeout=60)
            if (out + err).strip():
                self.log(f"✗ {(out or err).strip()}")
            else:
                self.log(f"✓ Eliminado: {remote}")
                self.after(200, self._files_refresh)
        self.threaded(_w)

    def _build_tvbox_page(self, icon, name):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew", padx=18, pady=12)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        self._cabecera_pagina(
            page, icon, "TV Box",
            "Corrige la fecha (si el reloj se va a 2019 ningún certificado TLS "
            "valida y la sincronización falla) y fuerza la salida de video. "
            "Requiere root por adb."
        ).grid(row=0, column=0, rowspan=2, sticky="ew", pady=(0, 14))

        body = self._scroll_autohide(
            ctk.CTkScrollableFrame(page, fg_color="transparent"))
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure((0, 1), weight=1)

        card = ctk.CTkFrame(body, fg_color=COLOR_BG, corner_radius=RADIO_TARJETA,
                            border_width=1, border_color=COLOR_BORDER_SOFT)
        card.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 12))
        card.grid_columnconfigure((1, 3), weight=1)

        def etiqueta(texto, fila, col):
            ctk.CTkLabel(card, text=texto, text_color=COLOR_MUTED, anchor="w",
                         font=ctk.CTkFont(size=12)
                         ).grid(row=fila, column=col, sticky="w",
                                padx=(14, 8), pady=(12 if fila == 0 else 4, 4))

        etiqueta("Resolución", 0, 0)
        self.tv_mode_var = tk.StringVar(value=self.cfg.get("tvbox_mode", TVBOX_MODE))
        self.tv_mode_menu = ctk.CTkOptionMenu(
            card, values=list(TVBOX_MODES), variable=self.tv_mode_var, width=150,
            command=lambda _v: self._tv_update_resumen(),
            fg_color=COLOR_BISEL, button_color=COLOR_ACCENT,
            button_hover_color=COLOR_ACCENT_HOVER, dropdown_fg_color=COLOR_CHROME)
        self.tv_mode_menu.grid(row=0, column=1, sticky="w", pady=(12, 4))

        etiqueta("Densidad (dpi)", 0, 2)
        self.tv_dpi_var = tk.StringVar(
            value=str(self.cfg.get("tvbox_dpi", TVBOX_DENSITY)))
        ctk.CTkEntry(card, textvariable=self.tv_dpi_var, width=90
                     ).grid(row=0, column=3, sticky="w", padx=(0, 14), pady=(12, 4))

        etiqueta("App a reiniciar", 1, 0)
        self.tv_pkg_var = tk.StringVar(value=self.tvbox_pkg)
        ctk.CTkEntry(card, textvariable=self.tv_pkg_var
                     ).grid(row=1, column=1, sticky="ew", padx=(0, 14), pady=4)

        etiqueta("Servidor NTP", 1, 2)
        self.tv_ntp_var = tk.StringVar(value=self.cfg.get("tvbox_ntp", TVBOX_NTP))
        ctk.CTkEntry(card, textvariable=self.tv_ntp_var
                     ).grid(row=1, column=3, sticky="ew", padx=(0, 14), pady=4)

        self.tv_force_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            card, variable=self.tv_force_var, checkbox_width=18, checkbox_height=18,
            text="Aplicar el modo aunque la TV no lo reporte como compatible",
            font=ctk.CTkFont(size=12), text_color=COLOR_TEXT,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            border_color=COLOR_MUTED
        ).grid(row=2, column=0, columnspan=4, sticky="w", padx=14, pady=(8, 2))

        self.tv_resumen = ctk.CTkLabel(card, text="", anchor="w",
                                       text_color=COLOR_MUTED,
                                       font=ctk.CTkFont(size=11))
        self.tv_resumen.grid(row=3, column=0, columnspan=4, sticky="w",
                             padx=14, pady=(0, 12))
        self.tv_dpi_var.trace_add("write", lambda *a: self._tv_update_resumen())
        self._tv_update_resumen()

        self._styled_button(
            body, "Fix completo   ·   fecha + video + reinicio de la app",
            self.action_tv_full_fix, "green", height=48
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 8))

        botones = [
            ("Solo fecha y hora", self.action_tv_fix_clock, "accent"),
            ("Solo resolución", self.action_tv_video_profile, "accent"),
            ("Diagnóstico del equipo", self.action_tv_diagnose, "accent"),
            ("Reiniciar app de señalización", self.action_tv_restart_app, "amber"),
        ]
        for idx, (texto, comando, key) in enumerate(botones):
            self._styled_button(body, texto, comando, key, height=46).grid(
                row=2 + idx // 2, column=idx % 2, padx=4, pady=4, sticky="ew")
        return page

    @staticmethod
    def _tv_size(modo):
        return "1280x720" if (modo or "").lower().startswith(
            ("720", "576", "480")) else "1920x1080"

    def _tv_update_resumen(self):
        modo = self.tv_mode_var.get()
        dpi = self.tv_dpi_var.get().strip() or TVBOX_DENSITY
        self.tv_resumen.configure(
            text=f"Se aplicará:    HDMI {modo}    ·    wm size {self._tv_size(modo)}"
                 f"    ·    wm density {dpi}")

    def _tv_cfg(self):
        modo = self.tv_mode_var.get().strip() or TVBOX_MODE
        dpi = self.tv_dpi_var.get().strip()
        if not dpi.isdigit() or not (120 <= int(dpi) <= 640):
            self.log(f"⚠ Densidad «{dpi}» no válida; uso {TVBOX_DENSITY}.")
            dpi = TVBOX_DENSITY
            self.tv_dpi_var.set(dpi)
        pkg = self.tv_pkg_var.get().strip() or TVBOX_PKG
        ntp = self.tv_ntp_var.get().strip() or TVBOX_NTP
        self.tvbox_pkg = pkg
        self.cfg.update({"tvbox_mode": modo, "tvbox_dpi": dpi,
                         "tvbox_pkg": pkg, "tvbox_ntp": ntp})
        save_config(self.cfg)
        return {"modo": modo, "size": self._tv_size(modo), "dpi": dpi,
                "pkg": pkg, "ntp": ntp, "forzar": bool(self.tv_force_var.get())}

    def _estilo_tabla(self):
        estilo = ttk.Style()
        estilo.theme_use("default")
        estilo.configure("Device.Treeview", background=COLOR_CARD,
                         fieldbackground=COLOR_CARD, foreground=COLOR_TEXT,
                         rowheight=28, borderwidth=0, font=(FUENTE, 10))
        estilo.configure("Device.Treeview.Heading", background=COLOR_CHROME,
                         foreground=COLOR_MUTED, relief="flat",
                         font=(FUENTE, 9, "bold"), padding=(8, 6))
        estilo.map("Device.Treeview",
                   background=[("selected", COLOR_ACCENT)],
                   foreground=[("selected", "#ffffff")])
        estilo.map("Device.Treeview.Heading",
                   background=[("active", COLOR_RAISED)])
        estilo.layout("Aqua.Vertical.TScrollbar",
                      [("Vertical.Scrollbar.trough",
                        {"sticky": "ns", "children": [
                            ("Vertical.Scrollbar.thumb",
                             {"expand": "1", "sticky": "nswe"})]})])
        estilo.configure("Aqua.Vertical.TScrollbar", background=COLOR_BISEL_HOVER,
                         troughcolor=COLOR_CARD, bordercolor=COLOR_CARD,
                         relief="flat", width=10)
        estilo.map("Aqua.Vertical.TScrollbar",
                   background=[("active", COLOR_FAINT)])
        return estilo

    def ventana_tabla(self, titulo, columnas, filas, anchos=None):
        self._estilo_tabla()
        win = ctk.CTkToplevel(self)
        win.title(titulo)
        win.geometry("720x560")
        win.configure(fg_color=COLOR_BG)
        win.transient(self)
        self._cromo_windows(win)
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(win, text=titulo, font=self._fuente("titulo"),
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w",
                                                 padx=18, pady=(16, 8))
        buscador = tk.StringVar()
        campo = ctk.CTkEntry(win, textvariable=buscador, height=34,
                             placeholder_text="Filtrar…", font=self._fuente("cuerpo"))
        campo.grid(row=1, column=0, sticky="ew", padx=18)

        marco = ctk.CTkFrame(win, fg_color=COLOR_CARD, corner_radius=RADIO_TARJETA,
                             border_width=1, border_color=COLOR_BORDER)
        marco.grid(row=2, column=0, sticky="nsew", padx=18, pady=12)
        marco.grid_columnconfigure(0, weight=1)
        marco.grid_rowconfigure(0, weight=1)

        tabla = ttk.Treeview(marco, style="Device.Treeview", columns=columnas[1:],
                             show="tree headings", selectmode="browse")
        tabla.heading("#0", text=columnas[0], anchor="w")
        tabla.column("#0", width=(anchos or [320])[0], anchor="w")
        for i, col in enumerate(columnas[1:], start=1):
            tabla.heading(col, text=col, anchor="w")
            tabla.column(col, width=(anchos or [320, 140, 120])[i], anchor="w",
                         stretch=False)
        tabla.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview,
                              style="Aqua.Vertical.TScrollbar")
        tabla.configure(yscrollcommand=barra.set)
        barra.grid(row=0, column=1, sticky="ns", pady=6)

        estado = {"orden": 0, "inverso": False}

        def pintar(*_):
            filtro = buscador.get().lower()
            for iid in tabla.get_children():
                tabla.delete(iid)
            visibles = [f for f in filas
                        if not filtro or any(filtro in str(c).lower() for c in f)]
            col = estado["orden"]

            def clave(f):
                valor = f[col] if col < len(f) else ""
                return (int(valor) if str(valor).isdigit() else str(valor).lower())
            try:
                visibles.sort(key=clave, reverse=estado["inverso"])
            except TypeError:
                visibles.sort(key=lambda f: str(f[col]).lower(),
                              reverse=estado["inverso"])
            for i, f in enumerate(visibles):
                tabla.insert("", "end", iid=str(i), text="  " + str(f[0]),
                             values=tuple(f[1:]))
            pie.configure(text="%d de %d" % (len(visibles), len(filas)))

        def ordenar_por(i):
            estado["inverso"] = not estado["inverso"] if estado["orden"] == i else False
            estado["orden"] = i
            pintar()

        tabla.heading("#0", command=lambda: ordenar_por(0))
        for i, col in enumerate(columnas[1:], start=1):
            tabla.heading(col, command=lambda i=i: ordenar_por(i))
        buscador.trace_add("write", pintar)

        pie_marco = ctk.CTkFrame(win, fg_color="transparent")
        pie_marco.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 16))
        pie_marco.grid_columnconfigure(0, weight=1)
        pie = ctk.CTkLabel(pie_marco, text="", text_color=COLOR_MUTED,
                           font=self._fuente("menudo"), anchor="w")
        pie.grid(row=0, column=0, sticky="w")

        def copiar():
            self.clipboard_clear()
            self.clipboard_append("\n".join("\t".join(str(c) for c in f)
                                            for f in filas))
            pie.configure(text="Copiado al portapapeles (%d filas)" % len(filas))

        self._styled_button(pie_marco, "Copiar", copiar, "accent", height=34
                            ).grid(row=0, column=1, padx=6)
        self._styled_button(pie_marco, "Cerrar", win.destroy, "muted", height=34
                            ).grid(row=0, column=2)
        pintar()
        campo.focus_set()
        return win
    def _build_ajustes_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew", padx=18, pady=10)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)

        self._cabecera_pagina(
            page, "engranaje", "Ajustes",
            "Se guardan en %USERPROFILE%\\.adb_toolbox\\config.json"
        ).grid(row=0, column=0, sticky="ew", pady=(0, 9))

        cuerpo = self._scroll_autohide(
            ctk.CTkScrollableFrame(page, fg_color="transparent"))
        cuerpo.grid(row=1, column=0, sticky="nsew")
        cuerpo.grid_columnconfigure(0, weight=1)

        self.ajustes_valores = {}
        fila = self._tarjeta_ajustes(cuerpo, 0, "Herramientas", [
            ("adb", "adb", [("Cambiar…", self._ajuste_adb)]),
            ("scrcpy", "scrcpy", [("Buscar…", self._ajuste_scrcpy)]),
        ])
        fila = self._tarjeta_ajustes(cuerpo, fila, "Carpetas de salida", [
            ("Capturas y grabaciones", "capturas",
             [("Cambiar…", lambda: self._ajuste_carpeta("screenshot_dir")),
              ("Abrir", self.action_open_shots)]),
            ("Registros", "registros",
             [("Cambiar…", lambda: self._ajuste_carpeta("log_dir")),
              ("Abrir", self.action_open_logs)]),
        ])

        tarjeta = ctk.CTkFrame(cuerpo, fg_color=COLOR_BG, corner_radius=RADIO_TARJETA,
                               border_width=1, border_color=COLOR_BORDER_SOFT)
        tarjeta.grid(row=fila, column=0, sticky="ew", pady=(0, 7))
        tarjeta.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tarjeta, text="Señalización", font=self._fuente("seccion"),
                     height=18, text_color=COLOR_TEXT
                     ).grid(row=0, column=0, columnspan=3, sticky="w",
                            padx=16, pady=(7, 2))
        ctk.CTkLabel(tarjeta, text="Paquete por defecto", text_color=COLOR_MUTED,
                     font=self._fuente("dato"), anchor="w", height=20
                     ).grid(row=1, column=0, sticky="w", padx=(16, 14), pady=(0, 8))
        self.ajustes_pkg = tk.StringVar(value=self.tvbox_pkg)
        entrada = ctk.CTkEntry(tarjeta, textvariable=self.ajustes_pkg, height=30,
                               font=self._fuente("cuerpo"))
        entrada.grid(row=1, column=1, sticky="ew", pady=(0, 8))
        entrada.bind("<FocusOut>", lambda e: self._ajuste_pkg())
        entrada.bind("<Return>", lambda e: self._ajuste_pkg())
        self._styled_button(tarjeta, "Guardar", self._ajuste_pkg, "accent",
                            height=30).grid(row=1, column=2, padx=16, pady=(0, 8))
        fila += 1

        pie = ctk.CTkFrame(cuerpo, fg_color="transparent", height=22)
        pie.grid(row=fila, column=0, sticky="ew", pady=(2, 0))
        ctk.CTkLabel(pie, text="", image=icono("tv", 14, COLOR_FAINT)
                     ).pack(side="left", padx=(4, 8))
        ctk.CTkLabel(pie, height=18, text_color=COLOR_MUTED, anchor="w",
                     font=self._fuente("menudo"),
                     text=f"{APP_NAME}  v{APP_VERSION}   ·   "
                          f"Una herramienta de {APP_VENDOR}"
                     ).pack(side="left")
        fila += 1

        self._ajustes_refrescar()
        return page

    def _tarjeta_ajustes(self, parent, fila, titulo, entradas):
        tarjeta = ctk.CTkFrame(parent, fg_color=COLOR_BG, corner_radius=RADIO_TARJETA,
                               border_width=1, border_color=COLOR_BORDER_SOFT)
        tarjeta.grid(row=fila, column=0, sticky="ew", pady=(0, 7))
        tarjeta.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tarjeta, text=titulo, font=self._fuente("seccion"),
                     height=18, text_color=COLOR_TEXT
                     ).grid(row=0, column=0, columnspan=3, sticky="w",
                            padx=16, pady=(7, 2))
        for i, (etiqueta, clave, acciones) in enumerate(entradas):
            ultimo = i == len(entradas) - 1
            ctk.CTkLabel(tarjeta, text=etiqueta, text_color=COLOR_MUTED,
                         font=self._fuente("dato"), anchor="w", width=170,
                         height=20
                         ).grid(row=i + 1, column=0, sticky="w", padx=(16, 14),
                                pady=(0, 8 if ultimo else 5))
            valor = ctk.CTkLabel(
                tarjeta, text="—", text_color=COLOR_TEXT, anchor="w", width=290,
                height=20, font=ctk.CTkFont(family=FUENTE_MONO, size=12))
            valor.grid(row=i + 1, column=1, sticky="ew",
                       pady=(0, 8 if ultimo else 5))
            self.ajustes_valores[clave] = valor
            botones = ctk.CTkFrame(tarjeta, fg_color="transparent")
            botones.grid(row=i + 1, column=2, sticky="e", padx=16,
                         pady=(0, 8 if ultimo else 5))
            for texto, orden in acciones:
                self._styled_button(botones, texto, orden, "accent", height=30
                                    ).pack(side="left", padx=(6, 0))
        return fila + 1

    def _ajustes_refrescar(self):
        def corto(ruta, vacio):
            if not ruta:
                return vacio
            return ruta if len(ruta) <= 32 else "…" + ruta[-31:]
        for clave, ruta, vacio in (
                ("adb", self.adb_path, "no encontrado"),
                ("scrcpy", self.scrcpy_path, "sin configurar"),
                ("capturas", self.screenshot_dir, ""),
                ("registros", self.log_dir, "")):
            etiqueta = self.ajustes_valores.get(clave)
            if etiqueta is not None:
                etiqueta.configure(text=corto(ruta, vacio),
                                   text_color=COLOR_TEXT if ruta else COLOR_FAINT)

    def _ajuste_adb(self):
        self.prompt_configure_adb()
        self._ajustes_refrescar()

    def _ajuste_scrcpy(self):
        if self._locate_scrcpy():
            self.scrcpy_path = self.cfg.get("scrcpy_path")
        self._ajustes_refrescar()

    def _ajuste_carpeta(self, clave):
        actual = self.screenshot_dir if clave == "screenshot_dir" else self.log_dir
        destino = filedialog.askdirectory(title="Elige la carpeta", initialdir=actual)
        if not destino:
            return
        if clave == "screenshot_dir":
            self.screenshot_dir = destino
        else:
            self.log_dir = destino
        self.cfg[clave] = destino
        save_config(self.cfg)
        self.log(f"✓ Carpeta guardada: {destino}")
        self._ajustes_refrescar()

    def _ajuste_pkg(self):
        pkg = self.ajustes_pkg.get().strip()
        if not pkg or pkg == self.tvbox_pkg:
            return
        self.tvbox_pkg = pkg
        self.cfg["tvbox_pkg"] = pkg
        save_config(self.cfg)
        if hasattr(self, "tv_pkg_var"):
            self.tv_pkg_var.set(pkg)
        self.log(f"✓ Paquete de señalización: {pkg}")
    def _build_remote_page(self, icon, name):
        marco = ctk.CTkFrame(self.content, fg_color="transparent")
        marco.grid(row=0, column=0, sticky="nsew", padx=18, pady=10)
        marco.grid_columnconfigure(0, weight=1)
        marco.grid_rowconfigure(0, weight=1)
        page = self._scroll_autohide(
            ctk.CTkScrollableFrame(marco, fg_color="transparent"))
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(1, weight=1)

        self._cabecera_pagina(
            page, icon, "Control remoto",
            "Los botones mandan «input keyevent» al equipo; el campo de abajo "
            "escribe en él lo que teclees aquí."
        ).grid(row=0, column=0, columnspan=2, rowspan=2, sticky="ew", pady=(0, 10))

        dpad = ctk.CTkFrame(page, fg_color=COLOR_BG, corner_radius=RADIO_TARJETA,
                            border_width=1, border_color=COLOR_BORDER_SOFT)
        dpad.grid(row=2, column=0, sticky="n", padx=(0, 16))
        for texto, code, fila, col in [("▲", 19, 0, 1), ("◀", 21, 1, 0),
                                       ("OK", 23, 1, 1), ("▶", 22, 1, 2),
                                       ("▼", 20, 2, 1)]:
            centro = texto == "OK"
            ctk.CTkButton(
                dpad, text=texto, width=64, height=52,
                font=ctk.CTkFont(size=15, weight="bold"),
                fg_color=COLOR_ACCENT if centro else COLOR_BISEL,
                hover_color=COLOR_ACCENT_HOVER if centro else COLOR_BISEL_HOVER,
                border_width=0 if centro else 1, border_color=COLOR_BORDER,
                text_color="#ffffff" if centro else COLOR_TEXT,
                command=lambda k=code, t=texto: self.action_key(k, t)
            ).grid(row=fila, column=col, padx=6, pady=6)

        lado = ctk.CTkFrame(page, fg_color="transparent")
        lado.grid(row=2, column=1, sticky="new")
        lado.grid_columnconfigure((0, 1), weight=1)
        teclas = [
            ("Atrás", 4), ("Inicio", 3),
            ("Menú", 82), ("Recientes", 187),
            ("Volumen −", 25), ("Volumen +", 24),
            ("Silencio", 164), ("Play / Pausa", 85),
            ("Enter", 66), ("Encender / Apagar", 26),
        ]
        for idx, (texto, code) in enumerate(teclas):
            ctk.CTkButton(
                lado, text=texto, height=38, anchor="center",
                font=self._fuente("cuerpo"),
                fg_color=COLOR_BISEL, hover_color=COLOR_BISEL_HOVER,
                border_width=1, border_color=COLOR_BORDER, text_color=COLOR_TEXT,
                command=lambda k=code, t=texto: self.action_key(k, t)
            ).grid(row=idx // 2, column=idx % 2, padx=5, pady=4, sticky="ew")

        caja = ctk.CTkFrame(page, fg_color=COLOR_BG, corner_radius=RADIO_TARJETA,
                            border_width=1, border_color=COLOR_BORDER_SOFT)
        caja.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        caja.grid_columnconfigure(0, weight=1)

        self.remote_text = tk.StringVar()
        entrada = ctk.CTkEntry(
            caja, textvariable=self.remote_text, height=36,
            placeholder_text="Escribe aquí: contraseñas de WiFi, URLs largas...")
        entrada.grid(row=0, column=0, sticky="ew", padx=(12, 8), pady=9)
        entrada.bind("<Return>", lambda e: self.action_send_text())

        self._styled_button(caja, "Enviar texto", self.action_send_text,
                            "primary", height=36).grid(row=0, column=1, pady=9)
        ctk.CTkButton(caja, text="⌫", width=54, height=36,
                      font=ctk.CTkFont(family="Segoe UI Symbol", size=15),
                      command=lambda: self.action_key(67, "Borrar"),
                      corner_radius=RADIO_BOTON, fg_color=COLOR_BISEL,
                      hover_color=COLOR_BISEL_HOVER, text_color=COLOR_TEXT,
                      border_width=1, border_color=COLOR_BORDER
                      ).grid(row=0, column=2, padx=(8, 12), pady=9)

        self.remote_status = ctk.CTkLabel(page, text="", text_color=COLOR_MUTED,
                                          font=ctk.CTkFont(size=11), anchor="w")
        self.remote_status.grid(row=4, column=0, columnspan=2, sticky="w",
                                pady=(5, 0))
        return marco

    def action_key(self, keycode, nombre=""):
        if not (self.ensure_adb() and self.ensure_device()):
            return

        def _w():
            code, out, err = self.run_adb(
                ["shell", f"input keyevent {keycode}"], timeout=15)
            if code == 0 and not (out + err).strip():
                self.after(0, lambda: self.remote_status.configure(
                    text=f"Enviado:  {nombre.strip()}   (keyevent {keycode})"))
            else:
                self.log(f"✗ Tecla {keycode}: {(out or err).strip() or 'falló'}")
        self.threaded(_w)

    def action_send_text(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        texto = self.remote_text.get()
        if not texto:
            return

        def _w():
            if any(ord(c) > 127 for c in texto):
                self.log("⚠ 'input text' sólo maneja ASCII en la mayoría de ROMs: "
                         "las tildes y la ñ pueden salir mal.")
            code, out, err = self.run_adb(
                ["shell", f"input text {self._shq(texto)}"], timeout=25)
            if code == 0 and not (out + err).strip():
                self.after(0, lambda: self.remote_status.configure(
                    text=f"Texto enviado:  {len(texto)} caracteres"))
            else:
                self.log(f"✗ No se pudo enviar el texto: "
                         f"{(out or err).strip() or 'sin detalle'}")
        self.threaded(_w)

    def _build_info_page(self, icon, name):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew", padx=16, pady=10)
        page.grid_columnconfigure((0, 1), weight=1)

        cabecera = ctk.CTkFrame(page, fg_color="transparent")
        cabecera.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        cabecera.grid_columnconfigure(0, weight=1)
        self._cabecera_pagina(cabecera, icon, "Información").grid(
            row=0, column=0, sticky="w")
        self._boton_icono(cabecera, "copiar", self._info_copiar,
                          "Copiar toda la información").grid(
            row=0, column=1, sticky="e", padx=(0, 8))
        self._styled_button(cabecera, "Actualizar", self.action_info_refresh,
                            "primary", height=34, ico="refrescar").grid(
            row=0, column=2, sticky="e")

        cuerpo = self._scroll_autohide(
            ctk.CTkScrollableFrame(page, fg_color="transparent"))
        cuerpo.grid(row=1, column=0, columnspan=2, sticky="nsew")
        cuerpo.grid_columnconfigure((0, 1), weight=1)
        page.grid_rowconfigure(1, weight=1)

        self.info_labels = {}
        self.info_bars = {}
        self.info_tarjetas = []
        for titulo, fila, col, campos, barras in [
                ("Dispositivo", 1, 0, ["Modelo", "Fabricante", "Serie",
                                       "CID", "CPU"], False),
                ("Batería", 1, 1, ["Nivel", "Estado", "Salud", "Temperatura"],
                 False),
                ("Sistema", 2, 0, ["Android", "SDK", "Compilación",
                                   "Encendido hace"], False),
                ("Almacenamiento y memoria", 2, 1, ["/data", "RAM"], True),
                ("Pantalla", 3, 0, ["Resolución", "Densidad"], False),
                ("Red", 3, 1, ["WiFi", "Ethernet"], False)]:
            self._info_card(cuerpo, titulo, fila - 1, col, campos, barras)
            self.info_tarjetas.append((titulo, campos))
        return page

    def _info_card(self, parent, titulo, fila, col, campos, barras=False):
        card = ctk.CTkFrame(parent, fg_color=COLOR_BG, corner_radius=RADIO_TARJETA,
                            border_width=1, border_color=COLOR_BORDER_SOFT)
        card.grid(row=fila, column=col, sticky="new", pady=(0, 5),
                  padx=(0, 5) if col == 0 else (5, 0))
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(card, text=titulo, height=22,
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, sticky="w",
                            padx=14, pady=(6, 3))
        r = 1
        for i, campo in enumerate(campos):
            ultimo = i == len(campos) - 1
            margen = (0, 0 if barras or not ultimo else 8)
            ctk.CTkLabel(card, text=campo, text_color=COLOR_MUTED, anchor="w",
                         height=20, font=ctk.CTkFont(size=12)
                         ).grid(row=r, column=0, sticky="w",
                                padx=(14, 6), pady=margen)
            valor = self._dato_copiable(card)
            valor.grid(row=r, column=1, sticky="ew", padx=(0, 8), pady=margen)
            self.info_labels[campo] = valor
            r += 1
            if barras:
                barra = ctk.CTkProgressBar(card, height=8, corner_radius=4,
                                           fg_color=COLOR_CARD,
                                           progress_color=COLOR_GREEN)
                barra.set(0)
                barra.grid(row=r, column=0, columnspan=2, sticky="ew",
                           padx=14, pady=(2, 8 if ultimo else 5))
                self.info_bars[campo] = barra
                r += 1

    def _info_set(self, campo, valor):
        etiqueta = self.info_labels.get(campo)
        if etiqueta is None:
            return
        texto = str(valor).strip() if valor is not None else ""
        self.after(0, lambda: self._poner_dato(etiqueta, texto or "—"))

    def _info_copiar(self):
        if self.info_labels["Modelo"].get() in ("—", "…"):
            self.log("Todavía no hay información que copiar: pulsa «Actualizar».")
            return
        bloques = []
        for titulo, campos in self.info_tarjetas:
            bloques.append("\n".join(
                [titulo] + ["  %s: %s" % (c, self.info_labels[c].get())
                            for c in campos]))
        self.clipboard_clear()
        self.clipboard_append("\n\n".join(bloques))
        self.log("Información del dispositivo copiada al portapapeles.")

    def _info_bar(self, campo, fraccion):
        barra = self.info_bars.get(campo)
        if barra is None or fraccion is None:
            return
        valor = max(0.0, min(1.0, fraccion))
        color = (COLOR_RED if valor >= OCUPACION_CRITICA else
                 COLOR_AMBER if valor >= OCUPACION_AVISO else COLOR_GREEN)

        def _():
            barra.set(valor)
            barra.configure(progress_color=color)
        self.after(0, _)

    @staticmethod
    def _ultimo_valor(texto):
        valor = ""
        for linea in (texto or "").splitlines():
            if ":" in linea:
                valor = linea.split(":", 1)[1].strip()
        return valor

    def action_info_refresh(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        for campo in self.info_labels:
            self._info_set(campo, "…")
        for barra in self.info_bars.values():
            barra.set(0)
        self.threaded(self._info_worker)

    def _getprops_all(self):
        _, out, _ = self.run_adb(["exec-out", "getprop"], timeout=30)
        props = {}
        for linea in out.splitlines():
            m = re.match(r"\[([^\]]+)\]:\s*\[(.*)\]\s*$", linea.strip())
            if m:
                props[m.group(1)] = m.group(2).strip()
        return props

    @staticmethod
    def _primera_prop(props, claves, vacios=("", "unknown")):
        for clave in claves:
            valor = props.get(clave, "")
            if valor.lower() not in vacios:
                return valor
        return ""

    @staticmethod
    def _version_firmware(props):
        for clave in PROPS_FIRMWARE:
            valor = props.get(clave, "").strip()
            if not valor:
                continue
            m = re.search(r"\d+(?:\.\d+){1,3}", valor)
            if m:
                return m.group(0)
        return ""

    def _buscar_cid(self, props):
        cid = self._primera_prop(props, PROPS_CID)
        if cid:
            return cid
        for clave in sorted(props):
            if re.search(r"(^|[._])cid$", clave) and props[clave]:
                return f"{props[clave]}   ({clave})"
        return ""

    def _info_worker(self):
        props = self._getprops_all()

        self._info_set("Modelo", props.get("ro.product.model", ""))
        self._info_set("Fabricante", props.get("ro.product.manufacturer", ""))

        serie = self._primera_prop(props, PROPS_SERIE)
        if not serie:
            _, s, _ = self.run_adb(["get-serialno"], target_device=True, timeout=15)
            s = s.strip()
            serie = s if s and ":" not in s and s.lower() != "unknown" else ""
        self._info_set("Serie", serie or "no disponible")

        cid = self._buscar_cid(props)
        self._info_set("CID", cid or "no disponible")
        if not cid:
            self.log("· CID: este equipo no lo publica con un nombre conocido. "
                     "Búscalo con:  shell getprop | grep -i cid")
        self._info_set("CPU", props.get("ro.product.cpu.abi", ""))

        sdk = props.get("ro.build.version.sdk", "")
        real = SDK_A_ANDROID.get(sdk)
        self._info_set("Android", props.get("ro.build.version.release", ""))
        self._info_set("SDK", f"{sdk}   (Android {real})" if real else sdk)
        self._info_set("Compilación",
                       self._version_firmware(props)
                       or self._primera_prop(props, PROPS_COMPILACION))
        up = self._tv_cat("/proc/uptime")
        try:
            self._info_set("Encendido hace", self._fmt_dur(float(up.split()[0])))
        except (ValueError, IndexError):
            self._info_set("Encendido hace", "")

        _, bat, _ = self.run_adb(["exec-out", "dumpsys", "battery"], timeout=25)
        datos = {}
        for linea in bat.splitlines():
            if ":" in linea:
                clave, valor = linea.split(":", 1)
                datos[clave.strip()] = valor.strip()
        if datos.get("present") == "false":
            self._info_set("Nivel", "sin batería")
            for campo in ("Estado", "Salud", "Temperatura"):
                self._info_set(campo, "—")
        else:
            nivel = datos.get("level", "")
            self._info_set("Nivel", f"{nivel} %" if nivel else "")
            self._info_set("Estado", BATERIA_ESTADO.get(datos.get("status", ""),
                                                        datos.get("status", "")))
            self._info_set("Salud", BATERIA_SALUD.get(datos.get("health", ""),
                                                      datos.get("health", "")))
            temp = datos.get("temperature", "")
            self._info_set("Temperatura",
                           f"{int(temp) / 10:.1f} °C" if temp.isdigit() else "")

        _, df, _ = self.run_adb(
            ["exec-out", "sh", "-c", "df -h /data | tail -1"], timeout=25)
        partes = df.split()
        if len(partes) >= 5:
            self._info_set("/data", f"{partes[-3]} libres de {partes[-5]}"
                                    f"   ({partes[-2]} usado)")
            usado = partes[-2].rstrip("%")
            if usado.isdigit():
                self._info_bar("/data", int(usado) / 100.0)
        _, mem, _ = self.run_adb(["exec-out", "cat", "/proc/meminfo"], timeout=25)
        valores = {}
        for linea in mem.splitlines():
            if ":" in linea:
                clave, valor = linea.split(":", 1)
                valores[clave.strip()] = valor.strip()

        def gigas(texto):
            try:
                return int(texto.split()[0]) / 1048576.0
            except (ValueError, IndexError, AttributeError):
                return None

        total = gigas(valores.get("MemTotal", ""))
        libre = gigas(valores.get("MemAvailable", valores.get("MemFree", "")))
        if total and libre:
            self._info_set("RAM", f"{libre:.1f} GB libres de {total:.1f} GB")
            self._info_bar("RAM", 1 - libre / total)

        _, size, _ = self.run_adb(["exec-out", "wm", "size"], timeout=25)
        _, dens, _ = self.run_adb(["exec-out", "wm", "density"], timeout=25)
        self._info_set("Resolución", self._ultimo_valor(size))
        self._info_set("Densidad", self._ultimo_valor(dens))

        for campo, interfaz in (("WiFi", "wlan0"), ("Ethernet", "eth0")):
            _, out, _ = self.run_adb(
                ["exec-out", "ip", "-f", "inet", "addr", "show", interfaz],
                timeout=25)
            m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", out)
            self._info_set(campo, m.group(1) if m else "no conectado")

    def _build_log(self):
        wrap = ctk.CTkFrame(self, fg_color=COLOR_CHROME, corner_radius=0)
        wrap.grid(row=2, column=0, sticky="ew")
        wrap.grid_columnconfigure(0, weight=1)
        self._separador(wrap, row=0, column=0, sticky="ew")

        barra = ctk.CTkFrame(wrap, fg_color="transparent")
        barra.grid(row=1, column=0, sticky="ew", padx=(10, 12), pady=(6, 0))
        barra.grid_columnconfigure(1, weight=1)

        self.btn_consola = ctk.CTkButton(
            barra, text="  Consola", image=icono("chevron", 13, COLOR_MUTED),
            compound="left", anchor="w", width=100, height=28,
            font=self._fuente("cuerpo"), corner_radius=6, fg_color="transparent",
            hover_color=COLOR_RAISED, text_color=COLOR_TEXT,
            command=self.toggle_consola)
        self.btn_consola.grid(row=0, column=0, sticky="w")

        self.log_resumen = ctk.CTkLabel(barra, text="", text_color=COLOR_FAINT,
                                        font=self._fuente("menudo"), anchor="w")
        self.log_resumen.grid(row=0, column=1, sticky="ew", padx=12)

        acciones = ctk.CTkFrame(barra, fg_color="transparent")
        acciones.grid(row=0, column=2, sticky="e")
        self._boton_icono(acciones, "copiar", self.copiar_log,
                          "Copiar la consola", tam=28).pack(side="left", padx=3)
        self._boton_icono(acciones, "papelera", self.clear_log,
                          "Limpiar la consola", tam=28).pack(side="left", padx=3)

        self.consola_cuerpo = ctk.CTkFrame(wrap, fg_color="transparent")
        self.consola_cuerpo.grid(row=2, column=0, sticky="ew")
        self.consola_cuerpo.grid_columnconfigure(0, weight=1)

        self.log_box = ctk.CTkTextbox(
            self.consola_cuerpo, height=118, fg_color=COLOR_CARD,
            corner_radius=RADIO_BOTON, border_width=1,
            border_color=COLOR_BORDER, text_color=COLOR_TEXT,
            font=ctk.CTkFont(family=FUENTE_MONO, size=TIPO["mono"][0]))
        self.log_box.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 0))
        self.log_box.configure(state="disabled")

        self.progress_frame = ctk.CTkFrame(self.consola_cuerpo, fg_color="transparent")
        self.progress_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(8, 0))
        self.progress_frame.grid_columnconfigure(0, weight=1)
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, height=6, corner_radius=3,
            progress_color=COLOR_ACCENT, fg_color=COLOR_RAISED)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(2, 12))
        self.progress_label = ctk.CTkLabel(
            self.progress_frame, text="", text_color=COLOR_MUTED, anchor="e",
            font=self._fuente("menudo"), width=240)
        self.progress_label.grid(row=0, column=1, sticky="e")
        self.progress_frame.grid_remove()

        cmd_bar = ctk.CTkFrame(wrap, fg_color="transparent")
        cmd_bar.grid(row=3, column=0, sticky="ew", padx=12, pady=(8, 10))
        cmd_bar.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(cmd_bar, text="adb", text_color=COLOR_MUTED,
                     font=ctk.CTkFont(family=FUENTE_MONO, size=13, weight="bold")
                     ).grid(row=0, column=0, padx=(4, 10))
        self.cmd_var = tk.StringVar()
        self.cmd_entry = ctk.CTkEntry(
            cmd_bar, textvariable=self.cmd_var, height=34,
            corner_radius=RADIO_BOTON, fg_color=COLOR_CARD,
            border_color=COLOR_BORDER, text_color=COLOR_TEXT,
            font=ctk.CTkFont(family=FUENTE_MONO, size=TIPO["mono"][0]),
            placeholder_text="shell getprop ro.product.model      "
                             "— Enter ejecuta, ↑ ↓ recuperan lo anterior")
        self.cmd_entry.grid(row=0, column=1, sticky="ew")
        self.cmd_entry.bind("<Return>", lambda e: self.action_run_command())
        self.cmd_entry.bind("<Up>", lambda e: self._cmd_history(-1))
        self.cmd_entry.bind("<Down>", lambda e: self._cmd_history(1))
        self._styled_button(cmd_bar, "Ejecutar", self.action_run_command,
                            "accent", height=34).grid(row=0, column=2, padx=(8, 0))

        if not self.consola_abierta:
            self.consola_cuerpo.grid_remove()
            self.btn_consola.configure(image=icono("chevron_arriba", 13, COLOR_MUTED))

    def toggle_consola(self):
        self.consola_abierta = not self.consola_abierta
        if self.consola_abierta:
            self.consola_cuerpo.grid()
            self.log_resumen.configure(text="")
        else:
            self.consola_cuerpo.grid_remove()
        self.btn_consola.configure(image=icono(
            "chevron" if self.consola_abierta else "chevron_arriba", 13, COLOR_MUTED))
        self.cfg["consola_abierta"] = self.consola_abierta
        save_config(self.cfg)

    def copiar_log(self):
        texto = self.log_box.get("1.0", "end").strip()
        if not texto:
            return
        self.clipboard_clear()
        self.clipboard_append(texto)
        self.log_resumen.configure(text="Consola copiada al portapapeles.")

    def log(self, msg):
        stamp = datetime.datetime.now().strftime("%H:%M:%S")
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", f"[{stamp}] {msg}\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
            if not self.consola_abierta:
                self.log_resumen.configure(text=msg[:110])
        try:
            self.after(0, _append)
        except Exception:
            pass

    def clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def set_status(self, connected):
        self.status_dot.configure(text_color=COLOR_OK if connected else COLOR_FAIL)

    def ensure_adb(self):
        if not self.adb_path:
            self.log("⚠ ADB no configurado.")
            self.prompt_configure_adb()
            return False
        return True

    def ensure_device(self):
        if not self.selected_serial:
            self.log("⚠ No hay dispositivo seleccionado. Conecta uno y pulsa ⟳.")
            return False
        return True

    def _base_cmd(self, target_device=True):
        cmd = [self.adb_path]
        if target_device and self.selected_serial:
            cmd += ["-s", self.selected_serial]
        return cmd

    def run_adb(self, args, target_device=True, timeout=60, capture=True):
        cmd = self._base_cmd(target_device) + args
        try:
            proc = subprocess.run(
                cmd, capture_output=capture, timeout=timeout,
                creationflags=CREATE_NO_WINDOW)
            out = proc.stdout.decode("utf-8", "replace") if capture and proc.stdout else ""
            err = proc.stderr.decode("utf-8", "replace") if capture and proc.stderr else ""
            return proc.returncode, out, err
        except subprocess.TimeoutExpired:
            return -1, "", "Tiempo de espera agotado."
        except Exception as e:
            return -1, "", str(e)

    def run_adb_binary(self, args, timeout=60):
        cmd = self._base_cmd(True) + args
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout,
                              creationflags=CREATE_NO_WINDOW)
        return proc.returncode, proc.stdout, proc.stderr

    def _progress_show(self, texto):
        def _():
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self.progress_label.configure(text=texto)
            self.progress_frame.grid()
        self.after(0, _)

    def _progress_determinado(self):
        def _():
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(0)
        self.after(0, _)

    def _progress_set(self, fraccion, texto=None):
        def _():
            self.progress_bar.set(max(0.0, min(1.0, fraccion)))
            if texto:
                self.progress_label.configure(text=texto)
        self.after(0, _)

    def _progress_hide(self):
        def _():
            self.progress_bar.stop()
            self.progress_frame.grid_remove()
        self.after(0, _)

    def run_adb_transfer(self, args, etiqueta, timeout=1800):
        cmd = self._base_cmd(True) + args
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, bufsize=0,
                                    creationflags=CREATE_NO_WINDOW)
        except Exception as e:
            return -1, str(e)

        corte = threading.Timer(timeout, proc.kill)
        corte.start()
        self._progress_show(etiqueta)
        patron = re.compile(rb"\[\s*(\d+)%\]")
        lineas, buf, determinado = [], b"", False
        try:
            while True:
                trozo = proc.stdout.read(1)
                if not trozo:
                    break
                if trozo in (b"\r", b"\n"):
                    if buf:
                        m = patron.search(buf)
                        if m:
                            if not determinado:
                                self._progress_determinado()
                                determinado = True
                            pct = int(m.group(1))
                            self._progress_set(pct / 100.0, f"{etiqueta}   {pct} %")
                        else:
                            lineas.append(buf.decode("utf-8", "replace").strip())
                    buf = b""
                else:
                    buf += trozo
            if buf:
                lineas.append(buf.decode("utf-8", "replace").strip())
            codigo = proc.wait()
        finally:
            corte.cancel()
            self._progress_hide()
        return codigo, "\n".join(l for l in lineas if l)

    def threaded(self, fn):
        t = threading.Thread(target=self._safe_run, args=(fn,), daemon=True)
        t.start()

    def _safe_run(self, fn):
        try:
            fn()
        except Exception as e:
            self.log(f"✗ Error: {e}")

    def refresh_devices(self):
        if not self.ensure_adb():
            return
        self.log("Buscando dispositivos...")
        self.threaded(self._refresh_devices_worker)

    def _refresh_devices_worker(self):
        code, out, err = self.run_adb(["devices", "-l"], target_device=False, timeout=15)
        self.device_map = {}
        labels = []
        for line in out.splitlines()[1:]:
            line = line.strip()
            if not line or "\t" not in line and " " not in line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            serial, state = parts[0], parts[1]
            model = ""
            m = re.search(r"model:(\S+)", line)
            if m:
                model = m.group(1).replace("_", " ")
            if state == "device":
                label = f"{model or 'Dispositivo'}  ({serial})"
            else:
                label = f"[{state}] {serial}"
            self.device_map[label] = serial if state == "device" else None
            labels.append(label)

        def _update():
            if labels:
                self.device_menu.configure(values=labels)
                sigue = next((l for l in labels
                              if self.selected_serial
                              and self.device_map.get(l) == self.selected_serial),
                             None)
                elegido = sigue or labels[0]
                self.device_menu.set(elegido)
                self.on_device_selected(elegido)
                self.log(f"✓ {len(labels)} dispositivo(s) detectado(s).")
            else:
                self.device_menu.configure(values=["Sin dispositivos"])
                self.device_menu.set("Sin dispositivos")
                self.selected_serial = None
                self.set_status(False)
                self.log("No se detectaron dispositivos. ¿Depuración USB activada?")
        self.after(0, _update)

    def on_device_selected(self, label):
        serial = self.device_map.get(label)
        self.selected_serial = serial
        self.set_status(bool(serial))
        if serial:
            self.log(f"Dispositivo activo: {label}")

    def prompt_configure_adb(self):
        messagebox.showinfo(
            "Configurar ADB",
            "Selecciona el archivo adb.exe (normalmente en la carpeta "
            "'platform-tools' del SDK de Android).")
        path = filedialog.askopenfilename(
            title="Selecciona adb.exe",
            filetypes=[("adb", "adb.exe"), ("Ejecutables", "*.exe"), ("Todos", "*.*")])
        if path and os.path.isfile(path):
            self.adb_path = path
            self.cfg["adb_path"] = path
            save_config(self.cfg)
            self.log(f"✓ ADB configurado: {path}")
            self.refresh_devices()

    def action_screenshot(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(self._screenshot_worker)

    def _screenshot_worker(self):
        self.log("Capturando pantalla...")
        code, data, err = self.run_adb_binary(["exec-out", "screencap", "-p"], timeout=30)
        if code != 0 or not data:
            self.log(f"✗ No se pudo capturar. {err.decode('utf-8','replace') if err else ''}")
            return
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            data = data.replace(b"\r\n", b"\n")

        os.makedirs(self.screenshot_dir, exist_ok=True)
        fname = "screenshot_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
        fpath = os.path.join(self.screenshot_dir, fname)
        try:
            with open(fpath, "wb") as f:
                f.write(data)
            self.log(f"✓ Guardada: {fpath}")
        except Exception as e:
            self.log(f"✗ Error al guardar: {e}")
            return

        try:
            from PIL import Image
            img = Image.open(io.BytesIO(data))
            image_to_clipboard(img)
            self.log("✓ Copiada al portapapeles.")
        except Exception as e:
            self.log(f"⚠ No se pudo copiar al portapapeles: {e}")

    def toggle_record(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        if self.recording:
            self._stop_record()
        else:
            self._start_record()

    def _start_record(self):
        cmd = self._base_cmd(True) + ["shell", "screenrecord", self._rec_remote]
        try:
            self._rec_proc = subprocess.Popen(cmd, creationflags=CREATE_NO_WINDOW)
        except Exception as e:
            self.log(f"✗ No se pudo iniciar la grabación: {e}")
            return
        self.recording = True
        self._rec_start = time.time()
        self.record_btn.configure(fg_color=COLOR_RED, hover_color=COLOR_RED_HOVER,
                                  text_color="#ffffff")
        self.log("● Grabando... pulsa 'Detener' cuando quieras (máx. ~3 min).")
        self._tick_record()

    def _tick_record(self):
        if not self.recording:
            return
        el = int(time.time() - self._rec_start)
        self.record_btn.configure(text=f"Detener  ({el // 60:02d}:{el % 60:02d})")
        if el >= 179:
            self.log("Se alcanzó el límite del dispositivo (~3 min).")
            self._stop_record()
            return
        self._rec_timer = self.after(1000, self._tick_record)

    def _stop_record(self):
        self.recording = False
        if self._rec_timer:
            try:
                self.after_cancel(self._rec_timer)
            except Exception:
                pass
            self._rec_timer = None
        fondo, hover, color_texto, _ = BUTTON_COLORS["record"]
        self.record_btn.configure(text="Grabar pantalla", fg_color=fondo,
                                  hover_color=hover, text_color=color_texto)
        self.log("Deteniendo y guardando grabación...")
        self.threaded(self._stop_record_worker)

    def _stop_record_worker(self):
        self.run_adb(["shell", "pkill", "-INT", "screenrecord"], timeout=15)
        try:
            if self._rec_proc:
                self._rec_proc.wait(timeout=10)
        except Exception:
            pass
        time.sleep(1.2)
        os.makedirs(self.screenshot_dir, exist_ok=True)
        fname = "rec_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".mp4"
        local = os.path.join(self.screenshot_dir, fname)
        code, salida = self.run_adb_transfer(
            ["pull", self._rec_remote, local], "Trayendo la grabación", timeout=600)
        self.run_adb(["shell", "rm", "-f", self._rec_remote], timeout=15)
        if code == 0:
            self.log(f"✓ Grabación guardada: {local}")
        else:
            self.log(f"✗ No se pudo guardar la grabación: {salida}")

    def action_open_shots(self):
        os.makedirs(self.screenshot_dir, exist_ok=True)
        try:
            os.startfile(self.screenshot_dir)
        except Exception as e:
            self.log(f"✗ {e}")

    def action_scrcpy(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        if not self.scrcpy_path:
            self.scrcpy_path = self._locate_scrcpy()
            if not self.scrcpy_path:
                return

        def _w():
            env = os.environ.copy()
            if self.adb_path:
                env["ADB"] = self.adb_path
            args = [self.scrcpy_path]
            if self.selected_serial:
                args += ["-s", self.selected_serial]
            try:
                subprocess.Popen(
                    args, env=env, creationflags=CREATE_NO_WINDOW,
                    cwd=os.path.dirname(self.scrcpy_path))
                self.log("🖥 scrcpy iniciado. Se abrirá la ventana del dispositivo "
                         "(puedes controlarlo con ratón y teclado).")
            except Exception as e:
                self.log(f"✗ No se pudo iniciar scrcpy: {e}")
        self.threaded(_w)

    def _locate_scrcpy(self):
        messagebox.showinfo(
            "scrcpy no encontrado",
            "scrcpy permite ver y controlar el dispositivo en tiempo real.\n\n"
            "Si ya lo tienes, selecciona 'scrcpy.exe'.\n"
            "Si no, descárgalo (gratis) desde:\n"
            "https://github.com/Genymobile/scrcpy/releases\n"
            "Descomprime el ZIP y luego elige el scrcpy.exe de esa carpeta.")
        path = filedialog.askopenfilename(
            title="Selecciona scrcpy.exe",
            filetypes=[("scrcpy", "scrcpy.exe"), ("Ejecutables", "*.exe"),
                       ("Todos", "*.*")])
        if path and os.path.isfile(path):
            self.cfg["scrcpy_path"] = path
            save_config(self.cfg)
            self.log(f"✓ scrcpy configurado: {path}")
            return path
        return None

    def _adb_version(self):
        _, out, _ = self.run_adb(["version"], target_device=False, timeout=15)
        m = re.search(r"Version (\d+)", out)
        return int(m.group(1)) if m else 0

    def action_wifi_pair(self):
        if not self.ensure_adb():
            return
        win = ctk.CTkToplevel(self)
        win.title("Emparejar por WiFi")
        win.geometry("560x430")
        win.configure(fg_color=COLOR_BG)
        win.transient(self)
        self._cromo_windows(win)
        win.grab_set()
        win.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(win, text="Emparejar por WiFi  (Android 11 o superior)",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 4))
        ctk.CTkLabel(
            win,
            text=("En el dispositivo:  Ajustes → Opciones de desarrollador → "
                  "Depuración inalámbrica → Vincular dispositivo con código.\n\n"
                  "Ese diálogo muestra una IP:puerto y un código de 6 dígitos. "
                  "Ojo: ese puerto sirve sólo para emparejar y caduca. El puerto "
                  "de conexión es el otro, el de la pantalla anterior."),
            font=ctk.CTkFont(size=12), text_color=COLOR_MUTED,
            justify="left", wraplength=500
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 12))

        campos = ctk.CTkFrame(win, fg_color=COLOR_CARD, corner_radius=RADIO_TARJETA)
        campos.grid(row=2, column=0, sticky="ew", padx=18)
        campos.grid_columnconfigure(1, weight=1)

        def campo(texto, fila, marcador):
            ctk.CTkLabel(campos, text=texto, text_color=COLOR_MUTED, anchor="w",
                         font=ctk.CTkFont(size=12)
                         ).grid(row=fila, column=0, sticky="w", padx=(14, 10),
                                pady=(12 if fila == 0 else 6,
                                      12 if fila == 2 else 6))
            var = tk.StringVar()
            entrada = ctk.CTkEntry(campos, textvariable=var, height=32,
                                   placeholder_text=marcador)
            entrada.grid(row=fila, column=1, sticky="ew", padx=(0, 14),
                         pady=(12 if fila == 0 else 6, 12 if fila == 2 else 6))
            return var

        v_par = campo("IP y puerto del código", 0, "192.168.1.50:41234")
        v_cod = campo("Código de 6 dígitos", 1, "123456")
        v_con = campo("IP y puerto de conexión", 2, "opcional: se busca solo")

        botones = ctk.CTkFrame(win, fg_color="transparent")
        botones.grid(row=3, column=0, sticky="e", padx=18, pady=16)

        def emparejar():
            direccion, codigo = v_par.get().strip(), v_cod.get().strip()
            conexion = v_con.get().strip()
            if not direccion or not codigo:
                self.log("⚠ Hacen falta la IP:puerto y el código.")
                return
            win.destroy()
            self.threaded(lambda: self._pair_worker(direccion, codigo, conexion))

        ctk.CTkButton(botones, text="Cancelar", command=win.destroy, width=110,
                      fg_color="transparent", border_width=1,
                      border_color=COLOR_BORDER, hover_color=COLOR_BISEL
                      ).grid(row=0, column=0, padx=6)
        ctk.CTkButton(botones, text="Emparejar", command=emparejar, width=140,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER
                      ).grid(row=0, column=1, padx=6)

    def _pair_worker(self, direccion, codigo, conexion):
        version = self._adb_version()
        if version and version < 30:
            self.log(f"✗ Tu adb es la versión {version}; 'adb pair' necesita la 30 "
                     "o superior. Actualiza platform-tools.")
            return
        self.log(f"Emparejando con {direccion} ...")
        _, out, err = self.run_adb(["pair", direccion, codigo],
                                   target_device=False, timeout=60)
        salida = ((out or "") + (err or "")).strip()
        if "Successfully paired" not in salida:
            self.log(f"✗ No se pudo emparejar: {salida or 'sin respuesta'}")
            self.log("  El código caduca solo: vuelve a abrir el diálogo del "
                     "dispositivo y usa el nuevo, con su puerto.")
            return
        self.log("✓ Emparejado.")

        destino = conexion or self._puerto_de_conexion(direccion.split(":")[0])
        if not destino:
            self.log("  Ahora conéctate: en «Depuración inalámbrica» hay otra "
                     "IP:puerto, distinta a la del código. Úsala en "
                     "«Conectar por IP...».")
            return
        self.log(f"Conectando a {destino} ...")
        _, out, err = self.run_adb(["connect", destino], target_device=False,
                                   timeout=30)
        self.log("  " + (((out or "") + (err or "")).strip() or "sin respuesta"))
        self.after(300, self.refresh_devices)

    def _puerto_de_conexion(self, ip):
        _, out, _ = self.run_adb(["mdns", "services"], target_device=False,
                                 timeout=20)
        for linea in out.splitlines():
            if "_adb-tls-connect" in linea and ip in linea:
                m = re.search(re.escape(ip) + r":\d+", linea)
                if m:
                    return m.group(0)
        return ""

    def action_open_app(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(lambda: self._package_picker(
            "Abrir una app", "Abrir", self._do_open_app))

    def _do_open_app(self, pkg):
        _, out, err = self.run_adb(
            ["shell", f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1"],
            timeout=30)
        if "No activities found" in (out + err):
            self.log(f"✗ {pkg} no tiene pantalla de inicio: no se puede abrir así.")
        else:
            self.log(f"✓ Abierta {pkg}.")

    def action_permissions(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(lambda: self._package_picker(
            "Permisos de una app", "Ver permisos", self._abrir_permisos))

    def _leer_permisos(self, pkg):
        _, out, _ = self.run_adb(["exec-out", "dumpsys", "package", pkg], timeout=45)
        permisos, vistos, dentro = [], set(), False
        for cruda in out.splitlines():
            linea = cruda.strip()
            if linea.endswith("permissions:"):
                dentro = "runtime permissions" in linea
                continue
            if not dentro:
                continue
            m = re.match(r"([\w.]+):\s*granted=(true|false)", linea)
            if not m:
                if linea and not linea.startswith("android.") and ":" not in linea:
                    dentro = False
                continue
            if m.group(1) not in vistos:
                vistos.add(m.group(1))
                permisos.append((m.group(1), m.group(2) == "true"))
        permisos.sort()
        return permisos

    def _abrir_permisos(self, pkg):
        permisos = self._leer_permisos(pkg)
        if not permisos:
            self.log(f"  {pkg} no pide permisos de los que se conceden en tiempo "
                     "de ejecución (los de instalación no se pueden cambiar).")
            return
        self.after(0, lambda: self._permisos_window(pkg, permisos))

    def _permisos_window(self, pkg, permisos):
        win = ctk.CTkToplevel(self)
        win.title(f"Permisos de {pkg}")
        win.geometry("560x540")
        win.configure(fg_color=COLOR_BG)
        win.transient(self)
        self._cromo_windows(win)
        win.grab_set()
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(win, text=pkg, font=ctk.CTkFont(size=15, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(win, text=f"{len(permisos)} permisos de tiempo de ejecución. "
                               "El cambio se aplica al momento.",
                     text_color=COLOR_MUTED, font=ctk.CTkFont(size=12)
                     ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 10))

        lista = ctk.CTkScrollableFrame(win, fg_color=COLOR_CARD)
        lista.grid(row=2, column=0, sticky="nsew", padx=18)
        lista.grid_columnconfigure(0, weight=1)

        for i, (permiso, concedido) in enumerate(permisos):
            interruptor = ctk.CTkSwitch(
                lista, text=permiso.replace("android.permission.", ""),
                font=ctk.CTkFont(size=12), progress_color=COLOR_GREEN,
                button_color="#ffffff", fg_color=COLOR_RAISED)
            if concedido:
                interruptor.select()
            interruptor.configure(
                command=lambda p=permiso, s=interruptor:
                self._cambiar_permiso(pkg, p, s))
            interruptor.grid(row=i, column=0, sticky="w", padx=12, pady=6)

        ctk.CTkButton(win, text="Cerrar", command=win.destroy, width=110,
                      fg_color=COLOR_BISEL, border_width=1,
                      border_color=COLOR_BORDER, hover_color=COLOR_BISEL_HOVER
                      ).grid(row=3, column=0, sticky="e", padx=18, pady=14)

    def _cambiar_permiso(self, pkg, permiso, interruptor):
        conceder = bool(interruptor.get())
        corto = permiso.replace("android.permission.", "")

        def _w():
            accion = "grant" if conceder else "revoke"
            code, out, err = self.run_adb(["shell", "pm", accion, pkg, permiso],
                                          timeout=25)
            salida = (out + err).strip()
            if code == 0 and not salida:
                self.log(f"✓ {'Concedido' if conceder else 'Revocado'}: {corto}")
            else:
                self.log(f"✗ {corto}: {salida or 'no se pudo cambiar'}")
                self.after(0, interruptor.deselect if conceder
                           else interruptor.select)
        self.threaded(_w)

    def action_animations(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(self._animations_worker)

    def _animations_worker(self):
        claves = ("window_animation_scale", "transition_animation_scale",
                  "animator_duration_scale")
        _, actual, _ = self.run_adb(
            ["exec-out", "settings", "get", "global", claves[0]], timeout=15)
        apagadas = actual.strip() in ("0", "0.0")
        nuevo = "1" if apagadas else "0"
        for clave in claves:
            self.run_adb(["shell", f"settings put global {clave} {nuevo}"],
                         timeout=15)
        self.log("✓ Animaciones: " + ("activadas" if nuevo == "1" else
                 "desactivadas (la interfaz responde bastante más rápido)"))

    def action_dont_keep_activities(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(lambda: self._toggle_setting(
            "No mantener actividades", "global", "always_finish_activities"))

    def action_stay_awake(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(lambda: self._toggle_setting(
            "Permanecer activo al cargar", "global", "stay_on_while_plugged_in",
            on_val="7", off_val="0"))

    def action_gpu_profile(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(lambda: self._toggle_prop(
            "Perfil de renderizado GPU", "debug.hwui.profile",
            "visual_bars", "false", poke=True))

    def _toggle_prop(self, name, prop, on_val, off_val, poke=False):
        _, cur, _ = self.run_adb(["shell", "getprop", prop], timeout=15)
        cur = cur.strip()
        new = off_val if cur == on_val else on_val
        self.run_adb(["shell", "setprop", prop, new], timeout=15)
        if poke:
            self.run_adb(["shell", "service", "call", "activity", "1599295570"], timeout=15)
        estado = "activado" if new == on_val else "desactivado"
        self.log(f"✓ {name}: {estado}")

    def _toggle_setting(self, name, ns, key, on_val="1", off_val="0"):
        _, cur, _ = self.run_adb(["shell", "settings", "get", ns, key], timeout=15)
        cur = cur.strip()
        new = off_val if cur == on_val else on_val
        self.run_adb(["shell", "settings", "put", ns, key, new], timeout=15)
        estado = "activado" if new == on_val else "desactivado"
        self.log(f"✓ {name}: {estado}")

    def action_layout_bounds(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(lambda: self._toggle_prop(
            "Límites de diseño", "debug.layout", "true", "false", poke=True))

    def action_overdraw(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(lambda: self._toggle_prop(
            "Overdraw GPU", "debug.hwui.overdraw", "show", "false", poke=True))

    def action_show_touches(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(lambda: self._toggle_setting(
            "Mostrar toques", "system", "show_touches"))

    def action_pointer(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(lambda: self._toggle_setting(
            "Ubicación del puntero", "system", "pointer_location"))

    def _get_packages(self, only_third_party=True):
        args = ["shell", "pm", "list", "packages"]
        if only_third_party:
            args.append("-3")
        _, out, _ = self.run_adb(args, timeout=30)
        pkgs = sorted(l.replace("package:", "").strip()
                      for l in out.splitlines() if l.startswith("package:"))
        return pkgs

    def action_list_packages(self):
        self._listar_versiones(solo_terceros=True)

    def action_list_system_packages(self):
        self._listar_versiones(solo_terceros=False)

    def _listar_versiones(self, solo_terceros=True):
        if not (self.ensure_adb() and self.ensure_device()):
            return

        def _w():
            titulo = "Apps de terceros" if solo_terceros else "Todas las apps"
            self.log(f"Consultando {titulo.lower()} y sus versiones...")
            self._progress_show("Consultando versiones")
            try:
                _, salida, _ = self.run_adb(
                    ["exec-out", "sh", "-c",
                     CMD_VERSIONES % ("-3" if solo_terceros else "")],
                    timeout=300)
            finally:
                self._progress_hide()

            apps = self._parse_versiones(salida)
            if not apps:
                self.log("No se encontró ninguna app. ¿Responde el dispositivo?")
                return
            filas = [(p, v or "?", c or "") for p, v, c in apps]
            self.log(f"✓ {len(apps)} app(s). Se abre el listado en una ventana.")
            sin_version = [p for p, v, _ in apps if not v]
            if sin_version:
                self.log(f"  ({len(sin_version)} sin versionName declarado)")
            self.after(0, lambda: self.ventana_tabla(
                titulo, ["Paquete", "Versión", "Código"], filas, [360, 150, 110]))
        self.threaded(_w)

    @staticmethod
    def _parse_versiones(salida):
        datos, actual = {}, None
        for cruda in (salida or "").splitlines():
            linea = cruda.strip()
            if linea.startswith("PKG:"):
                actual = linea[4:].strip()
                if actual:
                    datos.setdefault(actual, ["", ""])
                continue
            if not actual:
                continue
            m = re.search(r"versionName=(\S+)", linea)
            if m and not datos[actual][0]:
                datos[actual][0] = m.group(1)
            m = re.search(r"versionCode=(\d+)", linea)
            if m and not datos[actual][1]:
                datos[actual][1] = m.group(1)
        return [(p, datos[p][0], datos[p][1]) for p in sorted(datos)]

    def action_uninstall(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(lambda: self._package_picker(
            "Desinstalar aplicación", "Desinstalar", self._do_uninstall,
            danger=True))

    def _do_uninstall(self, pkg):
        code, out, err = self.run_adb(["uninstall", pkg], timeout=60)
        if "Success" in out:
            self.log(f"✓ Desinstalada: {pkg}")
            return
        salida = (out or err).strip()
        if "DEVICE_POLICY" not in salida.upper():
            self.log(f"✗ Error al desinstalar {pkg}: {salida}")
            return
        self.log(f"⚠ {pkg} es administrador de dispositivos; quitando el permiso…")
        comps = self._admin_components(pkg)
        if not comps:
            self.log(f"✗ No se encontró el componente de administrador de {pkg}. "
                     f"Quítalo a mano en Ajustes › Seguridad › Administradores.")
            return
        for comp in comps:
            c, o, e = self.run_adb(
                ["exec-out", "dpm", "remove-active-admin", comp], timeout=30)
            salida_dpm = (o or e).strip()
            if "Success" in o or "removed" in salida_dpm.lower():
                self.log(f"  ✓ Administrador desactivado: {comp}")
            else:
                self.log(f"  ✗ No se pudo desactivar {comp}: {salida_dpm}")
                if "owner" in salida_dpm.lower():
                    self.log(f"    ({pkg} es propietario del dispositivo; no se "
                             f"puede quitar por adb.)")
        code, out, err = self.run_adb(["uninstall", pkg], timeout=60)
        if "Success" in out:
            self.log(f"✓ Desinstalada: {pkg}")
        else:
            self.log(f"✗ Error al desinstalar {pkg}: {(out or err).strip()}")

    def _admin_components(self, pkg):
        comps = []

        def apuntar(comp):
            comp = comp.rstrip(":")
            if comp not in comps:
                comps.append(comp)

        code, out, err = self.run_adb(["exec-out", "dumpsys", "device_policy"])
        for m in re.finditer(re.escape(pkg) + r"/[\w.$]+", out):
            apuntar(m.group(0))
        if comps:
            return comps

        code, out, err = self.run_adb(["exec-out", "dumpsys", "package", pkg])
        lineas = out.splitlines()
        for i, linea in enumerate(lineas):
            if linea.strip().endswith("DEVICE_ADMIN_ENABLED:"):
                for sig in lineas[i + 1:i + 4]:
                    m = re.search(re.escape(pkg) + r"/[\w.$]+", sig)
                    if m:
                        apuntar(m.group(0))
                        break
        return comps

    def action_force_stop(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(lambda: self._package_picker(
            "Forzar detención", "Detener", self._do_force_stop))

    def _do_force_stop(self, pkg):
        self.run_adb(["shell", "am", "force-stop", pkg], timeout=30)
        self.log(f"✓ Detenida: {pkg}")

    def action_clear_data(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(lambda: self._package_picker(
            "Borrar datos de aplicación", "Borrar datos", self._do_clear_data,
            danger=True))

    def _do_clear_data(self, pkg):
        code, out, err = self.run_adb(["shell", "pm", "clear", pkg], timeout=30)
        if "Success" in out:
            self.log(f"✓ Datos borrados: {pkg}")
        else:
            self.log(f"✗ Error: {(out or err).strip()}")

    def action_install(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        path = filedialog.askopenfilename(
            title="Selecciona un APK", filetypes=[("APK", "*.apk"), ("Todos", "*.*")])
        if not path:
            return
        def _w():
            nombre = os.path.basename(path)
            self.log(f"Instalando {nombre}...")
            code, salida = self.run_adb_transfer(["install", "-r", path],
                                                 f"Instalando {nombre}", timeout=600)
            if "Success" in salida:
                self.log("✓ Instalación correcta.")
            else:
                self.log(f"✗ Error: {salida or 'sin detalle'}")
        self.threaded(_w)

    def action_reboot(self, mode=None):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        nombre = {None: "reiniciar", "recovery": "reiniciar a Recovery",
                  "bootloader": "reiniciar a Bootloader"}[mode]
        if not messagebox.askyesno("Confirmar", f"¿Seguro que deseas {nombre} el dispositivo?"):
            return
        def _w():
            args = ["reboot"] + ([mode] if mode else [])
            self.run_adb(args, timeout=20)
            self.log(f"✓ Comando enviado: {nombre}.")
        self.threaded(_w)

    def action_poweroff(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        if not messagebox.askyesno("Confirmar", "¿Apagar el dispositivo?"):
            return
        def _w():
            self.run_adb(["shell", "reboot", "-p"], timeout=20)
            self.log("✓ Comando de apagado enviado.")
        self.threaded(_w)

    def action_screen_power(self, on):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        key = "224" if on else "223"
        def _w():
            self.run_adb(["shell", "input", "keyevent", key], timeout=15)
            self.log(f"✓ Pantalla {'encendida' if on else 'apagada'}.")
        self.threaded(_w)

    def action_wifi_enable(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        def _w():
            self.run_adb(["tcpip", "5555"], timeout=20)
            _, out, _ = self.run_adb(["shell", "ip", "-f", "inet", "addr", "show", "wlan0"], timeout=15)
            m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", out)
            ip = m.group(1) if m else "IP_DEL_DISPOSITIVO"
            self.log(f"✓ ADB WiFi activado. Conéctate con: adb connect {ip}:5555")
        self.threaded(_w)

    def action_wifi_connect(self):
        ip = self._ask_text("Conectar por WiFi", "IP del dispositivo (ej. 192.168.1.50):", "")
        if not ip:
            return
        if ":" not in ip:
            ip = ip + ":5555"
        def _w():
            code, out, err = self.run_adb(["connect", ip], target_device=False, timeout=25)
            self.log((out or err).strip())
            self.after(300, self.refresh_devices)
        self.threaded(_w)

    def action_wifi_scan(self):
        if not self.ensure_adb():
            return
        self.threaded(self._scan_worker)

    def _scan_worker(self, port=5555):
        bases = self._bases_de_red()
        if not bases:
            self.log("✗ No pude determinar la red local. Conéctate por IP a mano.")
            return
        timeout = float(self.cfg.get("scan_timeout", 1.5))
        workers = int(self.cfg.get("scan_workers", 256))
        pasadas = int(self.cfg.get("scan_pasadas", 2))
        self.log("Buscando dispositivos con ADB por WiFi (puerto %d) en %s "
                 "[timeout %.1fs, %d pasadas] ..."
                 % (port, ", ".join(b + ".0/24" for b in bases), timeout, pasadas))
        encontrados = self._escanear_red(bases, port, timeout, workers, pasadas)
        if not encontrados:
            self.log("No se encontró ningún equipo con ADB por WiFi. Comprueba que "
                     "el equipo tiene «Habilitar ADB por WiFi (5555)», está en esta "
                     "misma red y no está en reposo. Si tarda en responder, sube "
                     "«scan_timeout» en config.json (p. ej. 3).")
            return
        self.log("✓ %d con el puerto %d abierto: %s"
                 % (len(encontrados), port, ", ".join(encontrados)))
        self.after(0, lambda: self._ventana_encontrados(encontrados, port))

    def _bases_de_red(self):
        ips = set()
        try:
            for res in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                ips.add(res[4][0])
        except Exception:
            pass
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ips.add(s.getsockname()[0])
            s.close()
        except Exception:
            pass
        bases = []
        for ip in ips:
            if ip.startswith("127.") or ":" in ip:
                continue
            base = ".".join(ip.split(".")[:3])
            if base not in bases:
                bases.append(base)
        return bases

    def _escanear_red(self, bases, port=5555, timeout=1.5, workers=256,
                      pasadas=2):
        objetivos = ["%s.%d" % (b, h) for b in bases for h in range(1, 255)]
        encontrados = []
        pendientes = objetivos
        pasadas = max(1, pasadas)
        self._progress_show("Explorando la red...")
        self._progress_determinado()
        for n in range(pasadas):
            if not pendientes:
                break
            nuevos = self._barrido(pendientes, port, timeout, workers,
                                   n / pasadas, 1.0 / pasadas)
            encontrados.extend(nuevos)
            hallados = set(encontrados)
            pendientes = [ip for ip in pendientes if ip not in hallados]
        self._progress_hide()
        return sorted(encontrados, key=lambda s: [int(x) for x in s.split(".")])

    def _barrido(self, objetivos, port, timeout, workers, base_frac, paso_frac):
        total = len(objetivos)
        hall = []
        hechos = [0]
        lock = threading.Lock()

        def sondear(ip):
            try:
                with socket.create_connection((ip, port), timeout=timeout):
                    abierto = True
            except Exception:
                abierto = False
            with lock:
                hechos[0] += 1
                if abierto:
                    hall.append(ip)
                if hechos[0] % 8 == 0 or hechos[0] == total:
                    self._progress_set(base_frac + paso_frac * hechos[0] / total)
            return abierto

        with ThreadPoolExecutor(max_workers=min(workers, total)) as ex:
            list(ex.map(sondear, objetivos))
        return hall

    def _conectar_ips(self, ips, port=5555):
        ok = 0
        for ip in ips:
            destino = ip if ":" in ip else "%s:%d" % (ip, port)
            _, out, err = self.run_adb(["connect", destino], target_device=False,
                                       timeout=25)
            salida = (out or err).strip()
            self.log("  " + (salida or "sin respuesta"))
            if "connected" in salida.lower():
                ok += 1
        self.log("✓ Conectados %d de %d." % (ok, len(ips)))
        self.after(300, self.refresh_devices)

    def _ventana_encontrados(self, ips, port=5555):
        conectados = {s.split(":")[0] for s in (self.device_map or {}).values() if s}
        win = ctk.CTkToplevel(self)
        win.title("Dispositivos en la red")
        win.geometry("440x460")
        win.configure(fg_color=COLOR_BG)
        win.transient(self)
        self._cromo_windows(win)
        win.grab_set()
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(win, text="Dispositivos con ADB por WiFi",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        listframe = ctk.CTkScrollableFrame(win, fg_color=COLOR_CARD)
        listframe.grid(row=1, column=0, sticky="nsew", padx=16, pady=6)
        listframe.grid_columnconfigure(0, weight=1)

        seleccion = {ip: True for ip in ips}
        filas = {}

        def pintar(ip):
            activa = seleccion[ip]
            filas[ip].configure(
                fg_color=COLOR_ACCENT if activa else "transparent",
                hover_color=COLOR_ACCENT_HOVER if activa else COLOR_RAISED,
                text_color="#ffffff" if activa else COLOR_TEXT)

        def alternar(ip):
            seleccion[ip] = not seleccion[ip]
            pintar(ip)
            refrescar_boton()

        for ip in ips:
            ya = ip in conectados
            etiqueta = ip + (":%d" % port) + ("   · ya conectado" if ya else "")
            b = ctk.CTkButton(listframe, text=etiqueta, anchor="w", height=30,
                              command=lambda p=ip: alternar(p))
            b.grid(sticky="ew", pady=1)
            filas[ip] = b
            pintar(ip)

        btnbar = ctk.CTkFrame(win, fg_color="transparent")
        btnbar.grid(row=2, column=0, sticky="ew", padx=16, pady=12)
        btnbar.grid_columnconfigure(0, weight=1)

        def refrescar_boton():
            n = sum(1 for v in seleccion.values() if v)
            conectar.configure(text="Conectar (%d)" % n,
                               state="normal" if n else "disabled")

        def confirmar():
            elegidos = [ip for ip, v in seleccion.items() if v]
            if not elegidos:
                return
            win.destroy()
            self.threaded(lambda: self._conectar_ips(elegidos, port))

        ctk.CTkButton(btnbar, text="Cancelar", command=win.destroy,
                      fg_color="transparent", border_width=1,
                      border_color=COLOR_BORDER, hover_color=COLOR_BISEL, width=110
                      ).grid(row=0, column=1, padx=6)
        conectar = ctk.CTkButton(btnbar, text="Conectar", command=confirmar,
                                 width=150, fg_color=COLOR_ACCENT,
                                 hover_color=COLOR_ACCENT_HOVER, text_color="#ffffff")
        conectar.grid(row=0, column=2, padx=6)
        refrescar_boton()

    def action_run_command(self):
        linea = self.cmd_var.get().strip()
        if not linea:
            return
        if not self.ensure_adb():
            return
        try:
            args = shlex.split(linea)
        except ValueError as e:
            self.log(f"✗ No entiendo el comando: {e}")
            return
        if args and args[0].lower() in ("adb", "adb.exe"):
            args = args[1:]
        if not args:
            return

        GLOBALES = {"devices", "connect", "disconnect", "kill-server",
                    "start-server", "version", "help", "reconnect"}
        target = args[0] not in GLOBALES
        if target and not self.ensure_device():
            return

        self.cmd_hist.append(linea)
        self.cmd_hist_idx = len(self.cmd_hist)
        self.cmd_var.set("")

        def _w():
            self.log(f"$ adb {linea}")
            if args[0] == "logcat" and not any(a.startswith(("-d", "-t"))
                                               for a in args):
                self.log("  ⚠ 'logcat' sin -d ni -t no termina solo: se corta a los "
                         "2 minutos.")
            code, out, err = self.run_adb(args, target_device=target, timeout=120)
            salida = (out or "") + (err or "")
            if salida.strip():
                for line in salida.splitlines():
                    if line.strip():
                        self.log("  " + line.rstrip())
            elif code == 0:
                self.log("  (sin salida)")
            if code != 0:
                self.log(f"  [código de salida {code}]")
        self.threaded(_w)

    def _cmd_history(self, paso):
        if not self.cmd_hist:
            return "break"
        self.cmd_hist_idx = max(0, min(len(self.cmd_hist),
                                       self.cmd_hist_idx + paso))
        self.cmd_var.set(self.cmd_hist[self.cmd_hist_idx]
                         if self.cmd_hist_idx < len(self.cmd_hist) else "")
        self.cmd_entry.icursor("end")
        return "break"

    def action_extract_apk(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        destino = filedialog.askdirectory(title="¿Dónde guardo el APK?")
        if not destino:
            return
        self.threaded(lambda: self._package_picker(
            "Extraer APK instalado", "Extraer",
            lambda pkg: self._do_extract_apk(pkg, destino)))

    def _do_extract_apk(self, pkg, destino):
        _, out, _ = self.run_adb(["exec-out", "pm", "path", pkg], timeout=30)
        rutas = [l.replace("package:", "").strip() for l in out.splitlines()
                 if l.startswith("package:")]
        if not rutas:
            self.log(f"✗ No se encontró el APK de {pkg}. ¿Sigue instalada?")
            return

        _, dp, _ = self.run_adb(
            ["exec-out", "sh", "-c", f"dumpsys package {pkg} | grep -m1 versionName"],
            timeout=30)
        version = dp.strip().split("=", 1)[-1].strip() if "=" in dp else ""
        self.log(f"──── Extrayendo {pkg}"
                 f"{' v' + version if version else ''} ────")
        if len(rutas) > 1:
            self.log(f"  La app está partida en {len(rutas)} APK (split apks): "
                     "hacen falta todos para reinstalarla.")

        for ruta in rutas:
            base = posixpath.basename(ruta)
            if len(rutas) == 1:
                nombre = f"{pkg}{'-' + version if version else ''}.apk"
            else:
                nombre = f"{pkg}{'-' + version if version else ''}-{base}"
            final = os.path.join(destino, nombre)
            self.log(f"  {ruta}  →  {nombre}")
            code, o, e = self.run_adb(["pull", ruta, final], timeout=600)
            if code == 0 and os.path.isfile(final):
                self.log(f"  ✓ {os.path.getsize(final) / 1048576:.1f} MB")
            else:
                self.log(f"  ✗ {(o or e).strip() or 'falló el pull'}")
        self.log(f"✓ Guardado en {destino}")

    def _ruta_log(self, sufijo):
        os.makedirs(self.log_dir, exist_ok=True)
        marca = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.log_dir, f"logcat_{sufijo}_{marca}.txt")

    @staticmethod
    def _sanea(texto):
        limpio = re.sub(r"[^A-Za-z0-9._-]+", "_", texto or "").strip("_")
        return limpio or "dispositivo"

    def _capturar_logcat(self, filtro=()):
        base = ["exec-out", "logcat", "-d", "-v", "threadtime", "-b", "all"]
        code, out, err = self.run_adb(base + list(filtro), timeout=300)
        if code != 0 or not out.strip():
            base = ["exec-out", "logcat", "-d", "-v", "threadtime"]
            code, out, err = self.run_adb(base + list(filtro), timeout=300)
            if code != 0 and err.strip():
                self.log(f"  ⚠ {err.strip().splitlines()[0]}")
        return out, "adb " + " ".join(base + list(filtro))

    def _cabecera_log(self, props, comando, extra=""):
        raya = "# " + "-" * 68
        lineas = [
            raya,
            f"# ADB Toolbox — registro extraído el "
            f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}",
            f"# Dispositivo : {props.get('ro.product.model', '?')}  "
            f"({self.selected_serial})",
            f"# Android     : {props.get('ro.build.version.release', '?')}  "
            f"(SDK {props.get('ro.build.version.sdk', '?')})",
            f"# Compilación : {self._version_firmware(props) or props.get('ro.build.display.id', '?')}",
            f"# Comando     : {comando}",
        ]
        if extra:
            lineas.append(f"# {extra}")
        lineas.append(raya)
        return "\n".join(lineas) + "\n"

    def _guardar_log(self, ruta, cabecera, lineas):
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(cabecera)
            f.write("\n".join(lineas))
            f.write("\n")
        return os.path.getsize(ruta)

    def _aviso_guardado(self, ruta, lineas):
        tam = os.path.getsize(ruta)
        unidad = f"{tam / 1048576:.1f} MB" if tam > 1048576 else f"{tam / 1024:.0f} KB"
        self.log(f"✓ {lineas} líneas guardadas  ({unidad})")
        self.log(f"  {ruta}")

    def action_log_full(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return

        def _w():
            self.log("Extrayendo el registro del dispositivo...")
            props = self._getprops_all()
            self._progress_show("Extrayendo registro")
            try:
                texto, comando = self._capturar_logcat()
            finally:
                self._progress_hide()
            lineas = texto.splitlines()
            if not lineas:
                self.log("✗ El dispositivo no devolvió nada.")
                return
            ruta = self._ruta_log(self._sanea(props.get("ro.product.model")))
            self._guardar_log(ruta, self._cabecera_log(props, comando), lineas)
            self._aviso_guardado(ruta, len(lineas))
        self.threaded(_w)

    def action_log_app(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        self.threaded(lambda: self._package_picker(
            "Registro de una app", "Extraer registro", self._do_log_app))

    @staticmethod
    def _linea_de_app(linea, pids, pkg):
        if pkg in linea:
            return True
        if pids:
            partes = linea.split()
            if len(partes) >= 3 and partes[2] in pids:
                return True
        return False

    def _do_log_app(self, pkg):
        self.log(f"Extrayendo el registro de {pkg}...")
        props = self._getprops_all()
        _, salida_pid, _ = self.run_adb(["exec-out", "pidof", pkg], timeout=20)
        pids = set(salida_pid.split())
        if pids:
            self.log(f"  Corriendo con pid {', '.join(sorted(pids))}.")
        else:
            self.log("  ⚠ La app no está corriendo: sólo saldrán las líneas que "
                     "nombren el paquete.")

        self._progress_show(f"Extrayendo registro de {pkg}")
        try:
            texto, comando = self._capturar_logcat()
        finally:
            self._progress_hide()

        todas = texto.splitlines()
        lineas = [l for l in todas if self._linea_de_app(l, pids, pkg)]
        if not lineas:
            self.log(f"✗ Ni una línea de {pkg} en el buffer. ¿Se limpió hace poco?")
            return
        ruta = self._ruta_log(self._sanea(pkg))
        extra = (f"Filtrado de {len(todas)} líneas: pid {', '.join(sorted(pids))} "
                 f"o mención de {pkg}" if pids else
                 f"Filtrado de {len(todas)} líneas por mención de {pkg} "
                 "(la app no estaba corriendo)")
        self._guardar_log(ruta, self._cabecera_log(props, comando, extra), lineas)
        self._aviso_guardado(ruta, len(lineas))

    def action_log_errors(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return

        def _w():
            self.log("Buscando errores y cierres inesperados...")
            props = self._getprops_all()
            self._progress_show("Extrayendo errores")
            try:
                texto, comando = self._capturar_logcat(["*:E"])
            finally:
                self._progress_hide()
            lineas = texto.splitlines()
            if not lineas:
                self.log("✓ Ni un error en el buffer del dispositivo.")
                return
            ruta = self._ruta_log(self._sanea(props.get("ro.product.model")) + "_errores")
            self._guardar_log(ruta, self._cabecera_log(props, comando,
                                                       "Sólo nivel E (error) y superior"),
                              lineas)
            self._aviso_guardado(ruta, len(lineas))
            for l in lineas[-8:]:
                self.log("  " + l.strip())
        self.threaded(_w)

    def action_log_vendor(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        win = ctk.CTkToplevel(self)
        win.title("Registros del fabricante")
        win.geometry("560x330")
        win.configure(fg_color=COLOR_BG)
        win.transient(self)
        self._cromo_windows(win)
        win.grab_set()
        win.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(win, text="Registros guardados en el equipo",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 4))
        ctk.CTkLabel(
            win,
            text=("Se empaquetan en el propio equipo y se traen comprimidos:\n\n"
                  f"   ·  {LOG_VENDOR_DIRS[0]}   (logcat y kernel guardados en disco)\n"
                  f"   ·  {LOG_VENDOR_DIRS[1]}   (recolector del fabricante)\n\n"
                  "La primera carpeta necesita root, que en estos equipos "
                  "funciona. Comprimir tarda un rato: son cientos de MB de texto."),
            font=ctk.CTkFont(size=12), text_color=COLOR_MUTED,
            justify="left", wraplength=510
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 14))

        def lanzar(dias):
            win.destroy()
            self.threaded(lambda: self._vendor_worker(dias))

        botones = ctk.CTkFrame(win, fg_color="transparent")
        botones.grid(row=2, column=0, sticky="ew", padx=18)
        botones.grid_columnconfigure((0, 1), weight=1)
        self._styled_button(botones, "Últimos 7 días", lambda: lanzar(7),
                            "green", height=46
                            ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self._styled_button(botones, "Todo lo que haya", lambda: lanzar(0),
                            "accent", height=46
                            ).grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ctk.CTkButton(win, text="Cancelar", command=win.destroy, width=110,
                      fg_color="transparent", border_width=1,
                      border_color=COLOR_BORDER, hover_color=COLOR_BISEL
                      ).grid(row=3, column=0, sticky="e", padx=18, pady=16)

    def _vendor_worker(self, dias):
        props = self._getprops_all()
        rooteado = self._tv_root()
        if not rooteado:
            self.log("  ⚠ Sin root: sólo se traerá lo que hay en /sdcard.")
        carpetas = [d for d in LOG_VENDOR_DIRS
                    if rooteado or d.startswith("/sdcard")]

        lista = f"{TMP_EQUIPO}/adbtoolbox_lista.txt"
        paquete = f"{TMP_EQUIPO}/adbtoolbox_registros.tgz"
        filtro = f" -mtime -{dias}" if dias else ""
        self.log("Buscando archivos en el equipo...")
        self.run_adb(["shell", f"rm -f {lista} {paquete}"], timeout=30)
        self.run_adb(
            ["shell", f"find {' '.join(carpetas)} -type f{filtro} > {lista} 2>/dev/null"],
            timeout=120)
        _, cuenta, _ = self.run_adb(
            ["exec-out", "sh", "-c", f"wc -l < {lista}"], timeout=30)
        try:
            total = int(cuenta.strip())
        except ValueError:
            total = 0
        if not total:
            self.log("✗ No hay archivos que traer" +
                     (f" de los últimos {dias} días." if dias else "."))
            if rooteado:
                self._tv_unroot()
            return
        self.log(f"  {total} archivo(s). Comprimiendo en el equipo "
                 "(esto es lo que más tarda)...")

        self._progress_show("Comprimiendo en el equipo")
        try:
            code, out, err = self.run_adb(
                ["shell", f"tar -czf {paquete} -T {lista} 2>/dev/null; "
                          f"chmod 666 {paquete}"], timeout=1800)
        finally:
            self._progress_hide()

        _, tam, _ = self.run_adb(
            ["exec-out", "sh", "-c", f"wc -c < {paquete} 2>/dev/null"], timeout=30)
        try:
            bytes_paquete = int(tam.strip())
        except ValueError:
            bytes_paquete = 0
        if bytes_paquete < 100:
            self.log("✗ No se pudo empaquetar en el equipo.")
            self.run_adb(["shell", f"rm -f {lista} {paquete}"], timeout=30)
            if rooteado:
                self._tv_unroot()
            return
        self.log(f"  Paquete de {bytes_paquete / 1048576:.1f} MB. Trayéndolo...")

        os.makedirs(self.log_dir, exist_ok=True)
        nombre = ("registros_%s_%s%s.tgz" % (
            self._sanea(props.get("ro.product.model")),
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
            f"_{dias}dias" if dias else "_todo"))
        destino = os.path.join(self.log_dir, nombre)
        code, salida = self.run_adb_transfer(["pull", paquete, destino],
                                             "Trayendo registros", timeout=3600)

        self.run_adb(["shell", f"rm -f {lista} {paquete}"], timeout=60)
        if rooteado:
            self._tv_unroot()

        if code == 0 and os.path.isfile(destino):
            self.log(f"✓ {os.path.getsize(destino) / 1048576:.1f} MB → {destino}")
            self.log("  Se abre con el Explorador de Windows, 7-Zip o WinRAR.")
        else:
            self.log(f"✗ {salida or 'no se pudo traer el paquete'}")

    def action_bugreport(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        if not messagebox.askyesno(
                "Bugreport completo",
                "Android genera un informe con todo lo que sabe de sí mismo:\n\n"
                "  ·  logcat y mensajes del kernel\n"
                "  ·  crashes nativos (tombstones) y apps colgadas (ANR)\n"
                "  ·  el historial de fallos del sistema (dropbox)\n"
                "  ·  el estado completo: batería, paquetes, red, actividades\n\n"
                "Tarda varios minutos y ocupa decenas de MB. No necesita root.\n\n"
                "¿Continuar?"):
            return

        def _w():
            props = self._getprops_all()
            os.makedirs(self.log_dir, exist_ok=True)
            destino = os.path.join(self.log_dir, "bugreport_%s_%s.zip" % (
                self._sanea(props.get("ro.product.model")),
                datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
            self.log("Generando el bugreport... (varios minutos, no cierres la app)")
            code, salida = self.run_adb_transfer(["bugreport", destino],
                                                 "Generando bugreport", timeout=1800)
            if os.path.isfile(destino):
                self.log(f"✓ {os.path.getsize(destino) / 1048576:.1f} MB → {destino}")
            else:
                if salida and len(salida) > 500:
                    alterno = destino[:-4] + ".txt"
                    with open(alterno, "w", encoding="utf-8", newline="\n") as f:
                        f.write(salida)
                    self.log(f"✓ (formato antiguo, texto plano) → {alterno}")
                else:
                    self.log(f"✗ {salida or 'el equipo no generó el informe'}")
        self.threaded(_w)

    def action_log_clear(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        if not messagebox.askyesno(
                "Limpiar el registro",
                "Se borra el buffer de logcat del dispositivo.\n\n"
                "Es lo que se hace antes de reproducir un fallo: limpias, "
                "provocas el problema y extraes el registro, que sale limpio.\n\n"
                "¿Continuar?"):
            return

        def _w():
            code, out, err = self.run_adb(["exec-out", "logcat", "-b", "all", "-c"],
                                          timeout=30)
            if code != 0:
                code, out, err = self.run_adb(["exec-out", "logcat", "-c"], timeout=30)
            if code == 0:
                self.log("✓ Registro del dispositivo limpio.")
            else:
                self.log(f"✗ {(out or err).strip() or 'no se pudo limpiar'}")
        self.threaded(_w)

    def action_open_logs(self):
        os.makedirs(self.log_dir, exist_ok=True)
        try:
            os.startfile(self.log_dir)
        except Exception as e:
            self.log(f"✗ {e}")

    def _tv_start(self, worker):
        if self._tv_busy:
            self.log("⏳ Ya hay una operación de TV Box en curso.")
            return
        self._tv_busy = True

        def _w():
            try:
                worker()
            finally:
                self._tv_busy = False
        self.threaded(_w)

    def _tv_is_tcp(self):
        return bool(self.selected_serial) and ":" in self.selected_serial

    def _tv_wait_device(self, intentos=12, espera=1.0):
        for _ in range(intentos):
            if self._tv_is_tcp():
                self.run_adb(["connect", self.selected_serial],
                             target_device=False, timeout=10)
            code, out, _ = self.run_adb(["exec-out", "echo", "ping"], timeout=10)
            if code == 0 and "ping" in out:
                return True
            time.sleep(espera)
        return False

    def _tv_uid(self):
        _, out, _ = self.run_adb(["exec-out", "id", "-u"], timeout=15)
        return out.strip()

    def _tv_root(self):
        if self._tv_uid() == "0":
            return True
        self.log("  Elevando adbd a root...")
        self.run_adb(["root"], timeout=25)
        time.sleep(1.5)
        if not self._tv_wait_device():
            self.log("✗ El equipo no volvió a responder tras 'adb root'.")
            return False
        uid = self._tv_uid()
        if uid != "0":
            self.log(f"✗ No se obtuvo root (uid={uid or '?'}). La ROM no es "
                     "userdebug o ro.debuggable=0.")
            return False
        self.log("  ✓ root activo.")
        return True

    def _tv_unroot(self):
        self.log("  Devolviendo adbd a modo normal (unroot)...")
        self.run_adb(["unroot"], timeout=25)
        time.sleep(1.5)
        self._tv_wait_device()

    def _tv_cat(self, path):
        _, out, _ = self.run_adb(
            ["exec-out", "sh", "-c", f"cat {path} 2>/dev/null"], timeout=20)
        return out.strip()

    def _getprop(self, prop):
        _, out, _ = self.run_adb(["exec-out", "getprop", prop], timeout=15)
        return out.strip()

    def _tv_setting(self, ns, key):
        _, out, _ = self.run_adb(["exec-out", "settings", "get", ns, key], timeout=15)
        return out.strip()

    def _log_lines(self, text, prefix="  "):
        for line in (text or "").splitlines():
            if line.strip():
                self.log(prefix + line.strip())

    @staticmethod
    def _fmt_dur(segundos):
        s = abs(int(segundos))
        d, r = divmod(s, 86400)
        h, r = divmod(r, 3600)
        m, s = divmod(r, 60)
        partes = []
        if d:
            partes.append(f"{d}d")
        if h:
            partes.append(f"{h}h")
        if m:
            partes.append(f"{m}m")
        partes.append(f"{s}s")
        return " ".join(partes)

    def _tv_clock(self):
        _, fecha, _ = self.run_adb(["exec-out", "date"], timeout=15)
        _, epoch, _ = self.run_adb(["exec-out", "date", "+%s"], timeout=15)
        m = re.search(r"\d{6,}", epoch)
        if not m:
            return None, fecha.strip()
        return int(m.group(0)) - int(time.time()), fecha.strip()

    def _tv_clock_report(self, prefijo="  "):
        offset, fecha = self._tv_clock()
        self.log(f"{prefijo}Fecha del equipo : {fecha or '(sin respuesta)'}")
        self.log(f"{prefijo}Fecha de este PC : "
                 f"{datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y')}")
        if offset is None:
            self.log(f"{prefijo}⚠ No se pudo leer la hora del equipo.")
        elif abs(offset) > TVBOX_MAX_DESFASE:
            signo = "atrasado" if offset < 0 else "adelantado"
            self.log(f"{prefijo}✗ RELOJ DESFASADO: {self._fmt_dur(offset)} {signo}.")
            self.log(f"{prefijo}  Con este desfase ningún certificado TLS valida y la")
            self.log(f"{prefijo}  sincronización falla con 'Unacceptable certificate'.")
        else:
            self.log(f"{prefijo}✓ Reloj correcto (desfase {int(offset)} s).")
        return offset

    def action_tv_diagnose(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        cfg = self._tv_cfg()
        self._tv_start(lambda: self._tv_diagnose_worker(cfg))

    def _tv_diagnose_worker(self, cfg):
        self.log("──── Diagnóstico del TV Box ────")

        modelo = self._getprop("ro.product.model")
        hw = self._getprop("ro.hardware")
        rel = self._getprop("ro.build.version.release")
        sdk = self._getprop("ro.build.version.sdk")
        tipo = self._getprop("ro.build.type")
        dbg = self._getprop("ro.debuggable")
        self.log(f"  Modelo           : {modelo or '?'}  ({hw or '?'})")
        self.log(f"  Build            : {tipo or '?'}   ro.debuggable={dbg or '?'}")
        self.log(f"  Android declarado: {rel or '?'}   SDK real: {sdk or '?'}")
        esperado = SDK_A_ANDROID.get(sdk)
        if esperado and rel and not rel.startswith(esperado):
            self.log(f"  ⚠ La ROM dice Android {rel} pero el SDK {sdk} es Android "
                     f"{esperado}. No confíes en ro.build.version.release.")

        self._tv_clock_report()

        auto = self._tv_setting("global", "auto_time")
        ntp = self._tv_setting("global", "ntp_server")
        self.log(f"  auto_time        : {auto or '(vacío)'}")
        self.log(f"  ntp_server       : {ntp or '(vacío)'}")
        if ntp in ("", "null"):
            self.log("  ⚠ Sin servidor NTP: cae al de la ROM, que no responde. "
                     f"Déjalo en {cfg['ntp']}.")

        modo = self._tv_cat(SYS_DISPLAY_MODE)
        _, size, _ = self.run_adb(["exec-out", "wm", "size"], timeout=20)
        _, dens, _ = self.run_adb(["exec-out", "wm", "density"], timeout=20)
        self.log(f"  Salida HDMI      : {modo or '(no disponible)'}")
        self._log_lines(size, "  ")
        self._log_lines(dens, "  ")
        if modo.startswith("2160") and "1280x720" in size:
            self.log("  ⚠ Sale a 4K pero Android renderiza 720p y lo escala. "
                     "No es 4K real.")

        cap = self._tv_cat(SYS_DISP_CAP)
        modos = [l.strip().rstrip("*") for l in cap.splitlines() if l.strip()]
        if modos:
            self.log(f"  La TV acepta     : {', '.join(modos)}")
            self.after(0, lambda: self.tv_mode_menu.configure(values=modos))

        pkg = cfg["pkg"]
        _, ppath, _ = self.run_adb(["exec-out", "pm", "path", pkg], timeout=25)
        if "package:" not in ppath:
            self.log(f"  App {pkg}: NO instalada.")
        else:
            _, pid, _ = self.run_adb(["exec-out", "pidof", pkg], timeout=15)
            pid = pid.strip()
            self.log(f"  App {pkg}: instalada, "
                     f"{'corriendo (pid ' + pid.split()[0] + ')' if pid else 'DETENIDA'}")

        self.log(f"  Último arranque  : "
                 f"{self._getprop('sys.boot.reason') or '(desconocido)'}")
        up = self._tv_cat("/proc/uptime")
        try:
            self.log(f"  Encendido hace   : {self._fmt_dur(float(up.split()[0]))}")
        except (ValueError, IndexError):
            pass

        self._tv_log_check(pkg)
        self.log("──── Fin del diagnóstico ────")

    def _tv_log_check(self, pkg):
        _, out, _ = self.run_adb(["logcat", "-v", "time", "-t", "2000"], timeout=90)
        lineas = out.splitlines()
        tls = re.compile(r"unacceptable certificate|sslhandshake|certpath|"
                         r"dnstlssocket", re.I)
        hits = [l.strip() for l in lineas if tls.search(l)]
        if hits:
            self.log(f"  ✗ {len(hits)} error(es) de TLS en el logcat. Últimos:")
            for line in hits[-5:]:
                self.log("    " + line)
            if any("unacceptable certificate" in l.lower() for l in hits):
                self.log("    ⚠ Eso casi siempre es el reloj, no el certificado.")
        else:
            self.log("  ✓ Sin errores de certificado en el logcat reciente.")
        propias = [l.strip() for l in lineas
                   if re.search(r"sync|signage|MainActivity", l, re.I)]
        if propias:
            self.log(f"  Últimas líneas de {pkg}:")
            for line in propias[-5:]:
                self.log("    " + line)

    def action_tv_fix_clock(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        cfg = self._tv_cfg()
        if not messagebox.askyesno(
                "Solo fecha y hora",
                "Se pondrá la hora de este PC en el equipo y se escribirá el RTC de "
                "hardware (hwclock -w) para que sobreviva a los reinicios.\n\n"
                f"También se dejará el NTP en {cfg['ntp']} y la hora automática "
                "activada.\n\nRequiere 'adb root' (ROM userdebug). ¿Continuar?"):
            return
        self._tv_start(lambda: self._tv_fix_clock_worker(cfg, suelto=True))

    def _tv_fix_clock_worker(self, cfg, suelto=True):
        self.log("──── Fecha y hora ────")
        self._tv_clock_report()
        if not self._tv_root():
            return False
        utc = datetime.datetime.now(datetime.timezone.utc).strftime("%m%d%H%M%Y.%S")
        self.log(f"  Fijando hora UTC {utc} ...")
        self.run_adb(["shell", f"date -u {utc}"], timeout=25)
        self.log("  Escribiendo el RTC de hardware (hwclock -w)...")
        self.run_adb(["shell", "hwclock -w"], timeout=25)
        self.log(f"  Dejando ntp_server={cfg['ntp']} y auto_time=1 ...")
        self.run_adb(["shell", f"settings put global ntp_server {cfg['ntp']}"],
                     timeout=25)
        self.run_adb(["shell", "settings put global auto_time 1"], timeout=25)
        self.run_adb(["shell", "settings put global auto_time_zone 1"], timeout=25)
        if suelto:
            self._tv_unroot()
        offset = self._tv_clock_report()
        if offset is not None and abs(offset) <= TVBOX_MAX_DESFASE:
            self.log("✓ Reloj corregido. La sincronización debería levantar sola.")
        else:
            self.log("⚠ El reloj sigue desfasado: revisa el RTC de la caja.")
        return True

    def action_tv_video_profile(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        cfg = self._tv_cfg()
        aviso = ("\n\n⚠ Vas a saltarte la comprobación de compatibilidad: si la TV no "
                 "acepta ese modo, la pantalla puede quedarse en negro."
                 if cfg["forzar"] else "")
        if not messagebox.askyesno(
                "Solo resolución",
                f"Se aplicará:\n\n"
                f"  · Salida HDMI {cfg['modo']}\n"
                f"  · Framebuffer {cfg['size']}, densidad {cfg['dpi']}\n\n"
                f"La pantalla parpadeará.{aviso}\n\n¿Continuar?"):
            return

        def _w():
            self.log("──── Resolución ────")
            if self._tv_set_mode_worker(cfg):
                self._tv_set_fb_worker(cfg)
            self._tv_unroot()
        self._tv_start(_w)

    def _tv_set_mode_worker(self, cfg):
        modo = cfg["modo"]
        cap = self._tv_cat(SYS_DISP_CAP)
        soportado = bool(cap) and modo.lower() in cap.lower()
        if not soportado:
            if not cfg["forzar"]:
                self.log(f"✗ La TV no reporta {modo} como compatible; no se aplica")
                self.log("  (así no se queda la pantalla en negro). Si aun así lo")
                self.log("  quieres, marca la casilla de la tarjeta y repite.")
                return False
            self.log(f"⚠ La TV no reporta {modo}, pero se fuerza por petición expresa.")
            self.log("  Si la pantalla se queda en negro, vuelve a 2160p60hz a ciegas.")
        if not self._tv_root():
            return False
        self.log(f"  Fijando la salida HDMI en {modo} ...")
        self.run_adb(["shell", f"echo {modo} > {SYS_DISPLAY_MODE}"], timeout=25)
        self.run_adb(["shell", f"setprop ubootenv.var.outputmode {modo}"], timeout=25)
        self.run_adb(["shell", "setprop ubootenv.var.is.bestmode false"], timeout=25)
        time.sleep(3)
        self.log(f"  Salida ahora: {self._tv_cat(SYS_DISPLAY_MODE) or '?'}")
        self.log("  Nota: esto NO persiste al reinicio; la caja vuelve a 2160p60hz.")
        return True

    def _tv_set_fb_worker(self, cfg):
        self.log(f"  Fijando framebuffer {cfg['size']} (densidad {cfg['dpi']}) ...")
        self.run_adb(["shell", f"wm density {cfg['dpi']}"], timeout=30)
        time.sleep(2)
        self.run_adb(["shell", f"wm size {cfg['size']}"], timeout=30)
        time.sleep(3)
        _, s, _ = self.run_adb(["exec-out", "wm", "size"], timeout=20)
        _, d, _ = self.run_adb(["exec-out", "wm", "density"], timeout=20)
        self._log_lines(s, "  ")
        self._log_lines(d, "  ")
        self.log("  ✓ Framebuffer aplicado (esto sí persiste al reinicio).")
        return True

    def action_tv_restart_app(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        cfg = self._tv_cfg()
        self._tv_start(lambda: self._tv_restart_app_worker(cfg))

    def _tv_restart_app_worker(self, cfg):
        pkg = cfg["pkg"]
        self.log(f"  Reiniciando {pkg} ...")
        self.run_adb(["shell", f"am force-stop {pkg}"], timeout=30)
        time.sleep(1)
        self.run_adb(
            ["shell", f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1"],
            timeout=30)
        time.sleep(2)
        _, pid, _ = self.run_adb(["exec-out", "pidof", pkg], timeout=15)
        if pid.strip():
            self.log(f"  ✓ {pkg} corriendo (pid {pid.strip().split()[0]}).")
        else:
            self.log(f"  ⚠ {pkg} no aparece corriendo. ¿Está instalada?")

    def action_tv_full_fix(self):
        if not (self.ensure_adb() and self.ensure_device()):
            return
        cfg = self._tv_cfg()
        aviso = ("\n\n⚠ La comprobación de compatibilidad del modo está desactivada."
                 if cfg["forzar"] else "")
        if not messagebox.askyesno(
                "Fix completo",
                "Sobre el equipo seleccionado se aplicará:\n\n"
                "  1. La hora de este PC + RTC de hardware (hwclock -w)\n"
                f"  2. NTP {cfg['ntp']} y hora automática\n"
                f"  3. Salida HDMI {cfg['modo']}, framebuffer {cfg['size']} "
                f"y densidad {cfg['dpi']}\n"
                f"  4. Reinicio de {cfg['pkg']}\n\n"
                f"La pantalla parpadeará al cambiar el video.{aviso}\n\n¿Continuar?"):
            return
        self._tv_start(lambda: self._tv_full_fix_worker(cfg))

    def _tv_full_fix_worker(self, cfg):
        self.log("════════ FIX COMPLETO — TV Box ════════")
        self.log(f"  Video antes : {self._tv_cat(SYS_DISPLAY_MODE) or '(n/d)'}")

        if not self._tv_root():
            self.log("✗ Sin root no se puede fijar la hora. Fix abortado.")
            return

        self._tv_fix_clock_worker(cfg, suelto=False)

        self.log("──── Resolución ────")
        if self._tv_set_mode_worker(cfg):
            self._tv_set_fb_worker(cfg)

        self._tv_unroot()

        self.log("──── Aplicación ────")
        self._tv_restart_app_worker(cfg)

        self.log("──── Verificación ────")
        self._tv_clock_report()
        self.log(f"  Video ahora : {self._tv_cat(SYS_DISPLAY_MODE) or '(n/d)'}")
        _, s, _ = self.run_adb(["exec-out", "wm", "size"], timeout=20)
        _, d, _ = self.run_adb(["exec-out", "wm", "density"], timeout=20)
        self._log_lines(s, "  ")
        self._log_lines(d, "  ")
        self.log("════════ Fin ════════")

    def _ask_text(self, title, prompt, default=""):
        dlg = ctk.CTkInputDialog(text=prompt, title=title)
        try:
            entry = dlg._entry
            entry.insert(0, default)
        except Exception:
            pass
        val = dlg.get_input()
        return val.strip() if val else None

    def _package_picker(self, title, action_label, callback, danger=False):
        pkgs = self._get_packages(True)
        if not pkgs:
            self.log("No se encontraron apps de terceros.")
            return
        self.after(0, lambda: self._show_picker_window(
            title, action_label, callback, pkgs, danger))

    def _show_picker_window(self, title, action_label, callback, pkgs, danger):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("460x520")
        win.configure(fg_color=COLOR_BG)
        win.transient(self)
        self._cromo_windows(win)
        win.grab_set()
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(win, text=title, font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        search_var = tk.StringVar()
        search = ctk.CTkEntry(win, placeholder_text="Buscar paquete...",
                              textvariable=search_var)
        search.grid(row=1, column=0, sticky="ew", padx=16, pady=6)

        listframe = ctk.CTkScrollableFrame(win, fg_color=COLOR_CARD)
        listframe.grid(row=2, column=0, sticky="nsew", padx=16, pady=6)
        listframe.grid_columnconfigure(0, weight=1)

        selected = {"pkg": None}
        row_buttons = {}

        def pintar_fila(pk, b):
            activa = pk == selected["pkg"]
            b.configure(fg_color=COLOR_ACCENT if activa else "transparent",
                        hover_color=COLOR_ACCENT_HOVER if activa else COLOR_RAISED,
                        text_color="#ffffff" if activa else COLOR_TEXT)

        def render(filter_text=""):
            for b in row_buttons.values():
                b.destroy()
            row_buttons.clear()
            ft = filter_text.lower()
            for p in pkgs:
                if ft and ft not in p.lower():
                    continue
                b = ctk.CTkButton(
                    listframe, text=p, anchor="w", height=30,
                    command=lambda pk=p: choose(pk))
                b.grid(sticky="ew", pady=1)
                pintar_fila(p, b)
                row_buttons[p] = b

        def choose(pk):
            selected["pkg"] = pk
            for p, b in row_buttons.items():
                pintar_fila(p, b)
            sel_label.configure(text=f"Seleccionado: {pk}", text_color=COLOR_TEXT)
            accion.configure(state="normal", fg_color=color_accion,
                             hover_color=hover_accion)

        search_var.trace_add("write", lambda *a: render(search_var.get()))
        render()

        sel_label = ctk.CTkLabel(win, text="Seleccionado: (ninguno)",
                                 text_color=COLOR_MUTED)
        sel_label.grid(row=3, column=0, sticky="w", padx=16, pady=(4, 0))

        btnbar = ctk.CTkFrame(win, fg_color="transparent")
        btnbar.grid(row=4, column=0, sticky="ew", padx=16, pady=12)
        btnbar.grid_columnconfigure(0, weight=1)

        def confirm():
            pk = selected["pkg"]
            if not pk:
                return
            if danger and not messagebox.askyesno(
                    "Confirmar", f"¿{action_label} '{pk}'?", parent=win):
                return
            win.destroy()
            self.threaded(lambda: callback(pk))

        ctk.CTkButton(btnbar, text="Cancelar", command=win.destroy,
                      fg_color="transparent", border_width=1,
                      border_color=COLOR_BORDER, hover_color=COLOR_BISEL, width=110
                      ).grid(row=0, column=1, padx=6)
        color_accion = COLOR_RED if danger else COLOR_ACCENT
        hover_accion = COLOR_RED_HOVER if danger else COLOR_ACCENT_HOVER
        accion = ctk.CTkButton(btnbar, text=action_label, command=confirm,
                               width=140, state="disabled", fg_color=COLOR_BISEL,
                               text_color="#ffffff")
        accion.grid(row=0, column=2, padx=6)

if __name__ == "__main__":
    app = ADBToolbox()
    app.mainloop()
