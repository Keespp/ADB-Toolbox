from tkinter import font as tkfont

from comun import Resultado, crear_app, poner_adb, esperar, T

def lienzos_de_pagina(widget, salida=None):
    salida = [] if salida is None else salida
    for hijo in widget.winfo_children():
        if isinstance(hijo, T.tk.Canvas):
            caja = hijo.bbox("all")
            if caja and (caja[3] - caja[1]) > 200 and hijo.winfo_height() > 200:
                salida.append((caja[3] - caja[1], hijo.winfo_height()))
        lienzos_de_pagina(hijo, salida)
    return salida

def correr():
    r = Resultado("Interfaz")
    app = crear_app()
    poner_adb(app)
    esperar(app)

    apretadas = []
    for nombre in list(app.pages):
        app.show_page(nombre)
        esperar(app, 250)
        for contenido, ventanilla in lienzos_de_pagina(app.pages[nombre]):
            if contenido > ventanilla + 2 and contenido > ventanilla - 60:
                apretadas.append("%s (%d de %d px)" % (nombre, contenido, ventanilla))
    r.check(not apretadas,
            "a 940x760 ninguna página necesita desplazarse: " + (str(apretadas) or "ok"))

    app.geometry("940x640")
    esperar(app, 300)
    app.show_page("Información")
    esperar(app, 300)
    barras = []

    def buscar_barras(w):
        for h in w.winfo_children():
            if isinstance(h, T.ctk.CTkScrollbar):
                barras.append(bool(h.grid_info()))
            buscar_barras(h)
    buscar_barras(app.pages["Información"])
    r.check(any(barras), "al encoger la ventana sale la barra de desplazamiento")
    app.geometry("940x760")
    esperar(app, 250)

    fuente = tkfont.Font(family="Roboto", size=14)
    anchos = set()
    for nombre, boton in app.nav_buttons.items():
        texto = boton.cget("text")
        anchos.add(fuente.measure(texto[:texto.index(nombre)]))
    r.check(len(anchos) == 1,
            "el texto de las %d secciones empieza en la misma columna "
            % len(app.nav_buttons) +
            "(sólo emoji de ancho normal: 'ℹ️' mide 34 px y '🛠️' 47)")

    acciones = [n for n in dir(T.ADBToolbox) if n.startswith("action_")]
    r.check(all(callable(getattr(app, n)) for n in acciones),
            "las %d acciones están enlazadas" % len(acciones))
    r.check(all(n in app.pages for n in app.nav_buttons),
            "cada sección de la barra tiene su página")
    r.check("Ajustes" in app.pages and "Ajustes" not in app.nav_buttons,
            "y Ajustes existe aunque se entre por el engranaje, no por la barra")

    DOS = ("List of devices attached\n"
           "AAA\tdevice product:a model:Equipo_A device:a transport_id:1\n"
           "BBB\tdevice product:b model:Equipo_B device:b transport_id:2\n")
    poner_adb(app, lambda args: (0, DOS, "") if args[:1] == ["devices"] else None)

    app._refresh_devices_worker()
    esperar(app, 250)
    r.check(app.selected_serial == "AAA", "sin nada elegido, se queda con el primero")

    app.selected_serial = "BBB"
    app._refresh_devices_worker()
    esperar(app, 250)
    r.check(app.selected_serial == "BBB",
            "tras refrescar sigues en el equipo que tenías, no saltas al primero")

    app.selected_serial = "CCC"
    app._refresh_devices_worker()
    esperar(app, 250)
    r.check(app.selected_serial == "AAA",
            "y si el tuyo se desconectó, cae al primero disponible")

    elegidos = []
    app._show_picker_window("Desinstalar app", "Desinstalar", elegidos.append,
                            ["com.uno", "com.dos"], danger=False)
    esperar(app, 200)
    ventana = [w for w in app.winfo_children()
               if isinstance(w, T.ctk.CTkToplevel)][-1]

    def botones_de(w, salida=None):
        salida = {} if salida is None else salida
        for h in w.winfo_children():
            if isinstance(h, T.ctk.CTkButton):
                salida[h.cget("text")] = h
            botones_de(h, salida)
        return salida

    b = botones_de(ventana)
    r.check(b["Desinstalar"].cget("state") == "disabled",
            "sin nada elegido, el botón de la acción está apagado")
    b["com.dos"].invoke()
    esperar(app, 100)
    r.check(b["com.dos"].cget("fg_color") == T.COLOR_ACCENT
            and b["com.dos"].cget("text_color") == "#ffffff",
            "la app elegida se pinta como la fila activa de la barra lateral")
    r.check(b["com.uno"].cget("fg_color") == "transparent"
            and b["com.uno"].cget("hover_color") != T.COLOR_ACCENT,
            "las demás quedan sin marcar, y su hover no se confunde con la selección")
    r.check(b["Desinstalar"].cget("state") == "normal",
            "al elegir una, el botón de la acción se enciende")

    buscador = [h for h in ventana.winfo_children()
                if isinstance(h, T.ctk.CTkEntry)][0]
    buscador.insert(0, "dos")
    esperar(app, 100)
    b = botones_de(ventana)
    r.check("com.uno" not in b and b["com.dos"].cget("fg_color") == T.COLOR_ACCENT,
            "al filtrar, la elegida sigue marcada")
    b["Desinstalar"].invoke()
    r.check(elegidos == ["com.dos"], "y la acción se hace sobre la elegida")

    estado = {"admin": True}
    DP = ("Current Device Policy Manager state:\n"
          "  \n  \n  \n"
          "  Enabled Device Admins (User 0, provisioningState: 0):\n"
          "    com.admin.app/.mdmcliente.AdminReceiver:\n"
          "      uid=10089\n"
          "      testOnlyAdmin=false\n")

    def resp_admin(args):
        if args[:1] == ["uninstall"]:
            if estado["admin"]:
                return 0, "Failure [DELETE_FAILED_DEVICE_POLICY_MANAGER]\n", ""
            return 0, "Success\n", ""
        if args[:3] == ["exec-out", "dumpsys", "device_policy"]:
            return 0, DP, ""
        if args[:3] == ["exec-out", "dpm", "remove-active-admin"]:
            estado["admin"] = False
            return 0, "Success: Admin com.admin.app removed\n", ""
        return None

    adb2 = poner_adb(app, resp_admin)
    app.salida = []
    app._do_uninstall("com.admin.app")
    r.check(adb2.se_mando("dpm remove-active-admin com.admin.app/.mdmcliente.AdminReceiver"),
            "el admin sale de device_policy aunque venga 'pelado' (sin ComponentInfo{})")
    r.check(any("Desinstalada: com.admin.app" in m for m in app.salida),
            "y tras quitarlo, el reintento de desinstalación termina bien")
    dichos = adb2.dichos()
    i_dpm = next(k for k, d in enumerate(dichos) if "remove-active-admin" in d)
    i_uni2 = max(k for k, d in enumerate(dichos) if d.startswith("uninstall"))
    r.check(i_uni2 > i_dpm, "el reintento va después de quitar el admin, no antes")

    estado_fb = {"admin": True}
    PKG_DUMP = ("Receiver Resolver Table:\n"
                "  Non-Data Actions:\n"
                "      android.app.action.DEVICE_ADMIN_ENABLED:\n"
                "        9186131 com.fb.app/.mdmcliente.AdminReceiver filter 9e48016\n"
                "          Action: \"android.app.action.DEVICE_ADMIN_ENABLED\"\n")

    def resp_fb(args):
        if args[:1] == ["uninstall"]:
            if estado_fb["admin"]:
                return 0, "Failure [DELETE_FAILED_DEVICE_POLICY_MANAGER]\n", ""
            return 0, "Success\n", ""
        if args[:3] == ["exec-out", "dumpsys", "device_policy"]:
            return 0, "Current Device Policy Manager state:\n", ""
        if args[:3] == ["exec-out", "dumpsys", "package"]:
            return 0, PKG_DUMP, ""
        if args[:3] == ["exec-out", "dpm", "remove-active-admin"]:
            estado_fb["admin"] = False
            return 0, "Success\n", ""
        return None

    adb_fb = poner_adb(app, resp_fb)
    app.salida = []
    app._do_uninstall("com.fb.app")
    r.check(adb_fb.se_mando("dpm remove-active-admin com.fb.app/.mdmcliente.AdminReceiver"),
            "si device_policy no lo lista, el componente se saca del manifiesto del paquete")
    r.check(any("Desinstalada: com.fb.app" in m for m in app.salida),
            "y con ese respaldo la desinstalación termina bien")

    def resp_no_admin(args):
        if args[:1] == ["uninstall"]:
            return 0, "Failure [DELETE_FAILED_DEVICE_POLICY_MANAGER]\n", ""
        if args[:3] == ["exec-out", "dumpsys", "device_policy"]:
            return 0, "Current Device Policy Manager state:\n  (none)\n", ""
        return None

    adb3 = poner_adb(app, resp_no_admin)
    app.salida = []
    app._do_uninstall("com.otro.app")
    r.check(not adb3.se_mando("remove-active-admin"),
            "si no se halla el componente por ningún lado, no se lanza dpm a ciegas")
    r.check(any("Seguridad" in m for m in app.salida),
            "y se avisa de quitarlo a mano en Ajustes")

    conexiones = []

    def resp_conn(args):
        if args[:1] == ["connect"]:
            conexiones.append(args[1])
            return 0, "connected to %s" % args[1], ""
        return None

    poner_adb(app, resp_conn)
    app.salida = []
    app._conectar_ips(["192.168.1.50", "192.168.1.51:5555"])
    r.check(conexiones == ["192.168.1.50:5555", "192.168.1.51:5555"],
            "conectar por red pone :5555 si falta y respeta el puerto si ya viene")
    r.check(any("Conectados 2 de 2" in m for m in app.salida),
            "y resume cuántas conexiones salieron bien")

    app.device_map = {}
    poner_adb(app, resp_conn)
    del conexiones[:]
    app._ventana_encontrados(["192.168.1.60"], 5555)
    esperar(app, 200)
    ventana = [w for w in app.winfo_children()
               if isinstance(w, T.ctk.CTkToplevel)][-1]
    bb = botones_de(ventana)
    clave = next(k for k in bb if k.startswith("Conectar"))
    r.check(clave == "Conectar (1)",
            "la ventana de red muestra cuántos hay seleccionados")
    bb[clave].invoke()
    esperar(app, 100)
    r.check("192.168.1.60:5555" in conexiones,
            "al confirmar, se conecta a los dispositivos hallados")

    dispositivos_auto(r, app)
    soltar_apk(r, app)
    zona_soltar(r, app)
    vigilancia_dpi(r, app)
    reescalado(r, app)
    app.destroy()
    return r.resumen()

