import faulthandler
import ipaddress
import os
import socket

from comun import Resultado, crear_app, poner_adb, esperar, T

RED_PC = {"nombre": "Intel Wi-Fi 6 AX201", "ip": "192.168.1.34",
          "mascara": "255.255.255.0", "puerta": "192.168.1.1"}
RED_VBOX = {"nombre": "VirtualBox Host-Only", "ip": "192.168.56.1",
            "mascara": "255.255.255.0", "puerta": ""}
USB = {"tipo": "usb", "ruta": r"\\?\usb#vid_0483&pid_5743#1#{28d78fad}",
       "nombre": "USB · Printer POS-80 (0483:5743)"}
COLA = {"tipo": "cola", "cola": "XP-80C", "nombre": "Windows · XP-80C (USB001)"}

class Impresora(object):

    def __init__(self):
        self.ip = T.IMPRESORA_FABRICA
        self.mascara = "255.255.255.0"
        self.puerta = "192.168.123.1"
        self.cable = True
        self.falla_usb = False
        self.recibido = []
        self.tickets = []
        self.intentos_tcp = 0

    def escribir(self, destino, datos):
        if self.falla_usb:
            raise OSError("El dispositivo no está listo")
        self.recibido.append((destino["tipo"], datos))
        if datos[:4] == T.IMPRESORA_TRAMA_IP and len(datos) == 16:
            self.ip, self.mascara, self.puerta = (
                socket.inet_ntoa(datos[i:i + 4]) for i in (4, 8, 12))

    def tcp(self, ip, datos, timeout=2):
        self.intentos_tcp += 1
        if not self.cable or ip != self.ip:
            raise OSError("timed out")
        self.tickets.append(datos)

def preparar(app, imp, ocupadas):
    consultas = []

    def arp(ip):
        consultas.append(ip)
        return ip in ocupadas
    app._impresoras = lambda: [USB, COLA]
    app._interfaces_red = lambda: [RED_PC, RED_VBOX]
    app._ip_ocupada = arp
    app._impresora_escribir = imp.escribir
    app._impresora_tcp = imp.tcp
    return consultas

def recorrer(w):
    for h in w.winfo_children():
        yield h
        for n in recorrer(h):
            yield n

def ventana(app):
    vs = [w for w in app.winfo_children()
          if isinstance(w, T.ctk.CTkToplevel) and w.winfo_exists()]
    return vs[-1] if vs else None

def campos(win):
    return [h for h in recorrer(win) if isinstance(h, T.ctk.CTkEntry)][:3]

def botones(win, texto):
    return [h for h in recorrer(win)
            if isinstance(h, T.ctk.CTkButton) and h.cget("text") == texto]

def boton(win, texto):
    return botones(win, texto)[0]

def textos(win):
    return " | ".join(h.cget("text") for h in recorrer(win)
                      if isinstance(h, T.ctk.CTkLabel))

def escribir(app, win, ip=None, mascara=None, puerta=None):
    for campo, valor in zip(campos(win), (ip, mascara, puerta)):
        if valor is not None:
            campo.delete(0, "end")
            campo.insert(0, valor)
    esperar(app, 600)

def menu_red(win):
    return next(h for h in recorrer(win) if isinstance(h, T.ctk.CTkOptionMenu))

def abrir(app):
    app.action_impresora_ip()
    esperar(app, 700)
    return ventana(app)

