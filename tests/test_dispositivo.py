from comun import Resultado, crear_app, poner_adb, esperar, T

PROPS_POS = """[ro.product.model]: [NEW9310]
[ro.product.manufacturer]: [NEWPOS]
[ro.product.cpu.abi]: [armeabi-v7a]
[ro.build.version.release]: [10]
[ro.build.version.sdk]: [29]
[ro.build.display.id]: [sl8541e_Natv-userdebug 10 QP1A.190711.020 test-keys]
[ro.imagename]: [new9220-pro-normal-dev-10.00.33-fw.img]
[ro.serialno]: [15300000000042]
[persist.sys.serialno]: [9310000042]
[persist.sys.cid]: [0]
"""

BATERIA = """  present: true
  level: 72
  status: 2
  health: 2
  temperature: 312
"""

APPS = """PKG:com.keesp.signage
    versionCode=1 minSdk=21 targetSdk=34
    versionName=1.0.0
PKG:com.app.sinversion
    versionCode=7 minSdk=21 targetSdk=29
"""

def responder(args):
    if args == ["exec-out", "getprop"]:
        return 0, PROPS_POS, ""
    if args[:3] == ["exec-out", "dumpsys", "battery"]:
        return 0, BATERIA, ""
    if args[:2] == ["exec-out", "wm"]:
        return 0, ("Physical size: 720x1600\n" if args[2] == "size"
                   else "Physical density: 320\n"), ""
    if args[:2] == ["exec-out", "cat"] and "meminfo" in args[2]:
        return 0, "MemTotal:         968264 kB\nMemAvailable:     314572 kB\n", ""
    if args[:2] == ["exec-out", "ip"]:
        return (0, "    inet 192.168.1.50/24\n", "") if args[-1] == "wlan0" else (0, "", "")
    if args[:2] == ["exec-out", "sh"]:
        orden = args[3]
        if "df -h /data" in orden:
            return 0, "/dev/block/mmcblk0p42 4.9G 1.4G 3.4G 30% /data\n", ""
        if "/proc/uptime" in orden:
            return 0, "3725.4 100.0\n", ""
        if "pm list packages" in orden:
            return 0, APPS, ""
    return None

def correr():
    r = Resultado("Datos del dispositivo")
    app = crear_app(serial="15300000000042")
    adb = poner_adb(app, responder)

    app._info_worker()
    esperar(app)
    v = {c: e.get() for c, e in app.info_labels.items()}

    serie = app.info_labels["Serie"]
    r.check(serie.cget("state") == "readonly",
            "los valores son campos de sólo lectura, no etiquetas")
    serie._entry.insert(0, "zz")
    r.check(serie.get() == v["Serie"], "y no se pueden editar por descuido")
    serie._entry.selection_range(0, "end")
    r.check(serie._entry.selection_get() == v["Serie"],
            "el ratón selecciona el valor entero, listo para Ctrl+C")

    largo = "p291-userdebug 9 PPR1.180610.011 eng.compilador.20240101.120000"
    app._info_set("Compilación", largo)
    esperar(app, 100)
    r.check(app.info_labels["Compilación"].get() == largo,
            "un valor largo no se recorta: lo que se copia es el valor completo")
    app._info_set("Compilación", v["Compilación"])
    esperar(app, 100)

    portapapeles = []
    app.clipboard_clear = lambda: portapapeles.clear()
    app.clipboard_append = portapapeles.append
    app._info_copiar()
    copiado = "".join(portapapeles)
    r.check("Dispositivo\n" in copiado and "  Serie: 9310000042" in copiado
            and "  CID: 0" in copiado,
            "«Copiar» lleva toda la ficha, por tarjetas y campo a campo")

    r.check(v["Serie"] == "9310000042",
            "el serial es el de la etiqueta (persist.sys.serialno), no el del USB")
    r.check(v["CID"] == "0", "un CID de valor 0 se muestra: no es lo mismo que vacío")
    r.check(v["Compilación"] == "10.00.33",
            "el número de compilación sale de ro.imagename, no de display.id")
    r.check(v["SDK"] == "29   (Android 10)", "el SDK se traduce a versión de Android")
    r.check(v["Nivel"] == "72 %" and v["Estado"] == "cargando",
            "la batería se traduce a texto (status=2 -> cargando)")
    r.check(v["Temperatura"] == "31.2 °C", "la temperatura va en grados, no en décimas")
    r.check(v["/data"] == "3.4G libres de 4.9G   (30% usado)", "almacenamiento")
    r.check(v["RAM"] == "0.3 GB libres de 0.9 GB", "memoria")
    r.check(v["Encendido hace"] == "1h 2m 5s", "el uptime se lee en claro")
    r.check(v["Ethernet"] == "no conectado", "una interfaz sin IP lo dice")
    r.check(app.info_bars["/data"].get() == 0.30,
            "la barra de ocupación refleja el porcentaje real")
    r.check(app.info_bars["/data"].cget("progress_color") == T.COLOR_GREEN,
            "y al 30% se pinta en verde")
    r.check(sum(1 for c, _ in adb.comandos if c == ["exec-out", "getprop"]) == 1,
            "las propiedades se piden de una vez, no una por campo")
    r.check(all(c[0] == "exec-out" for c, _ in adb.comandos),
            "el panel sólo lee, no escribe nada en el equipo")

    for pct, color, nombre in ((0.50, T.COLOR_GREEN, "verde"),
                               (0.75, T.COLOR_AMBER, "ámbar"),
                               (0.95, T.COLOR_RED, "rojo")):
        app._info_bar("RAM", pct)
        esperar(app, 120)
        r.check(app.info_bars["RAM"].cget("progress_color") == color,
                "al %d%% la barra sale %s" % (pct * 100, nombre))
    app._info_bar("RAM", 5.0)
    esperar(app, 120)
    r.check(app.info_bars["RAM"].get() == 1.0, "un valor imposible se recorta")

    adb.limpiar()
    del app.salida[:]
    tabla = {}
    app.ventana_tabla = lambda titulo, cols, filas, anchos=None: tabla.update(
        {"titulo": titulo, "columnas": cols, "filas": filas})
    app.action_list_packages()
    esperar(app, 200)
    orden = adb.comandos[0][0][3]
    r.check(len(adb.comandos) == 1, "todas las versiones en una sola llamada a adb")
    r.check('"' not in orden and "'" not in orden,
            "la orden va sin comillas: así llega intacta desde Windows")
    r.check(tabla.get("columnas") == ["Paquete", "Versión", "Código"],
            "el listado sale en tabla ordenable, no volcado a la consola")
    r.check(("com.keesp.signage", "1.0.0", "1") in tabla.get("filas", []),
            "cada app sale con versionName y versionCode")
    r.check(("com.app.sinversion", "?", "7") in tabla.get("filas", []),
            "una app sin versionName no rompe el listado")

    app.destroy()
    return r.resumen()

if __name__ == "__main__":
    import sys
    sys.exit(1 if correr() else 0)