import ctypes
from ctypes import wintypes

def memoria_dropfiles(rutas):
    import struct
    k32 = ctypes.WinDLL("kernel32")
    k32.GlobalAlloc.restype = ctypes.c_void_p
    k32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    k32.GlobalLock.restype = ctypes.c_void_p
    k32.GlobalLock.argtypes = [ctypes.c_void_p]
    k32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    datos = struct.pack("<IiiII", 20, 0, 0, 0, 1) + (
        "\0".join(rutas) + "\0\0").encode("utf-16-le")
    memoria = k32.GlobalAlloc(0x0042, len(datos))
    ctypes.memmove(k32.GlobalLock(memoria), datos, len(datos))
    k32.GlobalUnlock(memoria)
    return memoria

def soltar_en_ventana(app, rutas):
    u32 = ctypes.WinDLL("user32")
    u32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT,
                                 wintypes.WPARAM, wintypes.LPARAM]
    u32.PostMessageW(app.winfo_id(), T.WM_DROPFILES, memoria_dropfiles(rutas), 0)

def objeto_de_datos(rutas):
    class STGMEDIUM(ctypes.Structure):
        _fields_ = [("tymed", wintypes.DWORD), ("hGlobal", ctypes.c_void_p),
                    ("pUnkForRelease", ctypes.c_void_p)]
    PEDIR = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p,
                               ctypes.POINTER(STGMEDIUM))

    def pedir(this, formato, medio):
        if ctypes.cast(formato, ctypes.POINTER(ctypes.c_ushort))[0] != 15:
            return -2147221404
        medio.contents.tymed = 1
        medio.contents.hGlobal = memoria_dropfiles(rutas)
        medio.contents.pUnkForRelease = None
        return 0
    funcion = PEDIR(pedir)
    tabla = (ctypes.c_void_p * 4)(None, None, None, ctypes.cast(funcion, ctypes.c_void_p))
    objeto = (ctypes.c_void_p * 1)(ctypes.addressof(tabla))
    return ctypes.addressof(objeto), (funcion, tabla, objeto)

