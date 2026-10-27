import os
import re
import tempfile

from comun import Resultado, crear_app, poner_adb, esperar, T

PROPS = {
    "p291": {
        "ro.product.device": "p291", "ro.board.platform": "p291",
        "ro.build.version.sdk": "28", "ro.build.version.release": "14.0",
        "ro.product.model": "Google", "ro.product.manufacturer": "Amlogic",
        "ro.adb.secure": "0", "ro.serialno": "P291PRUEBA01", "sys.boot_completed": "1",
    },
    "rk322x_box": {
        "ro.product.device": "rk322x_box", "ro.board.platform": "rk322x",
        "ro.build.version.sdk": "25", "ro.build.version.release": "14",
        "ro.product.model": "Android", "ro.product.manufacturer": "rockchip",
        "ro.adb.secure": "0", "ro.serialno": "RK322XPRUEBA", "sys.boot_completed": "1",
    },
    "desconocida": {
        "ro.product.device": "x96max", "ro.board.platform": "g12a",
        "ro.build.version.sdk": "28", "ro.build.version.release": "9",
        "ro.product.model": "X96Max", "ro.product.manufacturer": "Amlogic",
        "ro.adb.secure": "1", "ro.serialno": "X96PRUEBA", "sys.boot_completed": "1",
    },
}
BASE = ("com.android.tv.settings", "com.android.vending", "com.google.android.gms",
        "com.android.webview", "com.google.android.webview", "com.android.chrome")
WEBVIEW = {"p291": "com.android.webview", "rk322x_box": "com.android.chrome",
           "desconocida": "com.android.webview"}
FALLBACK = ("com.android.tv.settings", ".system.FallbackHome", -1000)

