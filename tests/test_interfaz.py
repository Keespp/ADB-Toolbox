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
            "el texto de las 10 secciones empieza en la misma columna "
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

    app.destroy()
    return r.resumen()

if __name__ == "__main__":
    import sys
    sys.exit(1 if correr() else 0)