def zona_soltar(r, app):
    import tempfile
    carpeta = tempfile.mkdtemp(prefix="adbtoolbox_zona_")
    apk = T.os.path.join(carpeta, "uno.apk")
    nota = T.os.path.join(carpeta, "nota.txt")
    for ruta in (apk, nota):
        open(ruta, "wb").close()
    app.selected_serial = "HHH"
    quitar = app._soltar_quitar
    r.check(quitar is not None and quitar.ole,
            "la ventana se registra como destino de arrastre (OLE): sabe cuándo "
            "le pasa algo por encima, no sólo cuándo lo sueltan")
    destino = quitar.destino
    tabla = destino.tabla.contents
    yo = ctypes.addressof(destino)
    salida = ctypes.c_void_p()
    propio = (ctypes.c_ubyte * 16)(*(b"\x22\x01" + bytes(6) + b"\xc0" + bytes(6) + b"\x46"))
    ajeno = (ctypes.c_ubyte * 16)(*range(16))
    r.check(tabla.pregunta(yo, ctypes.addressof(propio), ctypes.byref(salida)) == 0
            and salida.value == yo
            and tabla.pregunta(yo, ctypes.addressof(ajeno), ctypes.byref(salida)) != 0,
            "responde como IDropTarget, y sólo como eso")

    recibidas = []
    app._soltar_archivos = recibidas.append
    con_apk, vivo1 = objeto_de_datos([apk])
    sin_apk, vivo2 = objeto_de_datos([nota])
    mapeada = lambda: app.zona_soltar.winfo_manager() == "place"

    efecto = wintypes.DWORD(7)
    tabla.entra(yo, con_apk, 0, 0, ctypes.byref(efecto))
    esperar(app, 150)
    app.update_idletasks()
    r.check(efecto.value == 1 and mapeada()
            and app._zona_titulo.cget("text") == "Suelta aquí para instalar"
            and app.device_menu.get() in app._zona_detalle.cget("text")
            and "uno.apk" in app._zona_archivos.cget("text"),
            "al entrar arrastrando un APK, el panel se vuelve la zona de soltar, con "
            "el equipo de destino y el archivo")
    r.check(app.zona_soltar.winfo_width() == app.content.winfo_width()
            and app.zona_soltar.winfo_height() == app.content.winfo_height()
            and app.zona_soltar.cget("border_color") == T.COLOR_ACCENT,
            "y cubre el panel entero, con el aro azul")
    efecto = wintypes.DWORD(7)
    tabla.encima(yo, 0, 0, ctypes.byref(efecto))
    r.check(efecto.value == 1, "mientras se mueve encima, el cursor sigue en «copiar»")

    tabla.sale(yo)
    tabla.entra(yo, con_apk, 0, 0, ctypes.byref(wintypes.DWORD(7)))
    esperar(app, 300)
    r.check(mapeada(), "salir y volver a entrar al pasar de un widget a otro no la "
                       "hace parpadear")
    tabla.sale(yo)
    esperar(app, 300)
    r.check(not mapeada(), "al salir de la ventana, la zona se va")

    efecto = wintypes.DWORD(7)
    tabla.entra(yo, sin_apk, 0, 0, ctypes.byref(efecto))
    esperar(app, 150)
    r.check(efecto.value == 0 and app._zona_titulo.cget("text") == "Esto no es un APK"
            and app.zona_soltar.cget("border_color") == T.COLOR_RED,
            "con algo que no es un APK, se pone en rojo y no deja soltar")
    tabla.sale(yo)
    app.selected_serial = None
    efecto = wintypes.DWORD(7)
    tabla.entra(yo, con_apk, 0, 0, ctypes.byref(efecto))
    esperar(app, 150)
    r.check(efecto.value == 0
            and app._zona_titulo.cget("text") == "No hay ningún equipo elegido",
            "sin equipo elegido, lo avisa antes de soltar")
    tabla.sale(yo)
    esperar(app, 300)
    app.selected_serial = "HHH"

    tabla.entra(yo, con_apk, 0, 0, ctypes.byref(wintypes.DWORD(7)))
    efecto = wintypes.DWORD(7)
    tabla.suelta(yo, con_apk, 0, 0, ctypes.byref(efecto))
    esperar(app, 150)
    r.check(efecto.value == 1 and recibidas == [[apk]] and not mapeada(),
            "al soltar, la zona se va y se pasa a instalar (con su confirmación)")
    del app._soltar_archivos