class CajaTV(object):

    def __init__(self, modelo="p291"):
        self.props = dict(PROPS[modelo])
        perfil = T.PERFILES_TVBOX.get(modelo)
        self.instalados = set(BASE)
        self.home = [FALLBACK]
        if perfil:
            self.instalados |= set(T.ADBToolbox._prep_paquetes(perfil))
            self.instalados.add(perfil["explorador"])
            pkg, cls = perfil["lanzador_serie"].split("/")
            self.instalados.add(pkg)
            self.home.insert(0, (pkg, cls, 30 if modelo == "p291" else 0))
        else:
            self.instalados |= {"com.vendor.launcher", "com.vendor.store"}
            self.home.insert(0, ("com.vendor.launcher", ".Main", 0))
        self.sistema = set(self.instalados)
        self.terceros = set()
        self.desactivados = {"com.google.android.webview"}
        self.webview = WEBVIEW[modelo]
        self.preferido = None
        r = self.resolver()
        self.delante = "%s/%s" % (r[0], r[1])
        self.tv_input, self.ignora, self.reactiva, self.no_arranca = (
            set(), set(), set(), set())
        self.home_roto = False
        self.apagada = self.arrancando = 0
        self.subidos, self.apks, self.lanzados, self.tema = {}, {}, [], []
        self.al_desactivar = None

    def candidatos(self):
        return [h for h in self.home
                if h[0] in self.instalados and h[0] not in self.desactivados]

    def resolver(self):
        cands = self.candidatos()
        if not cands:
            return None
        tope = max(h[2] for h in cands)
        mejores = [h for h in cands if h[2] == tope]
        if len(mejores) == 1:
            return mejores[0]
        elegido = [h for h in mejores if self.preferido == "%s/%s" % (h[0], h[1])]
        return elegido[0] if elegido else ("android",
                                           "com.android.internal.app.ResolverActivity", 0)

    def reiniciar(self):
        self.apagada, self.arrancando = 1, 2
        self.desactivados -= self.reactiva
        r = self.resolver()
        self.delante = "%s/%s" % (r[0], r[1]) if r else ""

    def __call__(self, args):
        a = list(args)
        if a[0] == "connect":
            return 0, "connected to %s\n" % a[1], ""
        if a[0] == "disconnect":
            return 0, "disconnected %s\n" % a[1], ""
        if a[0] == "reboot":
            self.reiniciar()
            return 0, "", ""
        if a[0] == "exec-out":
            if self.apagada:
                self.apagada -= 1
                return 1, "", "error: device offline"
            return self.leer(a[1:])
        if a[0] == "shell":
            return self.orden(a[1])
        return None

    def lista(self, filtros):
        if "-d" in filtros:
            nombres = self.desactivados & self.instalados
        elif "-e" in filtros:
            nombres = self.instalados - self.desactivados
        elif "-s" in filtros:
            nombres = self.sistema & self.instalados
        elif "-3" in filtros:
            nombres = self.terceros & self.instalados
        else:
            nombres = self.instalados
        if "-f" in filtros:
            return "".join("package:/system/app/%s/base.apk=%s  installer=null\n" % (p, p)
                           for p in sorted(nombres))
        return "".join("package:%s\n" % p for p in sorted(nombres))

    def leer(self, r):
        if r == ["echo", "ping"]:
            return 0, "ping\n", ""
        if r == ["getprop"]:
            return 0, "".join("[%s]: [%s]\n" % kv for kv in sorted(self.props.items())), ""
        if r[:1] == ["getprop"]:
            if r[1] == "sys.boot_completed" and self.arrancando:
                self.arrancando -= 1
                return 0, "0\n", ""
            return 0, self.props.get(r[1], "") + "\n", ""
        if r[:3] == ["pm", "list", "packages"]:
            return 0, self.lista(r[3:]), ""
        if r[:2] == ["settings", "list"]:
            return 0, "ajuste_%s=1\n" % r[2], ""
        if r[:3] == ["cmd", "package", "resolve-activity"]:
            h = self.resolver()
            if not h:
                return 0, "No activity found\n", ""
            return 0, "priority=%d preferredOrder=0\n%s/%s\n" % (h[2], h[0], h[1]), ""
        if r[:3] == ["cmd", "package", "query-activities"]:
            cands = self.candidatos()
            texto = "%d activities found:\n" % len(cands)
            for i, h in enumerate(cands):
                texto += "  Activity #%d:\n    priority=%d\n    %s/%s\n" % (i, h[2], h[0], h[1])
            return 0, texto, ""
        if r == ["wm", "size"]:
            return 0, "Physical size: 1280x720\n", ""
        if r == ["wm", "density"]:
            return 0, "Physical density: 240\n", ""
        if r == ["ls", "-l", "/system/xbin/su"]:
            return 0, "-rwsr-sr-x 1 root shell 75364 2019-01-01 00:00 /system/xbin/su\n", ""
        if r[:2] == ["dumpsys", "package"]:
            permiso = ("android.permission.TV_INPUT_HARDWARE" if r[2] in self.tv_input
                       else "android.permission.INTERNET")
            return 0, ("  declared permissions:\n    %s.TV_INPUT_HARDWARE_PROPIO\n"
                       "  requested permissions:\n    %s\n"
                       "  install permissions:\n    android.permission.TV_INPUT_HARDWARE: "
                       "granted=false\n" % (r[2], permiso)), ""
        if r == ["dumpsys", "webviewupdate"]:
            if int(self.props["ro.build.version.sdk"]) < 26:
                return 0, "", ""
            return 0, ("Current WebView package (name, version): (%s, 68.0.3440.91)\n"
                       % self.webview), ""
        if r == ["sh", "-c", T.PREP_RESUMIDA]:
            return 0, "    mResumedActivity: ActivityRecord{1a2b3c u0 %s t7}\n" % self.delante, ""
        return None

    def orden(self, texto):
        m = re.fullmatch(r"pm disable-user --user 0 (\S+)", texto)
        if m:
            if self.al_desactivar:
                self.al_desactivar(m.group(1))
            if m.group(1) not in self.ignora:
                self.desactivados.add(m.group(1))
            return 0, "Package %s new state: disabled-user\n" % m.group(1), ""
        m = re.fullmatch(r"pm enable (\S+)", texto)
        if m:
            self.desactivados.discard(m.group(1))
            return 0, "Package %s new state: enabled\n" % m.group(1), ""
        m = re.fullmatch(r"cmd package set-home-activity --user 0 (\S+)", texto)
        if m:
            self.preferido = m.group(1)
            return 0, "Success\n", ""
        m = re.fullmatch(r"am start -W -n (\S+)", texto)
        if m:
            pkg = m.group(1).split("/")[0]
            self.lanzados.append(pkg)
            if (pkg in self.instalados and pkg not in self.desactivados
                    and pkg not in self.no_arranca):
                self.delante = m.group(1)
                return 0, "Starting: Intent { cmp=%s }\nStatus: ok\n" % m.group(1), ""
            return 0, "Error: Activity class {%s} does not exist.\n" % m.group(1), ""
        if texto == "input keyevent 3":
            h = self.resolver()
            if self.home_roto:
                self.delante = "%s/%s" % FALLBACK[:2]
            elif h:
                self.delante = "%s/%s" % (h[0], h[1])
            return 0, "", ""
        m = re.fullmatch(r"pm install -r (\S+)", texto)
        if m:
            info = self.apks.get(self.subidos.get(m.group(1)))
            if not info:
                return 0, "Failure [INSTALL_FAILED_INVALID_APK]\n", ""
            pkg, cls = info
            self.instalados.add(pkg)
            self.terceros.add(pkg)
            if cls and not any(h[0] == pkg for h in self.home):
                self.home.insert(0, (pkg, cls, 0))
            return 0, "Success\n", ""
        if "gathin" in texto or "fondo" in texto or "theme" in texto:
            self.tema.append(texto)
        return None