def correr():
    r = Resultado("Impresora térmica")

    r.check(T.trama_ip_xprinter("192.168.1.250", "255.255.255.0", "192.168.1.1")
            == bytes.fromhex("1f1b1fb2" "c0a801fa" "ffffff00" "c0a80101"),
            "la trama de Xprinter es 1F 1B 1F B2 + IP + máscara + puerta, 4 bytes cada una")

    red, error = T.revisar_ip_impresora("192.168.1.80", "255.255.255.0", "192.168.1.1")
    r.check(red == ipaddress.IPv4Network("192.168.1.0/24") and not error,
            "una IP, máscara y puerta coherentes pasan")
    malos = {
        "IP imposible": ("192.168.1.300", "255.255.255.0", "192.168.1.1"),
        "máscara no contigua": ("192.168.1.80", "255.0.255.0", "192.168.1.1"),
        "máscara al revés (0.0.0.255)": ("192.168.1.80", "0.0.0.255", "192.168.1.1"),
        "IP de difusión": ("192.168.1.255", "255.255.255.0", "192.168.1.1"),
        "IP de red": ("192.168.1.0", "255.255.255.0", "192.168.1.1"),
        "puerta fuera de la red": ("192.168.1.80", "255.255.255.0", "10.0.0.1"),
        "IP igual a la puerta": ("192.168.1.1", "255.255.255.0", "192.168.1.1"),
        "IP de enlace local": ("169.254.3.4", "255.255.0.0", "169.254.0.1"),
    }
    pasan = [k for k, v in malos.items() if T.revisar_ip_impresora(*v)[0] is not None]
    r.check(not pasan, "se rechaza: " + ", ".join(malos) + (" — pasan: %s" % pasan
                                                            if pasan else ""))

    c24 = T.ips_candidatas(ipaddress.IPv4Network("192.168.1.0/24"),
                           {"192.168.1.250"})
    r.check(c24[0] == "192.168.1.249" and "192.168.1.250" not in c24,
            "las candidatas bajan desde la .250 y se saltan lo que hay que evitar")
    r.check(all(c not in ("192.168.1.0", "192.168.1.255") for c in c24)
            and len(c24) == 48, "nunca proponen la de red ni la de difusión")
    r.check(T.ips_candidatas(ipaddress.IPv4Network("10.0.0.0/30")) ==
            ["10.0.0.2", "10.0.0.1"], "en una /30 también salen sus dos hosts")
    r.check(T.ips_candidatas(ipaddress.IPv4Network("172.16.0.0/16"))[0] ==
            "172.16.255.250", "y en una /16 empiezan arriba del todo")
    t = T.ticket_ip("192.168.1.248", "255.255.255.0", "192.168.1.1")
    r.check(t.startswith(b"\x1b@") and t.endswith(T.IMPRESORA_CORTE)
            and b"192.168.1.248" in t and max(t[2:-4]) < 128,
            "el ticket inicializa, lleva la IP en ASCII puro y corta el papel")

    app = crear_app()
    adb = poner_adb(app)
    esperar(app)

    nombres = [b.cget("text") for b in recorrer(app.pages["Red / WiFi"])
               if isinstance(b, T.ctk.CTkButton)]
    r.check("Cambiar IP de impresora térmica (USB)..." in nombres,
            "la acción está en Red / WiFi")

    imp = Impresora()
    consultas = preparar(app, imp, {"192.168.1.1", "192.168.1.34",
                                    "192.168.1.250", "192.168.1.249"})
    win = abrir(app)
    r.check(win is not None, "se abre la ventana")
    ip, mascara, puerta = (c.get() for c in campos(win))
    r.check(ip == "192.168.1.248",
            "propone la primera IP libre de la red del PC, de la .250 hacia abajo "
            "(%s)" % ip)
    r.check((mascara, puerta) == ("255.255.255.0", "192.168.1.1"),
            "con la máscara y la puerta de enlace del PC")
    r.check("192.168.1.34" not in consultas and "192.168.1.1" not in consultas,
            "ni pregunta por la IP del PC ni por la puerta: nunca se proponen")
    r.check(menu_red(win).get().startswith("192.168.1.34/24"),
            "la red elegida es la del PC con puerta de enlace")
    r.check("✓ 192.168.1.248 está libre" in textos(win), "y avisa de que está libre")

    cambiar = boton(win, "Cambiar IP")
    r.check(cambiar.cget("state") == "disabled",
            "sin impresora elegida, «Cambiar IP» está apagado")
    r.check(len(botones(win, USB["nombre"])) == 1
            and len(botones(win, COLA["nombre"])) == 1,
            "lista la impresora USB y la cola de Windows, una fila cada una")

    win.update_idletasks()
    r.check(win.winfo_reqheight() <= win.winfo_height(),
            "la ventana cabe entera sin recortar nada (%d de %d px)"
            % (win.winfo_reqheight(), win.winfo_height()))
    r.check(win.winfo_height() - win.winfo_reqheight() < 60,
            "y sin un hueco vacío debajo")

    boton(win, USB["nombre"]).invoke()
    r.check(cambiar.cget("state") == "normal", "al elegir la impresora se enciende")

    escribir(app, win, ip="192.168.1.300")
    r.check(cambiar.cget("state") == "disabled" and "La IP no es válida" in textos(win),
            "una IP mal escrita lo apaga y lo dice")
    escribir(app, win, ip="192.168.1.34")
    r.check(cambiar.cget("state") == "disabled" and "es la IP de este PC" in textos(win),
            "la IP del propio PC no se acepta")
    escribir(app, win, ip="192.168.1.80", puerta="10.0.0.1")
    r.check(cambiar.cget("state") == "disabled",
            "con la puerta de enlace en otra red tampoco")
    escribir(app, win, ip="192.168.1.250", puerta="192.168.1.1")
    r.check("192.168.1.250 ya responde" in textos(win),
            "una IP que ya contesta en la red se avisa")

    preguntas = []
    original = T.messagebox.askyesno
    T.messagebox.askyesno = lambda titulo, *a, **k: preguntas.append(titulo) or False
    try:
        cambiar.invoke()
        esperar(app, 100)
    finally:
        T.messagebox.askyesno = original
    r.check(preguntas == ["IP en uso"] and not imp.recibido and ventana(app) is win,
            "y al pulsar pregunta; si dices que no, no se manda nada")

    escribir(app, win, ip="192.168.1.248")
    cambiar.invoke()
    esperar(app, 200)
    r.check(ventana(app) is None, "al cambiar, la ventana se cierra")
    r.check(imp.recibido == [("usb", T.trama_ip_xprinter(
        "192.168.1.248", "255.255.255.0", "192.168.1.1"))],
            "por USB va exactamente una trama, con la IP elegida")
    r.check(imp.ip == "192.168.1.248" and len(imp.tickets) == 1
            and b"192.168.1.248" in imp.tickets[0],
            "y se comprueba por la red imprimiendo el ticket en la IP nueva")
    r.check(any("✓ Responde en 192.168.1.248:9100" in m for m in app.salida),
            "la consola confirma que responde")

    del app.salida[:]
    imp.cable = False
    imp.intentos_tcp = 0
    ok = app._impresora_ip_worker(USB, "192.168.1.247", "255.255.255.0",
                                  "192.168.1.1")
    r.check(not ok and imp.intentos_tcp == T.IMPRESORA_INTENTOS
            and any("✗ No responde en 192.168.1.247" in m for m in app.salida),
            "sin cable de red reintenta %d veces y explica qué mirar"
            % T.IMPRESORA_INTENTOS)

    del app.salida[:]
    imp.cable = True
    imp.falla_usb = True
    imp.intentos_tcp = 0
    ok = app._impresora_ip_worker(USB, "192.168.1.246", "255.255.255.0",
                                  "192.168.1.1")
    r.check(not ok and imp.intentos_tcp == 0
            and any("✗ No se pudo escribir" in m for m in app.salida),
            "si el USB falla, lo dice y no intenta comprobar nada")
    imp.falla_usb = False

    imp.recibido, imp.intentos_tcp = [], 0
    win = abrir(app)
    boton(win, USB["nombre"]).invoke()
    escribir(app, win, ip="10.0.0.50", mascara="255.255.255.0", puerta="10.0.0.1")
    r.check("Fuera de la red del PC" in textos(win)
            and boton(win, "Cambiar IP").cget("state") == "normal",
            "una IP de otra red se acepta, avisando de que no se podrá comprobar")
    preguntas = []
    T.messagebox.askyesno = lambda titulo, *a, **k: preguntas.append(titulo) or True
    try:
        boton(win, "Cambiar IP").invoke()
        esperar(app, 200)
    finally:
        T.messagebox.askyesno = original
    r.check(preguntas == ["Fuera de la red del PC"],
            "y antes de mandarla lo pregunta")
    r.check(imp.recibido == [("usb", T.trama_ip_xprinter(
        "10.0.0.50", "255.255.255.0", "10.0.0.1"))] and imp.intentos_tcp == 0,
            "la manda por USB y no pierde tiempo intentando comprobarla")

    imp.recibido = []
    win = abrir(app)
    menu = menu_red(win)
    r.check(T.IMPRESORA_MANUAL in menu.cget("values"),
            "el menú de red tiene la opción de escribirla a mano")
    menu._dropdown_callback(T.IMPRESORA_MANUAL)
    esperar(app, 200)
    boton(win, COLA["nombre"]).invoke()
    escribir(app, win, ip="172.20.4.30", mascara="255.255.0.0", puerta="172.20.0.1")
    preguntas = []
    T.messagebox.askyesno = lambda titulo, *a, **k: preguntas.append(titulo) or True
    try:
        boton(win, "Cambiar IP").invoke()
        esperar(app, 200)
    finally:
        T.messagebox.askyesno = original
    r.check(not preguntas and imp.recibido == [("cola", T.trama_ip_xprinter(
        "172.20.4.30", "255.255.0.0", "172.20.0.1"))],
            "a mano, con la cola de Windows: se manda sin preguntar por la red del PC")

    muchas = [dict(USB, nombre="USB · Impresora %d" % i) for i in range(6)]
    app._impresoras = lambda: muchas
    faulthandler.dump_traceback_later(60, exit=True)
    latidos = []
    win = abrir(app)
    app.after(50, lambda: latidos.append(1))
    esperar(app, 400)
    faulthandler.cancel_dump_traceback_later()
    lista = next(h for h in recorrer(win) if isinstance(h, T.ctk.CTkScrollableFrame))
    r.check(latidos and bool(lista._scrollbar.grid_info()),
            "con más impresoras de las que caben sale la barra y la ventana sigue viva "
            "(antes la barra se mostraba y escondía sin fin y la colgaba)")
    r.check(lista._scrollbar.winfo_reqheight() <= lista._parent_canvas.winfo_height(),
            "la barra no pide más alto que la lista, que es lo que disparaba el vaivén")
    win.destroy()

    r.check(not adb.comandos, "nada de esto pasa por adb")
    app.destroy()

    if os.name == "nt":
        real = T.ADBToolbox.__new__(T.ADBToolbox)
        real.log = lambda m: None
        redes = real._interfaces_red()
        r.check(isinstance(redes, list) and all(
            {"nombre", "ip", "mascara", "puerta"} <= set(x) for x in redes),
            "leer la red de este PC de verdad no revienta (%d redes)" % len(redes))
        destinos = real._impresoras()
        r.check(isinstance(destinos, list) and all(
            d["tipo"] in ("usb", "cola") and d["nombre"] for d in destinos),
            "ni listar sus impresoras USB y colas (%d)" % len(destinos))

    return r.resumen()

if __name__ == "__main__":
    import sys
    sys.exit(1 if correr() else 0)