def soltar_apk(r, app):
    import tempfile
    carpeta = tempfile.mkdtemp(prefix="adbtoolbox_apk_")
    uno = T.os.path.join(carpeta, "uno.apk")
    dos = T.os.path.join(carpeta, "Dos Ñandú.APK")
    nota = T.os.path.join(carpeta, "nota.txt")
    falsa = T.os.path.join(carpeta, "carpeta.apk")
    for ruta in (uno, dos, nota):
        open(ruta, "wb").close()
    T.os.mkdir(falsa)

    recibidas = []
    app._soltar_archivos = recibidas.append
    soltar_en_ventana(app, [uno, dos])
    esperar(app, 400)
    del app._soltar_archivos
    r.check(recibidas == [[uno, dos]],
            "la ventana acepta archivos soltados desde el Explorador (WM_DROPFILES), "
            "con rutas con espacios y eñes")

    instalados, preguntas = [], []

    def transferencia(args, etiqueta, timeout=1800):
        instalados.append(args)
        return 0, "Performing Streamed Install\nSuccess"
    app.run_adb_transfer = transferencia
    respuesta = [True]
    original = T.messagebox.askyesno
    T.messagebox.askyesno = lambda titulo, texto, **k: preguntas.append(texto) or respuesta[0]
    try:
        app.selected_serial = "HHH"
        del app.salida[:]
        app._soltar_archivos([uno, dos, nota, falsa])
        esperar(app, 150)
        r.check(instalados == [["install", "-r", uno], ["install", "-r", dos]],
                "se instalan los APK soltados, uno tras otro (también en mayúsculas)")
        r.check(len(preguntas) == 1 and app.device_menu.get() in preguntas[0]
                and "uno.apk" in preguntas[0] and "Dos Ñandú.APK" in preguntas[0],
                "antes se pregunta, diciendo en qué equipo y qué archivos")
        r.check(any("Se ignoran 2" in m for m in app.salida)
                and any("Instalados 2 de 2" in m for m in app.salida),
                "lo que no es un .apk (ni una carpeta que se llame así) se ignora y "
                "se avisa")

        del instalados[:], preguntas[:]
        app._soltar_archivos([nota])
        r.check(not instalados and not preguntas
                and any("Sólo se instalan archivos .apk" in m for m in app.salida),
                "sin ningún APK no se pregunta ni se instala nada")
        respuesta[0] = False
        app._soltar_archivos([uno])
        r.check(len(preguntas) == 1 and not instalados,
                "si dices que no, no se instala")
        respuesta[0] = True
        del preguntas[:]
        app.selected_serial = None
        app._soltar_archivos([uno])
        r.check(not preguntas and not instalados,
                "sin equipo elegido no se pregunta ni se instala")
    finally:
        T.messagebox.askyesno = original
        del app.run_adb_transfer
        app.selected_serial = "HHH"
    poner_adb(app)