def poner_caja(app, caja, todos):
    doble = poner_adb(app, caja)

    def transferencia(args, etiqueta, timeout=1800):
        doble.comandos.append((list(args), True))
        if args[0] == "push":
            caja.subidos[args[2]] = args[1]
        return 0, "1 file pushed"
    app.run_adb_transfer = transferencia
    todos.append(doble)
    return doble

def archivo(carpeta, nombre, datos):
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, "wb") as f:
        f.write(datos)
    return ruta

def ventanas(app):
    return [w for w in app.winfo_children() if isinstance(w, T.ctk.CTkToplevel)]

def pm_suelto(dicho):
    orden = dicho[len("shell "):]
    return (len(re.findall(r"(^|\s)pm\s", orden)) == 1
            and not any(s in orden for s in (";", "&&", "|")))

def correr():
    r = Resultado("Preparar TV Box")
    originales = (T.messagebox.askyesno, T.messagebox.askyesnocancel,
                  T.messagebox.showinfo, T.filedialog.askopenfilename,
                  T.filedialog.askdirectory, T.socket.create_connection,
                  T.PREP_FLAUNCHER_SHA256)
    try:
        _correr(r)
    finally:
        (T.messagebox.askyesno, T.messagebox.askyesnocancel, T.messagebox.showinfo,
         T.filedialog.askopenfilename, T.filedialog.askdirectory,
         T.socket.create_connection, T.PREP_FLAUNCHER_SHA256) = originales
    return r.resumen()

