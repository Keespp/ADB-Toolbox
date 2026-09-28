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

    app.destroy()
    return r.resumen()

if __name__ == "__main__":
    import sys
    sys.exit(1 if correr() else 0)