def dispositivos_auto(r, app):
    lista = []

    def responder(args):
        if args[:1] == ["devices"]:
            return 0, "List of devices attached\n" + "".join(
                "%s\t%s product:x model:Equipo_%s device:x\n" % (s, e, s)
                for s, e in lista), ""
        if args == ["exec-out", "getprop"]:
            return 0, "[ro.product.model]: [Modelo-%s]\n" % app.selected_serial, ""
        if args[:1] == ["connect"]:
            return 0, "connected to %s" % args[1], ""
        return None
    adb = poner_adb(app, responder)

    def hay(*equipos, **kw):
        lista[:] = [(e, "device") if isinstance(e, str) else e for e in equipos]
        app._refresh_devices_worker(auto=kw.get("auto", True), elegir=kw.get("elegir"))
        esperar(app, 150)

    def dicho(texto):
        return any(texto in m for m in app.salida)

    modelo = lambda: app.info_labels["Modelo"].get()
    app.show_page("Información")
    app._elegir_dispositivo(None)
    hay("AAA", auto=False)
    r.check(app.selected_serial == "AAA" and modelo() == "Modelo-AAA",
            "al quedar elegido un equipo, Información se carga sola")
    hay("AAA", "BBB", auto=False)
    app.on_device_selected("Equipo BBB  (BBB)")
    esperar(app, 150)
    r.check(app.selected_serial == "BBB" and modelo() == "Modelo-BBB",
            "al cambiar de equipo en el menú, Información pasa al nuevo")

    del app.salida[:]
    hay("AAA", "BBB", "CCC")
    r.check(app.selected_serial == "BBB" and dicho("＋ Conectado: Equipo CCC  (CCC)"),
            "un equipo nuevo no le quita el sitio al elegido si sigue conectado "
            "(se avisa en la consola)")
    hay("AAA", "CCC")
    r.check(app.selected_serial == "BBB" and dicho("－ Desconectado: BBB"),
            "si el elegido se desconecta, no salta solo a otro que ya estaba")
    hay()
    r.check(app.selected_serial is None
            and app.device_menu.get() == "Sin dispositivos" and modelo() == "—",
            "sin equipos, Información se vacía")
    hay("DDD")
    r.check(app.selected_serial == "DDD" and modelo() == "Modelo-DDD",
            "al conectar uno nuevo sin otro elegido, se elige y carga su información")

    app._tv_busy = True
    hay("EEE")
    r.check(app.selected_serial == "DDD",
            "con una operación en marcha no se cambia de equipo (p. ej. adb root "
            "tumba la conexión de la caja un momento)")
    app._tv_busy = False

    app.show_page("Capturas")
    hay()
    adb.limpiar()
    hay("FFF")
    r.check(app.selected_serial == "FFF" and modelo() == "—"
            and not adb.se_mando("getprop"),
            "en otra sección sólo se vacía Información, sin preguntar al equipo")
    app.show_page("Información")
    esperar(app, 150)
    r.check(modelo() == "Modelo-FFF", "y se carga al abrirla")

    hay(("GGG", "unauthorized"), "FFF")
    r.check(dicho("GGG: acepta la depuración USB"),
            "un equipo sin autorizar avisa de aceptar la depuración en su pantalla")
    hay("FFF", "HHH", auto=False, elegir="HHH")
    r.check(app.selected_serial == "HHH",
            "tras conectar por IP queda elegido el equipo recién conectado")

    pedidos = []
    app.refresh_devices = lambda elegir=None: pedidos.append(elegir)
    app._conectar_ips(["10.0.0.5"])
    esperar(app, 450)
    del app.refresh_devices
    r.check(pedidos == ["10.0.0.5:5555"],
            "«Conectar por IP» pide elegir el equipo al que se conectó")

    avisos = []
    app._refresh_devices_worker = lambda auto=False, elegir=None: avisos.append(auto)
    app._firma_vista = None
    app._vigia_aviso("AAA\tdevice\n")
    app._vigia_aviso("AAA\tdevice\n")
    app._vigia_aviso("AAA\tdevice\nBBB\toffline\n")
    del app._refresh_devices_worker
    r.check(avisos == [True, True],
            "la vigilancia (adb track-devices) sólo recarga la lista cuando cambia")

    evento = T.threading.Event()
    T.ADBToolbox.threaded(app, lambda: evento.wait(5))
    ocupado = app._ocupado()
    evento.set()
    for _ in range(80):
        if app._trabajos == 0:
            break
        esperar(app, 25)
    r.check(ocupado and not app._ocupado(),
            "un trabajo en marcha cuenta como ocupado, y deja de contar al acabar")