def _correr(r):
    preguntas = []

    def si(*a, **k):
        preguntas.append(a[0] if a else "")
        return True
    T.messagebox.askyesno = si
    T.messagebox.askyesnocancel = si
    T.messagebox.showinfo = lambda *a, **k: None

    disco = tempfile.mkdtemp(prefix="adbtoolbox_prep_")
    apk_tvhome = archivo(disco, "tvhome.apk", b"tvhome")
    apk_flauncher = archivo(disco, "flauncher-0.18.0.apk", b"flauncher")
    apk_senal = archivo(disco, "senal.apk", b"senal")
    apk_otro = archivo(disco, "otro.apk", b"otro")
    tema = os.path.join(disco, "tema")
    os.makedirs(tema)
    archivo(tema, "config.json", b'{"columns": 4, "wallpaper": true}')
    archivo(tema, "wallpaper.jpg", b"\xff\xd8jpeg")
    APKS = {apk_tvhome: ("com.gathin.tvhome", ".MainActivity"),
            apk_flauncher: ("me.efesser.flauncher", ".MainActivity"),
            apk_senal: ("com.ejemplo.signage", None),
            apk_otro: ("com.otra.app", None)}

    app = crear_app(serial="192.168.1.50:5555")
    app.prep_dir = tempfile.mkdtemp(prefix="adbtoolbox_copias_")
    todos = []
    esperar(app)

    lateral = app.sidebar._parent_canvas
    r.check("Preparar TV Box" in app.pages and "Preparar TV Box" in app.nav_buttons,
            "la sección Preparar TV Box está en la barra, en el grupo Sistema")
    r.check(lateral.bbox("all")[3] <= lateral.winfo_height(),
            "con la sección nueva la barra lateral sigue cabiendo entera a 940x760")

    perfil = T.PERFILES_TVBOX["p291"]
    caja = CajaTV("p291")
    caja.apks.update(APKS)
    adb = poner_caja(app, caja, todos)
    caja_p291 = caja

    app._prep_identificar_worker()
    esperar(app, 150)
    log = "\n".join(app.salida)
    r.check(app._prep["perfil"] == "p291", "una p291 con SDK 28 usa el perfil p291")
    r.check("La ROM miente" in log and "Android 9" in log,
            "avisa de que la ROM dice Android 14 pero el SDK 28 es Android 9")
    r.check("ro.adb.secure=0" in log and "setuid" in log,
            "avisa de ro.adb.secure=0 y del su setuid")
    r.check("Amlogic p291" in app.prep_equipo.cget("text"),
            "la tarjeta enseña el equipo y su perfil")
    r.check(all(c[0] == "exec-out" for c, _ in adb.comandos),
            "identificar sólo lee del equipo")

    adb.limpiar()
    del app.salida[:]
    r.check(app._prep_ui_desactivar(False) is False and not adb.comandos,
            "sin copia de seguridad no se desactiva nada")
    r.check(any("copia de seguridad" in m for m in app.salida), "y se dice por qué")

    caja.desactivados.add("com.android.printspooler")
    caja.instalados.discard("com.netflix.mediaclient")
    caja.tv_input.add("com.droidlogic.videoplayer")
    adb.limpiar()
    app._prep_copia_worker()
    carpeta = app._prep["carpeta"]
    r.check(os.path.dirname(carpeta) == os.path.join(app.prep_dir, "p291_P291PRUEBA01"),
            "la copia va a una carpeta por equipo (modelo y serie) y fecha")
    r.check(all(os.path.isfile(os.path.join(carpeta, n)) for n, _ in T.PREP_COPIA)
            and os.path.isfile(os.path.join(carpeta, "equipo.txt")),
            "guarda paquetes, getprop, ajustes, Home, pantalla y la ficha del equipo")
    r.check(adb.se_mando("exec-out pm list packages -f -u -i")
            and adb.se_mando("exec-out cmd package query-activities --brief")
            and adb.se_mando("exec-out settings list secure"),
            "con los comandos que se pidieron (-f -u -i, query-activities, settings)")
    r.check(all(c[0] == "exec-out" for c, _ in adb.comandos),
            "la copia sólo lee del equipo")
    ficha = open(os.path.join(carpeta, "equipo.txt"), encoding="utf-8").read()
    r.check("perfil: p291" in ficha and "home: com.droidlogic.mboxlauncher/.Launcher" in ficha,
            "y apunta el perfil y el Home de serie para poder restaurar")

    aplicada = os.path.join(carpeta, "lista-aplicada.txt")
    antes = {}
    caja.al_desactivar = lambda p: antes.setdefault("existia", os.path.isfile(aplicada))
    caja.ignora.add("com.abc.ninja")
    adb.limpiar()
    del app.salida[:]
    ok = app._prep_desactivar_worker(perfil["lotes"])
    log = "\n".join(app.salida)
    r.check(not ok and "com.abc.ninja no sale en «pm list packages -d»" in log,
            "se comprueba con «pm list packages -d», no con el código de salida")
    r.check(antes.get("existia") is True,
            "lo que se va a desactivar queda apuntado ANTES del primer pm")
    caja.ignora.clear()
    adb.limpiar()
    del app.salida[:]
    ok = app._prep_desactivar_worker(perfil["lotes"])
    dichos = adb.dichos()
    pm = [d for d in dichos if d.startswith("shell pm ")]
    r.check(ok and "com.abc.ninja" in caja.desactivados,
            "al repetir sale bien y ya está todo desactivado")
    r.check(pm and all(pm_suelto(d) for d in pm), "un solo comando pm por llamada")
    r.check(dichos and dichos[-1] == "exec-out pm list packages -d",
            "y lo último es comprobar la lista de desactivados")
    lista = T.ADBToolbox._prep_leer_paquetes(aplicada)
    r.check("com.android.printspooler" not in lista,
            "lo que ya venía desactivado no se apunta: restaurar no lo toca")
    r.check("com.droidlogic.videoplayer" not in caja.desactivados
            and "TV_INPUT_HARDWARE" in "\n".join(app.salida) + log,
            "se salta lo que pide TV_INPUT_HARDWARE (las entradas HDMI)")
    r.check("com.droidlogic.mboxlauncher" not in caja.desactivados,
            "el lanzador de serie no se toca en el paso 3")
    r.check("com.ftest" in caja.desactivados and "com.ftest" not in caja.lanzados,
            "el test de fábrica se desactiva, nunca se arranca")
    esperados = set(T.ADBToolbox._prep_paquetes(perfil)) - {
        "com.netflix.mediaclient", "com.droidlogic.videoplayer"}
    r.check(esperados <= caja.desactivados, "el resto del perfil queda desactivado")
    r.check("com.android.chrome" in caja_p291.desactivados,
            "en la p291, que sí dice su WebView (com.android.webview), Chrome se desactiva")

    adb.limpiar()
    del app.salida[:]
    ok = app._prep_desactivar_worker((("x", ("com.charon.rocketfly",
                                              "com.android.systemui")),))
    r.check(not ok and not adb.comandos and "núcleo" in "\n".join(app.salida),
            "una lista con un paquete de núcleo se rechaza entera, sin tocar nada")
    ok = app._prep_desactivar_worker((("x", ("com.x;reboot",)),))
    r.check(not ok and not adb.comandos, "y una con algo que no es un paquete, igual")
    nucleo = ("android", "com.android.systemui", "com.android.shell", "com.android.phone",
              "com.android.settings", "com.android.tv.settings",
              "com.android.permissioncontroller", "com.google.android.permissioncontroller",
              "com.android.packageinstaller", "com.google.android.packageinstaller",
              "com.google.android.ext.services", "com.android.ext.shared",
              "com.google.android.modulemetadata",
              "com.google.android.overlay.modules.ext.services",
              "com.android.providers.media", "com.android.providers.settings")
    libres = ("com.android.providers.calendar", "com.android.providers.contacts",
              "com.android.providers.userdictionary", "com.android.providers.blockednumber",
              "com.android.settings.intelligence", "com.android.chrome")
    r.check(all(T.ADBToolbox._prep_es_nucleo(p) for p in nucleo)
            and not any(T.ADBToolbox._prep_es_nucleo(p) for p in libres),
            "la lista negra es la de disable.ps1 (providers de calendario y contactos aparte)")

    adb.limpiar()
    del app.salida[:]
    app._prep_desactivar_worker((("x", ("com.droidlogic.mboxlauncher",)),))
    r.check("com.droidlogic.mboxlauncher" not in caja.desactivados
            and "dueño de Home" in "\n".join(app.salida),
            "el dueño de Home no se desactiva si nadie más responde a HOME")

    adb.limpiar()
    del app.salida[:]
    ok = app._prep_lanzador_worker(apk_tvhome, T.PREP_TVHOME, perfil, tema)
    dichos = adb.dichos()
    log = "\n".join(app.salida)
    r.check(ok, "Android 9: el lanzador nuevo se instala y queda como Home")
    r.check(not any(c[0] == "install" for c, _ in adb.comandos)
            and "shell pm install -r /data/local/tmp/adbtoolbox-lanzador.apk" in dichos,
            "se instala con push + pm install -r, nunca con «adb install»")
    r.check("shell cmd package set-home-activity --user 0 com.gathin.tvhome/.MainActivity"
            in dichos, "set-home-activity --user 0 al lanzador nuevo")
    posicion = lambda d: dichos.index(d) if d in dichos else -1
    i_start = posicion("shell am start -W -n com.gathin.tvhome/.MainActivity")
    i_off = posicion("shell pm disable-user --user 0 com.droidlogic.mboxlauncher")
    r.check(0 <= i_start < i_off,
            "se arranca con am start -W ANTES de desactivar el de serie")
    r.check("Home sigue en com.droidlogic.mboxlauncher" in log,
            "explica que en la p291 set-home-activity no le gana a la prioridad 30")
    r.check(posicion("shell input keyevent 3") > i_off >= 0
            and caja.delante.startswith("com.gathin.tvhome/"),
            "tras desactivarlo se pulsa HOME y sale el nuevo (mResumedActivity)")
    r.check("com.droidlogic.mboxlauncher" in T.ADBToolbox._prep_leer_paquetes(aplicada),
            "el lanzador de serie también queda apuntado para restaurar")
    r.check(adb.se_mando("push %s /data/local/tmp/adbtoolbox-tema-config.json"
                         % os.path.join(tema, "config.json"))
            and adb.se_mando("adbtoolbox-tema-wallpaper.jpg")
            and adb.se_mando("content write --uri content://com.gathin.tvhome.theme/config.json")
            and adb.se_mando("|| cp /data/local/tmp/adbtoolbox-tema-config.json"),
            "el tema sube como theme.ps1: content write y, si no hay, cp")
    r.check(adb.se_mando("am force-stop com.gathin.tvhome"),
            "y se reinicia el lanzador para que lo lea")

    caja.desactivados.add("com.droidlogic.FileBrower")
    adb.limpiar()
    del app.salida[:]
    ok = app._prep_senal_worker(apk_senal, perfil)
    dichos = adb.dichos()
    r.check(ok and "shell pm install -r /data/local/tmp/adbtoolbox-senal.apk" in dichos,
            "la app de señalización se instala con push + pm install -r")
    r.check("shell pm enable com.droidlogic.FileBrower" in dichos
            and "com.droidlogic.FileBrower" not in caja.desactivados,
            "y en la p291 se reactiva el explorador nativo")
    r.check(any("com.ejemplo.signage" in m for m in app.salida),
            "dice qué paquete se instaló")

    adb.limpiar()
    del app.salida[:]
    ok = app._prep_reinicio_worker()
    dichos = adb.dichos()
    r.check(ok and "reboot" in dichos, "reinicia y todo sigue en su sitio")
    r.check(dichos.count("exec-out getprop sys.boot_completed") >= 3
            and "connect 192.168.1.50:5555" in dichos,
            "espera a sys.boot_completed reconectando por TCP")
    r.check(any("siguen desactivados" in m for m in app.salida)
            and any("Home sigue siendo com.gathin.tvhome" in m for m in app.salida),
            "compara los desactivados con la lista aplicada y que Home sigue siendo el nuevo")
    caja.reactiva.add("com.google.android.youtube.tv")
    del app.salida[:]
    ok = app._prep_reinicio_worker()
    r.check(not ok and any("reactivó" in m and "youtube.tv" in m for m in app.salida),
            "si el firmware reactiva algo al arrancar, se dice cuál")

    adb.limpiar()
    paquetes, home, problema = app._prep_leer_copia(carpeta)
    r.check(not problema and home == "com.droidlogic.mboxlauncher/.Launcher",
            "restaurar devuelve Home al lanzador de serie de la copia")
    app._prep_restaurar_worker(paquetes, home)
    dichos = adb.dichos()
    r.check(not (set(paquetes) & caja.desactivados)
            and "com.android.printspooler" in caja.desactivados,
            "reactiva lo de la lista y deja como estaba lo que ya venía desactivado")
    r.check(all(pm_suelto(d) for d in dichos if d.startswith("shell pm "))
            and "shell cmd package set-home-activity --user 0 "
                "com.droidlogic.mboxlauncher/.Launcher" in dichos,
            "pm enable uno por llamada y set-home-activity al de serie")
    mala = tempfile.mkdtemp(prefix="adbtoolbox_mala_")
    archivo(mala, "lista-aplicada.txt", b"com.charon.rocketfly\ncom.x;reboot\n")
    adb.limpiar()
    r.check(app._prep_leer_copia(mala)[2] and not adb.comandos,
            "una lista aplicada con algo que no es un paquete se rechaza")

    caja = CajaTV("p291")
    caja.apks.update(APKS)
    adb = poner_caja(app, caja, todos)
    del app.salida[:]
    ok = app._prep_lanzador_worker(apk_otro, T.PREP_TVHOME, perfil, "")
    r.check(not ok and "com.droidlogic.mboxlauncher" not in caja.desactivados
            and not adb.se_mando("set-home-activity"),
            "si el APK no es el lanzador, no se toca el Home")
    caja.no_arranca.add("com.gathin.tvhome")
    ok = app._prep_lanzador_worker(apk_tvhome, T.PREP_TVHOME, perfil, "")
    r.check(not ok and "com.droidlogic.mboxlauncher" not in caja.desactivados,
            "si el nuevo no llega a primer plano, el de serie sigue activo")
    caja.no_arranca.clear()
    caja.home_roto = True
    adb.limpiar()
    ok = app._prep_lanzador_worker(apk_tvhome, T.PREP_TVHOME, perfil, "")
    r.check(not ok and adb.se_mando("shell pm enable com.droidlogic.mboxlauncher")
            and "com.droidlogic.mboxlauncher" not in caja.desactivados,
            "si tras HOME no sale el nuevo, se reactiva el de serie")
    adb.limpiar()
    r.check(app._prep_abrir("com.ftest/.MainActivity") is False and not adb.comandos,
            "un paquete de fábrica no se arranca nunca")

    def cerrado(*a, **k):
        raise ConnectionRefusedError()

    class Abierto(object):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    T.socket.create_connection = cerrado
    adb.limpiar()
    del app.salida[:]
    r.check(app._prep_cierre_worker("192.168.1.50")
            and any("rechaza la conexión" in m for m in app.salida),
            "ConnectionRefused en el 5555 = ADB cerrado")
    r.check(adb.dichos()[:1] == ["disconnect 192.168.1.50:5555"],
            "antes se suelta la conexión propia (la RK322x sólo admite una)")
    T.socket.create_connection = lambda *a, **k: Abierto()
    del app.salida[:]
    r.check(not app._prep_cierre_worker("192.168.1.50")
            and any("sigue abierto" in m for m in app.salida),
            "si el puerto acepta, avisa de que ADB sigue abierto")

    app.selected_serial = "192.168.1.51:5555"
    rk = T.PERFILES_TVBOX["rk322x_box"]
    caja = CajaTV("rk322x_box")
    caja.apks.update(APKS)
    adb = poner_caja(app, caja, todos)
    app.cfg.update({"tvprep_flauncher": apk_flauncher, "tvprep_tvhome": apk_tvhome,
                    "tvprep_tema": tema, "tvprep_senal": apk_senal})
    del app.salida[:]
    app._prep_identificar_worker()
    app._prep_copia_worker()
    r.check(app._prep["perfil"] == "rk322x_box" and app._prep["sdk"] == 25,
            "una RK322x con SDK 25 usa su perfil")
    adb.limpiar()
    del app.salida[:]
    app._prep_desactivar_worker((("x", ("com.android.chrome", "com.svox.pico")),))
    r.check("com.android.chrome" not in caja.desactivados
            and "com.svox.pico" in caja.desactivados
            and any("proveedor de WebView" in m for m in app.salida),
            "en la RK322x Chrome es el WebView y no se desactiva, aunque Android 7.1 "
            "no lo diga en dumpsys webviewupdate")
    trabajo = app._prep_ui_lanzador(False)
    adb.limpiar()
    antes_ventanas = len(ventanas(app))
    ok = trabajo()
    esperar(app, 200)
    dichos = adb.dichos()
    r.check(ok and "shell cmd package set-home-activity --user 0 "
                   "me.efesser.flauncher/.MainActivity" in dichos,
            "SDK 25: se usa FLauncher, no el lanzador del repo")
    r.check(adb.se_mando("push %s " % apk_flauncher) and not adb.se_mando(apk_tvhome),
            "y el APK de tvhome ni se sube")
    r.check("com.ik.MXQ_Stick_MINI_8K" in caja.desactivados
            and caja.resolver()[0] == "me.efesser.flauncher",
            "el de serie se desactiva y Home queda en FLauncher")
    r.check(adb.se_mando("push %s %s" % (os.path.join(tema, "wallpaper.jpg"),
                                         T.PREP_FONDO_FLAUNCHER))
            and not adb.se_mando("content write"),
            "el fondo se deja en Pictures para elegirlo con el mando")
    guias = [w for w in ventanas(app)[antes_ventanas:]
             if w.title() == "FLauncher: pasos con el mando"]
    r.check(guias, "y se abre la guía de lo que sólo se hace con el mando")
    for w in guias:
        w.destroy()
    adb.limpiar()
    app._prep_senal_worker(apk_senal, rk)
    r.check(not adb.se_mando("pm enable com.android.rockchip"),
            "en la RK322x el explorador ya está activo y no se toca")

    huella = T.ADBToolbox._prep_sha256(apk_flauncher)
    T.filedialog.askopenfilename = lambda *a, **k: apk_otro
    T.messagebox.askyesno = lambda *a, **k: preguntas.append("sha") or False
    del preguntas[:]
    r.check(app._prep_elegir("tvprep_flauncher") is None and preguntas == ["sha"]
            and app.cfg["tvprep_flauncher"] == apk_flauncher,
            "un FLauncher con otro SHA-256 pide confirmación y, si no, se descarta")
    T.PREP_FLAUNCHER_SHA256 = huella
    T.filedialog.askopenfilename = lambda *a, **k: apk_flauncher
    del preguntas[:]
    r.check(app._prep_elegir("tvprep_flauncher") == apk_flauncher and not preguntas,
            "con el SHA-256 publicado se acepta sin preguntar")
    T.messagebox.askyesno = si

    app.selected_serial = "192.168.1.52:5555"
    caja = CajaTV("desconocida")
    adb = poner_caja(app, caja, todos)
    tabla = {}
    app.ventana_tabla = lambda titulo, cols, filas, anchos=None: tabla.update(
        {"titulo": titulo, "filas": filas})
    del app.salida[:]
    app.action_prep_asistente()
    for _ in range(4):
        esperar(app, 150)
    log = "\n".join(app.salida)
    r.check(app._prep["perfil"] is None and "sin perfil probado" in log,
            "un modelo desconocido no tiene perfil")
    r.check(not adb.se_mando("disable-user") and not adb.se_mando("pm install"),
            "y el asistente sólo hace inventario y copia: no desactiva ni instala")
    r.check(tabla.get("titulo") == "Inventario de paquetes"
            and ("com.vendor.store", "activo", "sistema", "") in tabla.get("filas", []),
            "el inventario sale en tabla")
    r.check("Asistente detenido" in log, "y el asistente se para ahí")

    caja = CajaTV("desconocida")
    caja.props.update(PROPS["p291"])
    caja.props["ro.build.version.sdk"] = "30"
    poner_caja(app, caja, todos)
    del app.salida[:]
    app._prep_identificar_worker()
    r.check(app._prep["perfil"] is None
            and any("Parece una Amlogic p291" in m for m in app.salida),
            "una p291 con otro SDK no usa el perfil: manda el SDK")

    app.selected_serial = "192.168.1.53:5555"
    T.socket.create_connection = cerrado
    caja = CajaTV("p291")
    caja.apks.update(APKS)
    adb = poner_caja(app, caja, todos)
    del app.salida[:]
    del preguntas[:]
    app.action_prep_asistente()
    for _ in range(8):
        esperar(app, 150)
        if any("Asistente terminado" in m for m in app.salida):
            break
    log = "\n".join(app.salida)
    marcas = [log.find("──── %s ────" % T.PREP_TITULOS[p]) for p in T.PREP_PASOS]
    r.check(all(m >= 0 for m in marcas) and marcas == sorted(marcas)
            and "Asistente terminado" in log,
            "el asistente completo hace los 7 pasos en orden")
    r.check(len(preguntas) >= 5, "confirmando antes de cada bloque que cambia algo")
    r.check(caja.resolver()[0] == "com.gathin.tvhome"
            and set(T.ADBToolbox._prep_paquetes(perfil)) <= caja.desactivados,
            "y la caja acaba limpia y con el lanzador nuevo")

    app.selected_serial = "192.168.1.54:5555"
    caja = CajaTV("p291")
    caja.apks.update(APKS)
    adb = poner_caja(app, caja, todos)
    T.messagebox.askyesnocancel = lambda *a, **k: None
    del app.salida[:]
    app.action_prep_asistente()
    for _ in range(4):
        esperar(app, 150)
    r.check(not adb.se_mando("disable-user") and not adb.se_mando("pm install")
            and "Asistente detenido" in "\n".join(app.salida),
            "«Cancelar» para el asistente sin tocar nada")

    app.selected_serial = "192.168.1.55:5555"
    caja = CajaTV("p291")
    caja.apks.update(APKS)
    adb = poner_caja(app, caja, todos)
    T.messagebox.askyesnocancel = lambda *a, **k: False
    T.messagebox.askyesno = lambda *a, **k: False
    del app.salida[:]
    app.action_prep_asistente()
    for _ in range(6):
        esperar(app, 150)
        if any("Asistente terminado" in m for m in app.salida):
            break
    log = "\n".join(app.salida)
    r.check("Asistente terminado" in log and log.count("saltado") >= 4
            and not adb.se_mando("disable-user") and "reboot" not in adb.dichos(),
            "«No» salta cada paso y el asistente llega al final sin cambiar nada")

    total = [d for doble in todos for d in doble.dichos()]
    r.check(not any("uninstall" in d for d in total), "nunca se desinstala nada")
    r.check(not any('"' in a for doble in todos for c, _ in doble.comandos for a in c),
            "ningún comando lleva comillas dobles")
    r.check(all(pm_suelto(d) for d in total if d.startswith("shell pm ")),
            "en todo el flujo, un solo comando pm por llamada")
    r.check(not any(re.search(r"am start|monkey", d) and re.search(r"ftest|DeviceTest", d)
                    for d in total), "ni un paquete de fábrica arrancado en todo el flujo")

    app.destroy()

if __name__ == "__main__":
    import sys
    sys.exit(1 if correr() else 0)
