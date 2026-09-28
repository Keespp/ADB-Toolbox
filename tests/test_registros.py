import os
import tempfile

from comun import Resultado, crear_app, poner_adb, esperar

LOGCAT = """09-04 11:00:01.100  1234  1234 I MiApp   : arrancando
09-04 11:00:02.200  5820  5830 D food    : cargando catalogo
09-04 11:00:03.300   932   960 I am_pss  : [5820,10111,com.keesp.food_webview,3089]
09-04 11:00:04.400  7777  7777 E OtraCosa: nada que ver
09-04 11:00:05.500  5820  5820 W food    : sin conexion
"""

class Equipo(object):

    def __init__(self):
        self.uid = "2000"

    def __call__(self, args):
        if args[:1] == ["root"]:
            self.uid = "0"
            return 0, "restarting adbd as root\n", ""
        if args[:1] == ["unroot"]:
            self.uid = "2000"
            return 0, "", ""
        if args[:1] == ["logcat"] or args[:2] == ["exec-out", "logcat"]:
            return 0, LOGCAT, ""
        if args == ["exec-out", "id", "-u"]:
            return 0, self.uid + "\n", ""
        if args == ["exec-out", "echo", "ping"]:
            return 0, "ping\n", ""
        if args[:2] == ["exec-out", "pidof"]:
            return (0, "5820\n", "") if args[2] == "com.keesp.food_webview" else (0, "", "")
        if args == ["exec-out", "getprop"]:
            return 0, "[ro.product.model]: [NEW9310]\n", ""
        if args[:2] == ["exec-out", "sh"]:
            if "wc -l" in args[3]:
                return 0, "17\n", ""
            if "wc -c" in args[3]:
                return 0, "11300000\n", ""
        return None

def correr():
    r = Resultado("Registros, mando y consola")
    app = crear_app()
    adb = poner_adb(app, Equipo())
    app.log_dir = tempfile.mkdtemp(prefix="adbtoolbox_logs_")

    app._do_log_app("com.keesp.food_webview")
    archivos = os.listdir(app.log_dir)
    r.check(len(archivos) == 1, "se guarda un archivo por extracción")
    contenido = open(os.path.join(app.log_dir, archivos[0]), encoding="utf-8").read()
    datos = [l for l in contenido.splitlines() if l and not l.startswith("#")]
    r.check(any("5820" in l and "food" in l for l in datos),
            "entran las líneas del proceso de la app")
    r.check(any("am_pss" in l for l in datos),
            "y las de OTRO proceso que nombra el paquete: ahí van los cierres")
    r.check(not any("OtraCosa" in l for l in datos), "y no se cuela nada ajeno")
    r.check("# Comando" in contenido and "# Filtrado" in contenido,
            "el archivo lleva cabecera que explica de dónde salió")

    del app.salida[:]
    adb.limpiar()
    app._do_log_app("com.que.no.existe")
    r.check(any("no está corriendo" in l for l in app.salida),
            "si la app no corre, se avisa de que sólo hay filtro por nombre")

    adb.limpiar()
    del app.salida[:]
    app._vendor_worker(7)
    dichos = adb.dichos()
    r.check(any("find /data/Syslog /sdcard/ylog" in d and "-mtime -7" in d
                for d in dichos),
            "se buscan sólo los archivos de los últimos días pedidos")
    r.check(any("tar -czf" in d for d in dichos),
            "se comprime DENTRO del equipo, no se arrastran cientos de MB sueltos")
    r.check(any(d.startswith("shell rm -f") for d in dichos),
            "y el temporal que se dejó en el equipo se borra")
    r.check(dichos.count("unroot") == 1, "adbd queda como estaba")

    adb.limpiar()
    del app.salida[:]
    app.remote_text.set("ClaveWiFi-2026")
    app.action_send_text()
    esperar(app, 150)
    r.check(adb.dichos() == ["shell input text 'ClaveWiFi-2026'"],
            "el texto va entrecomillado para el shell del equipo")
    r.check(not any("ClaveWiFi" in l for l in app.salida),
            "el texto NUNCA se escribe en la consola: puede ser una contraseña")
    r.check("14 caracteres" in app.remote_status.cget("text"),
            "sólo se informa de cuántos caracteres se enviaron")

    adb.limpiar()
    del app.salida[:]
    app.action_key(19, "arriba")
    r.check(adb.dichos() == ["shell input keyevent 19"], "las teclas van como keyevent")
    r.check(app.salida == [], "y no llenan la consola de ruido")

    for linea, esperado, target, nota in [
            ("shell getprop ro.serialno", ["shell", "getprop", "ro.serialno"], True,
             "parte la línea en argumentos"),
            ("adb shell ls /sdcard", ["shell", "ls", "/sdcard"], True,
             "quita el 'adb' que sobra al pegar una línea entera"),
            ("devices -l", ["devices", "-l"], False,
             "'devices' no se manda contra un dispositivo concreto"),
            ('shell "am start -n com.x/.Main"', ["shell", "am start -n com.x/.Main"],
             True, "respeta las comillas de un comando con espacios")]:
        adb.limpiar()
        app.cmd_var.set(linea)
        app.action_run_command()
        r.check(adb.comandos and adb.comandos[0][0] == esperado
                and adb.comandos[0][1] is target, nota)

    adb.limpiar()
    del app.salida[:]
    app.cmd_var.set('shell "sin cerrar')
    app.action_run_command()
    r.check(not adb.comandos and any("No entiendo" in l for l in app.salida),
            "una línea mal escrita no se ejecuta")

    app.destroy()
    return r.resumen()

if __name__ == "__main__":
    import sys
    sys.exit(1 if correr() else 0)