class Rastreo(object):
    update_loop_interval = 100
    loop_pause_after_new_scaling = 1500

    def __init__(self, ventana, escala):
        self.window_widgets_dict = {ventana: []}
        self.window_dpi_scaling_dict = {ventana: escala}
        self.monitor = escala

    def get_window_dpi_scaling(self, ventana):
        return self.monitor

    def check_dpi_scaling(self):
        pass

def vigilancia_dpi(r, app):
    app._dpi_sitio = None
    rastreo = Rastreo(app, 1.25)
    hechos = []
    pulsado = [True]
    original, raton = T._reescalar_ventana, T._raton_pulsado
    T._reescalar_ventana = lambda ras, v: hechos.append(ras.window_dpi_scaling_dict[v])
    T._raton_pulsado = lambda: pulsado[0]
    try:
        rastreo.monitor = 1.0
        T._revisar_dpi(rastreo)
        r.check(hechos == [], "mientras se arrastra la ventana no se reescala")
        pulsado[0] = False
        T._revisar_dpi(rastreo)
        r.check(hechos == [1.0], "al soltarla en la otra pantalla se reescala una vez")
        rastreo.monitor = 1.25
        T._revisar_dpi(rastreo)
        T._revisar_dpi(rastreo)
        r.check(hechos == [1.0],
                "si al encogerse cae en la otra pantalla, no vuelve a reescalar "
                "sin moverse (era un bucle de varios segundos por vuelta)")
        x, y = app.winfo_rootx(), app.winfo_rooty()
        T.tk.Tk.wm_geometry(app, "+%d+%d" % (x + 40, y + 20))
        app.update()
        T._revisar_dpi(rastreo)
        r.check(hechos == [1.0, 1.25], "al moverla de nuevo sí vuelve a mirar la pantalla")
    finally:
        T._reescalar_ventana, T._raton_pulsado = original, raton

