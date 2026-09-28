import time as _t

from comun import Resultado, crear_app, poner_adb

EPOCH_2019 = 1577836320
DISP_CAP = "480p60hz\n720p60hz\n1080p60hz\n2160p60hz*\n"
PROPS = {
    "ro.product.model": "p291", "ro.hardware": "amlogic",
    "ro.build.version.release": "14.0", "ro.build.version.sdk": "28",
    "ro.build.type": "userdebug", "ro.debuggable": "1",
    "sys.boot.reason": "shutdown,userrequested",
}

class Caja(object):

    def __init__(self):
        self.epoch = EPOCH_2019
        self.uid = "2000"
        self.modo = "2160p60hz"
        self.size = "1280x720"
        self.densidad = "213"
        self.ajustes = {"auto_time": "1", "ntp_server": "null"}

    def __call__(self, args):
        a = list(args)
        if a[:1] == ["root"]:
            self.uid = "0"
            return 0, "restarting adbd as root\n", ""
        if a[:1] == ["unroot"]:
            self.uid = "2000"
            return 0, "", ""
        if a[:1] == ["logcat"]:
            return 0, ("08-20 15:00:01.000 W/MainActivity( 4653): Sync falló: "
                       "Unacceptable certificate\n"), ""
        if a[0] == "exec-out":
            resto = a[1:]
            if resto == ["echo", "ping"]:
                return 0, "ping\n", ""
            if resto == ["id", "-u"]:
                return 0, self.uid + "\n", ""
            if resto == ["date"]:
                return 0, _t.strftime("%a %b %d %H:%M:%S %Y",
                                      _t.localtime(self.epoch)) + "\n", ""
            if resto == ["date", "+%s"]:
                return 0, "%d\n" % self.epoch, ""
            if resto[:1] == ["getprop"]:
                return 0, PROPS.get(resto[1], "") + "\n", ""
            if resto[:2] == ["settings", "get"]:
                return 0, self.ajustes.get(resto[3], "null") + "\n", ""
            if resto[:2] == ["wm", "size"]:
                return 0, "Physical size: %s\n" % self.size, ""
            if resto[:2] == ["wm", "density"]:
                return 0, "Physical density: %s\n" % self.densidad, ""
            if resto[:1] == ["pm"]:
                return 0, "package:/data/app/base.apk\n", ""
            if resto[:1] == ["pidof"]:
                return 0, "4653\n", ""
            if resto[:2] == ["sh", "-c"]:
                orden = resto[2]
                if "disp_cap" in orden:
                    return 0, DISP_CAP, ""
                if "display/mode" in orden:
                    return 0, self.modo + "\n", ""
                if "uptime" in orden:
                    return 0, "812.30 3000.0\n", ""
        if a[0] == "shell":
            orden = a[1]
            if orden.startswith("date -u "):
                self.epoch = int(_t.time())
            elif orden.startswith("settings put global "):
                _, _, _, clave, valor = orden.split(" ", 4)
                self.ajustes[clave] = valor
            elif orden.startswith("echo ") and "display/mode" in orden:
                if self.uid != "0":
                    return 1, "", "Permission denied"
                self.modo = orden.split()[1]
            elif orden.startswith("wm size "):
                self.size = orden.split()[-1]
            elif orden.startswith("wm density "):
                self.densidad = orden.split()[-1]
        return None

def correr():
    r = Resultado("TV Box de señalización")
    app = crear_app(serial="192.168.1.50:5555")
    caja = Caja()
    adb = poner_adb(app, caja)
    cfg = app._tv_cfg()

    app._tv_diagnose_worker(cfg)
    diag = "\n".join(app.salida)
    r.check("RELOJ DESFASADO" in diag, "detecta el reloj desfasado")
    r.check("SDK 28 es Android 9" in diag,
            "avisa de que la ROM miente con la versión de Android")
    r.check("Sin servidor NTP" in diag, "avisa del ntp_server vacío")
    r.check("No es 4K real" in diag, "detecta el 4K falso (renderiza 720p)")
    r.check(all(c[0] in ("exec-out", "connect", "logcat") for c, _ in adb.comandos),
            "el diagnóstico no escribe nada en el equipo")

    del app.salida[:]
    app._tv_set_mode_worker({"modo": "1440p60hz", "forzar": False})
    r.check(caja.modo == "2160p60hz",
            "un modo que la TV no reporta en disp_cap NO se aplica")
    r.check("no reporta" in "\n".join(app.salida), "y se explica por qué")

    del app.salida[:]
    app._tv_set_mode_worker({"modo": "1440p60hz", "forzar": True})
    r.check(caja.modo == "1440p60hz", "con la casilla de forzar marcada sí se aplica")
    r.check("se fuerza" in "\n".join(app.salida), "avisando de que es bajo tu cuenta")
    caja.modo = "2160p60hz"
    app._tv_unroot()

    adb.limpiar()
    del app.salida[:]
    app._tv_full_fix_worker(cfg)
    dichos = adb.dichos()

    r.check(not any("reset" in d for d in dichos),
            "NUNCA se usa 'wm size reset' ni 'wm density reset': reinician la caja")
    fecha = [d for d in dichos if d.startswith("shell date -u ")]
    r.check(len(fecha) == 1 and len(fecha[0].split()[-1]) == 15
            and fecha[0].split()[-1][12] == ".",
            "la hora va en el formato de toybox MMDDhhmmAAAA.ss")
    r.check("shell hwclock -w" in dichos,
            "se escribe el RTC de hardware, que es lo que sobrevive al reinicio")
    r.check(dichos.index("root") < dichos.index("shell hwclock -w"),
            "se eleva a root antes de tocar el reloj")
    r.check("unroot" in dichos
            and dichos.index("unroot") > dichos.index("shell hwclock -w"),
            "y adbd vuelve a su estado normal al terminar")
    r.check(dichos.count("connect 192.168.1.50:5555") >= 2,
            "se reconecta por TCP tras cada root/unroot")
    orden_dens = next(i for i, d in enumerate(dichos) if d.startswith("shell wm density"))
    orden_size = next(i for i, d in enumerate(dichos) if d.startswith("shell wm size"))
    r.check(orden_dens < orden_size, "la densidad se aplica antes que el tamaño")
    r.check("shell am force-stop com.keesp.signage" in dichos,
            "y se reinicia la app de señalización")

    r.check(abs(caja.epoch - int(_t.time())) < 5, "el reloj queda en hora")
    r.check(caja.modo == "1080p60hz" and caja.size == "1920x1080"
            and caja.densidad == "320", "el video queda en 1080p60 con su framebuffer")
    r.check(caja.uid == "2000", "el equipo queda sin root")
    r.check(caja.ajustes["ntp_server"] == "time.google.com", "y con el NTP puesto")

    app.tv_mode_var.set("720p60hz")
    app.tv_dpi_var.set("213")
    app.tv_ntp_var.set("pool.ntp.org")
    otro = app._tv_cfg()
    r.check(otro["size"] == "1280x720", "720p implica framebuffer 1280x720")
    adb.limpiar()
    app._tv_full_fix_worker(otro)
    r.check(adb.se_mando("ntp_server pool.ntp.org"),
            "se usa el servidor NTP escrito en la tarjeta")
    r.check(adb.se_mando("wm density 213"), "y la densidad escrita en la tarjeta")
    app.tv_dpi_var.set("99999")
    r.check(app._tv_cfg()["dpi"] == "320", "una densidad absurda cae al valor por defecto")

    app.destroy()
    return r.resumen()

if __name__ == "__main__":
    import sys
    sys.exit(1 if correr() else 0)
