import os
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import adb_toolbox as T

class Adb(object):

    def __init__(self, responder=None):
        self.comandos = []
        self._responder = responder

    def __call__(self, args, target_device=True, timeout=60, capture=True):
        self.comandos.append((list(args), target_device))
        respuesta = self._responder(list(args)) if self._responder else None
        return respuesta if respuesta else (0, "", "")

    def dichos(self):
        return [" ".join(c) for c, _ in self.comandos]

    def se_mando(self, texto):
        return any(texto in d for d in self.dichos())

    def limpiar(self):
        del self.comandos[:]

def crear_app(serial="ABC123456789"):
    T.CONFIG_DIR = tempfile.mkdtemp(prefix="adbtoolbox_test_")
    T.CONFIG_FILE = os.path.join(T.CONFIG_DIR, "config.json")
    T.ADBToolbox.prompt_configure_adb = lambda self: None
    T.ADBToolbox.refresh_devices = lambda self: None
    T.time.sleep = lambda s: None

    app = T.ADBToolbox()
    app.update()
    app.selected_serial = serial
    app.adb_path = "adb"
    app.salida = []
    app.log = lambda m: app.salida.append(m)
    app.threaded = lambda fn: fn()
    return app

def poner_adb(app, responder=None):
    doble = Adb(responder)
    app.run_adb = doble

    def transferencia(args, etiqueta, timeout=1800):
        doble.comandos.append((list(args), True))
        if args and args[0] == "pull" and len(args) > 2:
            with open(args[2], "wb") as f:
                f.write(b"contenido de prueba")
        return 0, "1 file pulled"
    app.run_adb_transfer = transferencia
    return doble

def esperar(app, ms=350):
    app.after(ms, app.quit)
    app.mainloop()
    app.update_idletasks()

class Resultado(object):

    def __init__(self, titulo):
        self.titulo = titulo
        self.fallos = []
        self.total = 0
        print("\n=== %s ===" % titulo)

    def check(self, condicion, mensaje):
        self.total += 1
        print(("   [OK]   " if condicion else "   [FALLA] ") + mensaje)
        if not condicion:
            self.fallos.append(mensaje)
        return bool(condicion)

    def resumen(self):
        print("   ----  %d comprobaciones, %d fallos" % (self.total, len(self.fallos)))
        return self.fallos