def reescalado(r, app):
    ST = T.ctk.ScalingTracker
    real = ST.window_dpi_scaling_dict[app]
    otra = 1.5 if real != 1.5 else 1.0
    if not app.consola_abierta:
        app.toggle_consola()
    app.progress_frame.grid_remove()
    app.show_page("Información")
    app.update_idletasks()
    app._dpi_sitio = (app.winfo_rootx(), app.winfo_rooty())

    def a_destiempo(raiz, escala):
        malos = []
        for orden in ST.window_widgets_dict[app]:
            w = orden.__self__
            if (w is not app and T._en_rama(w, {raiz}) and w.winfo_ismapped()
                    and abs(w._get_widget_scaling() - escala) > 1e-6):
                malos.append(w)
        return malos

    ST.window_dpi_scaling_dict[app] = otra
    T._reescalar_ventana(ST, app)
    app.update_idletasks()
    mapeadas = [n for n, p in app.pages.items() if p.winfo_ismapped()]
    r.check(mapeadas == ["Información"],
            "al cambiar de escala no reaparecen las páginas ocultas: %s" % mapeadas)
    r.check(not app.progress_frame.winfo_ismapped(),
            "ni la barra de progreso escondida")
    r.check(not a_destiempo(app.pages["Información"], otra),
            "lo visible queda reescalado en el acto")
    archivos = app.pages["Archivos"]
    r.check(abs(archivos._get_widget_scaling() - real) < 1e-6,
            "las páginas ocultas se dejan para cuando se abran")
    app.show_page("Archivos")
    app.update_idletasks()
    r.check(abs(archivos._get_widget_scaling() - otra) < 1e-6
            and not a_destiempo(archivos, otra),
            "y al abrirlas se ponen al día")

    app.toggle_consola()
    app.update_idletasks()
    ST.window_dpi_scaling_dict[app] = real
    T._reescalar_ventana(ST, app)
    app.update_idletasks()
    r.check(not app.consola_cuerpo.winfo_ismapped(),
            "la consola plegada sigue plegada tras reescalar")
    app.toggle_consola()
    app.update_idletasks()
    r.check(app.consola_cuerpo.winfo_ismapped()
            and not a_destiempo(app.consola_cuerpo, real),
            "y al desplegarla ya tiene la escala nueva")
    esperar(app, 1100)

if __name__ == "__main__":
    import sys
    sys.exit(1 if correr() else 0)
