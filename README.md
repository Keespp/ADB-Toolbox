# ADB Toolbox

Interfaz gráfica limpia y profesional para ejecutar comandos ADB útiles desde Windows,
sin tener que memorizar la línea de comandos. Una herramienta de **keesp**.

El aspecto es **Aqua oscuro**, el lenguaje visual de macOS: barra de herramientas
unificada, barra lateral agrupada y las acciones de cada página en una lista con
filetes, no en una parrilla de botones.

![interfaz Aqua oscuro](https://img.shields.io/badge/interfaz-Aqua%20oscuro-0A84FF) ![keesp](https://img.shields.io/badge/de-keesp-2C2C31) ![python](https://img.shields.io/badge/python-3.14-blue) ![windows](https://img.shields.io/badge/plataforma-Windows-0078D6) ![licencia MIT](https://img.shields.io/badge/licencia-MIT-green)

## Descargar

**[⬇ Descarga `ADB_Toolbox.exe` desde la última versión](../../releases/latest)**

Es un único archivo portable (~20 MB) para Windows: lo copias a cualquier carpeta o al
escritorio y lo abres. No requiere instalar Python. Sólo necesitas `adb`
(ver [ADB (platform-tools)](#adb-platform-tools)).

La primera vez tarda unos segundos en abrir, porque se desempaqueta. Como el ejecutable
no está firmado, Windows SmartScreen puede avisar: *Más información → Ejecutar de todas
formas*. Si prefieres no fiarte del `.exe`, puedes [ejecutarlo desde el código](#ejecutar-desde-el-código).

## Funciones

La barra lateral agrupa las secciones en **Dispositivo**, **Software** y **Sistema**,
en este orden:

| Sección | Botones |
|---|---|
| ℹ️ **Información** | Panel con modelo, serial, CID, número de compilación, Android, batería (nivel, salud, temperatura), almacenamiento libre y RAM **con barra de ocupación** (verde / ámbar / rojo según lo llena que esté), resolución, IP y tiempo encendido. Cada dato **se puede seleccionar y copiar** (Ctrl+C), y el botón de copiar se lleva la ficha entera |
| 📸 **Capturas** | Captura de pantalla (guarda en carpeta **y** copia al portapapeles), grabar pantalla con inicio/parada manual, espejar en tiempo real (scrcpy), abrir carpeta |
| 📁 **Archivos** | Explorar el equipo, enviar (push), traer (pull), eliminar y **editar los XML en el sitio** — [ver abajo](#editar-un-xml-del-equipo) |
| 🎮 **Control remoto** | D-pad y OK, atrás, inicio, menú, recientes, volumen, silencio, play/pausa, encendido, y un campo que escribe en el equipo lo que teclees en el PC |
| 📦 **Aplicaciones** | Desinstalar APK (**incluidas las que son administrador de dispositivos**), instalar APK, extraer el APK instalado, abrir una app, ver y cambiar sus permisos, **listar las apps con su versión** (solo las tuyas o todas, incluidas las del sistema), forzar detención, borrar datos |
| 📋 **Registros** | Extraer el logcat completo, el de una app concreta o sólo los errores; traer los registros que el equipo guarda en disco; generar el bugreport de Android; limpiar el buffer |
| 🛠️ **Desarrollador** | Límites de diseño, overdraw GPU, mostrar toques, ubicación del puntero, animaciones, no mantener actividades, permanecer activo al cargar, perfil de renderizado GPU (todos alternables ON/OFF) |
| ⚡ **Energía** | Reiniciar, recovery, bootloader, apagar, pantalla ON/OFF |
| 🌐 **Red** | Habilitar ADB por WiFi (puerto 5555), conectar por IP, **buscar dispositivos en la red** (escanea tu LAN y los conecta de golpe), emparejar por WiFi (Android 11+) |
| 📺 **TV Box** | Signage p291: fix completo, fecha y hora, resolución, diagnóstico, reiniciar la app — [ver abajo](#sección-tv-box-signage-p291) |
| ✅ **Preparar TV Box** | Asistente para dejar lista una caja nueva: copia de seguridad, desactivar el bloatware, lanzador y tema, app de señalización, reinicio y cierre de ADB, con restauración — [ver abajo](#preparar-tv-box-paso-a-paso) |

### Editar un XML del equipo

Doble clic sobre un `.xml` de la lista (o el botón **Editar XML** con el archivo
seleccionado) lo abre en un editor, sin pasar por el disco del PC: se lee con
`exec-out cat` y se devuelve con `push`.

- **Comprobar XML** dice si está bien formado, y al guardar avisa si no lo está: un
  config roto puede dejar la app del equipo sin arrancar.
- **Guardar en el equipo** pide confirmación y enseña la ruta exacta que va a
  sobrescribir. **Deshacer cambios** vuelve a lo que hay en el dispositivo.
- Se respetan la **codificación** (UTF-8 con o sin BOM, o latin-1) y los **finales de
  línea** del archivo original.
- **Ajustar al ancho** parte las líneas largas para leerlas; estos config suelen venir
  en una sola línea kilométrica. No toca el contenido.
- El límite es 1 MB: por encima de eso no es un config, y para eso está *Traer al PC*.

El contenido **no se escribe nunca en la consola** — sólo su tamaño —, porque estos
XML llevan credenciales en claro.

## Registros (logcat)

Los archivos se guardan en `%USERPROFILE%\Documents\ADB_Toolbox\registros`, con el
modelo o el paquete y la fecha en el nombre. Cada uno lleva una cabecera con el
dispositivo, su Android, la compilación y el comando exacto que lo generó, para que se
entienda solo al abrirlo o al reenviarlo a alguien.

| Botón | Qué extrae |
|---|---|
| **Log completo del dispositivo** | Todos los buffers (`-b all`), lo que en un equipo con horas encendido son fácilmente 90.000 líneas |
| **Log de una app** | Sólo lo suyo: las líneas de su proceso **y** las que nombran el paquete, porque los cierres inesperados los registra otro proceso |
| **Sólo errores y cuelgues** | Nivel E y superior, y además enseña las últimas ocho en la consola |
| **Limpiar el registro** | Vacía el buffer del equipo — el paso previo a reproducir un fallo, para que el registro salga limpio |

Si la app no está corriendo cuando pides su registro, te avisa: sin proceso vivo
sólo se puede filtrar por menciones al paquete.

### Ojo: `logcat` no lo trae todo

`logcat` es un anillo en RAM. En un terminal NEW9310 son 4 MiB para `main` y 4 para
`system`, o sea **unas horas de historia**; lo anterior ya se perdió. Y fuera de ese
anillo quedan los crashes nativos, los ANR, el historial del sistema y el estado de
`dumpsys`. Para eso están los dos botones siguientes.

### Registros del fabricante

Estos POS guardan además el logcat y el kernel **en disco**, que es lo que empaqueta su
LogManager y por eso pesa: en `/data/Syslog` y `/sdcard/ylog`. Ese histórico llega
mucho más atrás que el anillo de RAM.

El botón los empaqueta **dentro del equipo** con `tar -czf` y se trae un solo archivo
comprimido, en vez de arrastrar cientos de MB archivo a archivo. Puedes pedir sólo los
últimos 7 días o todo. `/data/Syslog` necesita root, que en estos equipos (`userdebug`)
funciona; la app lo eleva, lo trae y devuelve `adbd` a su estado normal, borrando el
temporal que dejó en el equipo.

Ejemplo real: 17 archivos de los últimos 7 días → 10,8 MB comprimidos, 22 segundos.

### Bugreport

El informe estándar de Android, **sin root y en cualquier dispositivo**: logcat, kernel,
tombstones, ANR, dropbox y todos los `dumpsys`, en un zip. Tarda un par de minutos
(141 s y 3,1 MB con 380 archivos en el NEW9310).

Los dos no se solapan: el del fabricante te da **profundidad en el tiempo**, el
bugreport te da **amplitud del estado del sistema**.

## Serial, CID y número de compilación

Los tres salen en el panel de **Información**. El número de compilación es el mismo
que Ajustes muestra en *Acerca del dispositivo*.

El CID no está estandarizado: cada fabricante lo guarda en una propiedad distinta. La
app prueba las habituales (`ro.cid`, `ro.boot.cid`, `persist.sys.cid`…) y, si no da con
él, busca cualquier propiedad que termine en `cid` y te dice de cuál lo sacó. Si aun
así no aparece, búscalo desde la barra de comandos con `shell getprop | grep -i cid`.

Ojo con el serial: por red, `adb` devuelve la IP y el puerto en vez del número de
serie, así que la app sólo lo da por bueno cuando viene de una propiedad del equipo.

## Versiones de las apps instaladas

**Aplicaciones → Listar apps y versiones** saca cada paquete con su `versionName` y su
`versionCode`, en columna:

```
com.keesp.signage    1.0.0          (código 1)
com.spotify.music    8.7.60.842     (código 8100451)
```

Es una única llamada a adb: el bucle que recorre las apps se ejecuta dentro del
dispositivo, no una ida y vuelta por cada una. Aun así, en un móvil con muchas apps
tarda unos segundos — la barra de progreso avisa de que está trabajando.

**Listar TODAS** incluye las del sistema, que en una caja de señalización suelen ser
cientos.

## Buscar dispositivos en la red

**Red → Buscar dispositivos en la red...** explora tu red local buscando equipos con
ADB por WiFi escuchando (puerto **5555**, el que deja abierto `adb tcpip 5555` o el botón
**Habilitar ADB por WiFi**). Es lo que sirve para las cajas de señalización p291, que son
Android 9 y **no** aparecen por mDNS (eso es de Android 11+, y es lo que usa el emparejado).

Detecta la red de cada interfaz del PC (las `IP.0/24` que va a escanear se ven en la
consola) y sondea las 254 direcciones de cada una en paralelo, en **dos pasadas** (la
segunda rescata los equipos cuyo intento se perdió en la primera). Una sola subred tarda
unos segundos. Al terminar sale una ventana con los que encontró — los ya conectados vienen
marcados —; eliges cuáles y **los conecta todos de una** (`adb connect IP:5555`). Útil para
enchufar una flota entera sin ir IP por IP.

Por WiFi, hotspot o VPN un equipo puede tardar en responder; el sondeo espera **1,5 s** por
dirección. Si tus equipos siguen sin salir aunque estén encendidos y en la red, sube el
tiempo de espera en `config.json`:

```json
{ "scan_timeout": 3, "scan_workers": 256, "scan_pasadas": 2 }
```

- `scan_timeout` — segundos de espera por dirección (súbelo si tu red es lenta).
- `scan_workers` — cuántas direcciones sondea a la vez.
- `scan_pasadas` — número de barridos (más pasadas, más fiable pero más lento).

Sólo busca en la misma subred `/24` de cada interfaz del PC. Si tus equipos están en otra
red distinta, usa **Conectar por IP...**.

## Emparejar por WiFi (Android 11 o superior)

En Android 11 apareció "Depuración inalámbrica", y con ella `adb tcpip 5555` dejó de
bastar: hay que emparejar primero con un código de seis dígitos.

En el dispositivo: **Ajustes → Opciones de desarrollador → Depuración inalámbrica →
Vincular dispositivo con código**. Ese diálogo da una `IP:puerto` y el código.

La trampa está en que **ese puerto no es el de conexión**: sirve sólo para emparejar y
caduca en unos segundos. El de conexión es el que sale en la pantalla anterior. La app
lo busca sola por mDNS después de emparejar; si no lo encuentra, te lo pide.

Necesita platform-tools 30 o superior; si el tuyo es más viejo, te lo dice en vez de
fallar sin explicación.

## Permisos de una app

Muestra los permisos **de tiempo de ejecución** con un interruptor cada uno; encender
o apagar ejecuta `pm grant` / `pm revoke` al momento. Los de instalación no salen
porque no se pueden cambiar. Si el sistema rechaza el cambio, el interruptor vuelve a
su sitio y el motivo aparece en la consola.

## Progreso de las transferencias

Los `push`, `pull` e instalaciones muestran una barra bajo la consola con el porcentaje
real que va informando adb. Antes un archivo grande parecía dejar la app colgada.

## Control remoto

Para las cajas que se quedaron sin mando, y para no escribir una contraseña de WiFi
letra por letra con las flechas. Los botones mandan `input keyevent` y el campo de
texto manda `input text`.

Dos detalles: el texto que envías **no se escribe en la consola** (puede ser una
contraseña), sólo se informa de cuántos caracteres se mandaron; y `input text` sólo
maneja ASCII en la mayoría de ROMs, así que si el texto lleva tildes o eñes la app
te avisa antes de que salga mal.

## Consola ADB libre

Bajo la consola hay una barra de comandos: escribe cualquier cosa —
`shell getprop ro.serialno`, `connect 192.168.1.50:5555`, `shell dumpsys battery` —
y pulsa Enter. La salida cae en la consola de arriba.

- Puedes pegar la línea entera con el `adb` delante: se lo quita solo.
- `↑` y `↓` recuperan los comandos anteriores.
- Los comandos van contra el dispositivo seleccionado (`-s <serial>`), salvo los
  globales (`devices`, `connect`, `kill-server`…).
- Lo que no termina solo (`logcat` sin `-d`) se corta a los dos minutos, y te avisa.

## Extraer el APK instalado

`pm path` + `pull`: saca de la caja el APK exacto que está corriendo, con el nombre
del paquete y su versión (`com.keesp.signage-1.0.0.apk`). Si la app está partida en
varios APK (*split apks*) se los trae todos, porque hacen falta todos para
reinstalarla.

## Sección TV Box (signage p291)

Para las cajas Amlogic de cartelería digital, que se atienden por adb sobre WiFi.
Pierden el RTC, el reloj se les va a 2019 y con esa fecha **ningún certificado TLS
valida**: la app de señalización falla con `Unacceptable certificate`. No es el
certificado ni el servidor, es la hora.

Arriba hay una tarjeta con lo que cambia de equipo a equipo — resolución, densidad,
paquete de la app y servidor NTP. Se guarda en `config.json` y la línea
*"Se aplicará…"* muestra exactamente qué se le va a mandar al equipo.
El paquete viene como `com.keesp.signage`: cámbialo por el de tu app de
señalización la primera vez y se recordará.

| Botón | Qué hace |
|---|---|
| 🔧 **Fix completo** | Fecha + `hwclock -w` + NTP + resolución + reinicio de la app |
| 🕐 **Solo fecha y hora** | Pone la hora de este PC y **escribe el RTC**, para que sobreviva reinicios |
| 📺 **Solo resolución** | Salida HDMI + `wm size` + `wm density` con lo que diga la tarjeta |
| 🔎 **Diagnóstico del equipo** | Reloj y desfase, NTP, video, modos que acepta la TV, estado de la app, último arranque y errores de TLS en el logcat. Sólo lee |
| 🔄 **Reiniciar app de señalización** | `force-stop` y relanzar |

Requiere `adb root` (la ROM es `userdebug`); la app reconecta por TCP sola después de
cada `root`/`unroot`. Nunca usa `wm size/density reset` — en estas cajas eso *reinicia*
el equipo — y comprueba `disp_cap` antes de cambiar la salida HDMI, para no dejar la
pantalla en negro; sólo se la salta si marcas la casilla, y aun así lo avisa en la
consola. La salida HDMI no persiste al reinicio; el framebuffer sí.

> **Regla de oro:** ante cualquier `Unacceptable certificate` en estos boxes, compara
> primero la fecha del equipo con la real.

## Preparar TV Box (paso a paso)

La limpieza de una caja de señalización recién sacada de la caja, en siete pasos que
haces tú desde la app. Cada paso enseña antes lo que va a cambiar y espera tu
confirmación; nada se desinstala, todo se **desactiva** (`pm disable-user`) y se
deshace con **Restaurar desde una copia**.

### Antes de empezar

1. En la caja, con el mando: **Ajustes › Preferencias del dispositivo › Opciones para
   desarrolladores** › activa **Depuración USB** y, si sale, **Depuración por red**.
2. En la app: **Red / WiFi › Conectar por IP...** con la IP de la caja (o **Buscar
   dispositivos en la red...**) y elígela arriba, en el selector.
3. Si tienes Android Studio abierto, cierra su conexión (`adb disconnect <ip>:5555`):
   las RK322x sólo aceptan **una** conexión ADB a la vez.
4. Ten en el PC los archivos que vas a poner (no vienen con la app):
   - **Lanzador**: el APK de `com.gathin.tvhome`, para cajas Android 8 o superior.
   - **FLauncher**: `flauncher-0.18.0.apk` del GitLab oficial, para cajas Android 7.
     La app comprueba su SHA-256
     (`376fc528c880cdf7c7c04b2d3708c69f911144498218babb6300808b772af32e`) y, si no
     coincide, te pregunta antes de usarlo.
   - **Tema**: una carpeta con `config.json` y `wallpaper.jpg` para el lanzador.
   - **Señalización**: el APK de tu app.

   En la tarjeta de la página, **Elegir…** junto a cada uno. Se recuerdan para la
   siguiente caja, así que en una flota sólo se eligen la primera vez.

### Los pasos

**Asistente completo** los hace todos en orden. En cada uno que cambia algo pregunta:
**Sí** lo hace, **No** lo salta y sigue, **Cancelar** para el asistente. También puedes
pulsar cada paso suelto; si hace falta identificar antes el equipo, lo hace solo.

| Paso | Qué hace la app | Qué haces tú |
|---|---|---|
| **1 · Identificar equipo** | Lee `ro.product.device`, `ro.board.platform` y `ro.build.version.sdk` y elige el perfil. **Manda el SDK**: la ROM dice "Android 14" y miente. Avisa si `ro.adb.secure=0` y si hay un `su` setuid. Sólo lee | Mira en la tarjeta el modelo y el perfil |
| **2 · Copia de seguridad** | Guarda en una carpeta por equipo (`copias-tvbox\<modelo>_<serie>\<fecha>`) la lista de paquetes (`-f -u -i`, `-d`, `-e`, `-s`, `-3`), `getprop`, los ajustes global/secure/system, el Home y sus candidatos, `wm size` y `wm density`. Sólo lee | Nada. La carpeta lleva el número de serie: **no la compartas** |
| **3 · Desactivar bloatware** | Desactiva la lista del perfil con `pm disable-user --user 0`, **un paquete por llamada**, y lo comprueba con `pm list packages -d` (no se fía del código de salida). Antes apunta en la copia (`lista-aplicada.txt`) lo que va a desactivar | Confirmar |
| **4 · Lanzador y tema** | Android 8+: instala el lanzador, lo pone de Home (`set-home-activity`), lo arranca con `am start -W` y **sólo si queda en primer plano** desactiva el de serie; pulsa HOME y comprueba que sale el nuevo. Después sube el tema. Android 7: lo mismo con FLauncher, deja el fondo en `Pictures/fondo-tvbox.jpg` y abre la guía del mando | Confirmar. En Android 7, seguir la guía de FLauncher (abajo) |
| **5 · App de señalización** | La instala con push + `pm install -r` (`adb install` puede quedarse esperando una confirmación en la caja) y deja activo el explorador de archivos, para instalar APK desde un USB | Confirmar |
| **6 · Reiniciar y verificar** | Reinicia, espera a `sys.boot_completed`, compara los desactivados con la lista aplicada (por si el firmware reactiva algo al arrancar) y comprueba que Home sigue siendo el lanzador nuevo | Confirmar y esperar uno o dos minutos |
| **7 · Cerrar ADB y comprobar** | Te recuerda cerrar la depuración y, cuando lo hayas hecho, comprueba que el puerto 5555 **rechaza** la conexión | En la caja: Opciones para desarrolladores › desactiva Depuración USB y Depuración por red, reinicia, y responde **Sí** |

Si un paso falla, el asistente se para y la consola dice por qué; arréglalo y sigue con
el botón de ese paso. Un modelo **sin perfil** se queda en los pasos 1 y 2: inventario
(en una tabla) y copia de seguridad, sin desactivar nada.

### Modelos con perfil

| Perfil | Se reconoce por | Lanzador | Explorador de archivos |
|---|---|---|---|
| Amlogic p291 (S905L2) | `p291` · `p291` · SDK 28 (Android 9) | `com.gathin.tvhome`; el de serie (`com.droidlogic.mboxlauncher`) tiene prioridad 30 en su filtro HOME y `set-home-activity` dice *Success* sin cambiar nada, por eso se desactiva | `com.droidlogic.FileBrower`, se reactiva en el paso 5 |
| Rockchip RK322x (MXQ) | `rk322x_box` · `rk322x` · SDK 25 (Android 7.1) | FLauncher 0.18.0: el otro necesita SDK 26. El de serie es `com.ik.MXQ_Stick_MINI_8K` | `com.android.rockchip`, ya activo |

Qué se desactiva en cada uno:

- **p291**: limpiador de memoria, cajón de apps precargado, relleno de lanzador y
  salvapantallas, cola de impresión, SMS push y sincronización de contactos; las apps de
  sistema sospechosas (`com.abc.ninja`, con permisos para instalar, borrar y reiniciar),
  el test de fábrica `com.ftest`, recomendaciones, una app IPTV con SDK de publicidad y un
  receptor de cast; YouTube, Netflix, Prime Video, el ayudante de ratón de Netflix,
  Chrome (aquí el WebView es `com.android.webview`) y la búsqueda por voz; reproductor,
  galería y el actualizador OTA de este firmware `userdebug`.
- **RK322x**: limpiador de memoria, cola de impresión, sincronización de calendario y
  contactos, voz Pico; `com.yxotakeji.cdm` (arranca solo con permisos para instalar,
  reiniciar y **borrar de fábrica**), `com.oranth.accessibility`, la tienda del
  fabricante, Aptoide y el test de fábrica `com.DeviceTest`; YouTube, Netflix, Prime
  Video, IPTV, Kodi, AirPin, Miracast y DLNA; el centro multimedia y la música.
  **Chrome no se toca**: en esta caja es el proveedor de WebView.

### Salvaguardas

Van siempre, también con un perfil que alguien edite mal:

- **Nunca** `pm uninstall`, ni root, ni flasheo.
- Se rechaza entera, sin tocar nada, una lista con paquetes del núcleo de Android
  (permissioncontroller, packageinstaller, ext.services/shared, modulemetadata,
  overlay.modules, `com.android.providers.*` salvo calendario, contactos, diccionario y
  números bloqueados, systemui, shell, phone, settings, tv.settings, `android`): sin
  ellos la caja puede no volver a arrancar.
- No se desactiva al **dueño de Home** si nadie más responde a HOME.
- Se salta lo que pide `TV_INPUT_HARDWARE` (la capa bajo las entradas HDMI/AV) y el
  **proveedor de WebView**.
- Los paquetes de **fábrica** (`com.ftest`, `com.DeviceTest`…) se desactivan, pero la
  app nunca los arranca.
- Si tras pulsar HOME no sale el lanzador nuevo, se **reactiva** el de serie en el
  momento, para no dejar la caja sin Home.
- Sin copia de seguridad de esa caja, los pasos 3 y 4 no hacen nada.

### FLauncher: lo que sólo se hace con el mando

En las cajas Android 7 hay ajustes de FLauncher que no se pueden hacer por ADB. El
botón con el icono de documento, arriba a la derecha de la página, abre esta guía; el
paso 4 la abre solo:

1. **Fondo**: Ajustes de FLauncher › Wallpaper › Custom › `Pictures/fondo-tvbox.jpg`.
2. **Ocultar** Chrome, Descargas y el propio FLauncher: Ajustes › Applications › el ojo
   tachado. Chrome se oculta, no se desactiva.
3. **Categorías**: «Signage» arriba y «Herramientas» (explorador, Play Store, Ajustes).
   Una app nueva no sale sola: Applications › botón [+] › su categoría.
4. **Telemetría**: apaga *Crash Reporting* y *Analytics Reporting*.
5. Lo que se escriba por ADB va **sin tildes ni ñ**: en Android 7 `input text` no las
   admite. Se corrige con el mando en Categories › ⚙ › lápiz.

### Restaurar desde una copia

Con la depuración activada otra vez: **Restaurar desde una copia**, elige la carpeta de
la copia de esa caja (las de `copias-tvbox`, también en **Ajustes › Copias del TV Box ›
Abrir**). Reactiva con `pm enable`, uno por llamada, todo lo de su `lista-aplicada.txt`
—incluido el lanzador de serie— y devuelve el Home al de serie. Lo que ya venía
desactivado de fábrica se queda como estaba. Después reinicia la caja y vuelve a cerrar
la depuración.

Para reactivar **una sola** app basta la barra de comandos de abajo:
`shell pm enable com.google.android.youtube.tv`.

### Lo mismo con adb a mano

Por si toca hacerlo sin la app; es lo que ella manda, en el mismo orden (`<ip>` es la de
la caja, y cada `pm` va en su propia llamada):

```bat
adb connect <ip>:5555
adb -s <ip>:5555 shell getprop ro.product.device
adb -s <ip>:5555 shell getprop ro.build.version.sdk
adb -s <ip>:5555 shell pm list packages -f -u -i > paquetes-todos.txt
adb -s <ip>:5555 shell pm list packages -d > paquetes-deshabilitados.txt
adb -s <ip>:5555 shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME > home.txt
adb -s <ip>:5555 shell pm disable-user --user 0 com.charon.rocketfly
adb -s <ip>:5555 shell pm list packages -d
adb -s <ip>:5555 push lanzador.apk /data/local/tmp/lanzador.apk
adb -s <ip>:5555 shell pm install -r /data/local/tmp/lanzador.apk
adb -s <ip>:5555 shell cmd package set-home-activity --user 0 com.gathin.tvhome/.MainActivity
adb -s <ip>:5555 shell am start -W -n com.gathin.tvhome/.MainActivity
adb -s <ip>:5555 shell pm disable-user --user 0 com.droidlogic.mboxlauncher
adb -s <ip>:5555 shell input keyevent 3
adb -s <ip>:5555 shell "dumpsys activity activities | grep mResumedActivity"
adb -s <ip>:5555 reboot
adb -s <ip>:5555 shell getprop sys.boot_completed
```

Las listas completas de cada perfil están en `PERFILES_TVBOX`, al principio de
`adb_toolbox.py`. En Android 9 se mira `mResumedActivity`; `mFocusedApp` no existe.

## La interfaz

Barra de título y herramientas en una sola pieza arriba, barra lateral con las secciones
agrupadas, panel de contenido y consola abajo.

- La **barra de título de Windows** se pinta del color de la aplicación (Windows 11),
  para que la ventana se vea de una pieza.
- Las acciones de cada página van en una **lista agrupada**: una por fila, separadas por
  un filete, con el rojo para lo destructivo y el ámbar para los interruptores.
- En **Archivos**, el doble clic entra en la carpeta —o abre el XML en el editor.
  Mientras el equipo contesta —por WiFi son varios segundos— la lista enseña
  *Cargando…*, para que se vea que sí ha hecho caso.

- La **consola se pliega** con la flecha de su cabecera; plegada sigue mostrando la
  última línea, y la barra de comandos queda siempre a mano. Recuerda cómo la dejaste.
- El **engranaje** de arriba a la derecha abre **Ajustes**: rutas de adb y scrcpy,
  carpetas de salida y paquete de señalización, sin tener que editar el `config.json`.
- Al elegir una app (desinstalar, abrir, permisos, forzar detención, borrar datos,
  extraer APK, log de una app), la **elegida se marca en azul**, como la sección
  activa de la barra lateral, y el botón de la acción no se enciende hasta que
  hay una elegida.
- Los **listados salen en tabla** (ordenable pulsando la cabecera, con filtro y botón de
  copiar), no volcados a la consola.
- Cada página tiene **una sola acción principal** en color; el resto son botones neutros,
  con rojo para lo destructivo y ámbar para los interruptores.
- Los iconos están dibujados dentro del programa, así que se ven igual en cualquier
  Windows.
- La aplicación es **siempre oscura**: no sigue el tema de Windows, para que se vea
  igual en cualquier equipo del taller.

## Requisitos en el dispositivo Android

1. **Opciones de desarrollador** activadas.
2. **Depuración USB** activada.
3. Aceptar el diálogo *"¿Permitir depuración USB?"* al conectar por primera vez.

## ADB (platform-tools)

La app busca `adb.exe` automáticamente en:

- La ruta que configures (se guarda en `%USERPROFILE%\.adb_toolbox\config.json`)
- El `PATH` del sistema
- Ubicaciones comunes del SDK de Android (`%LOCALAPPDATA%\Android\Sdk\platform-tools`)
- La misma carpeta del ejecutable (puedes poner `adb.exe` junto al `.exe`)

Si no lo encuentra, pulsa **"Configurar ADB"** y selecciona tu `adb.exe`.
¿No tienes ADB? Descarga *SDK Platform-Tools* de Google y apunta a la carpeta descomprimida.

## Espejar la pantalla (scrcpy)

El botón **"🖥 Espejar en tiempo real (scrcpy)"** abre el dispositivo en una ventana del PC,
donde puedes verlo y controlarlo con ratón y teclado.

Requiere **scrcpy** (herramienta gratuita e independiente). La app lo busca automáticamente
(PATH, `C:\scrcpy`, scoop, chocolatey, o junto al `.exe`). Si no lo encuentra, te pedirá
localizar `scrcpy.exe`.

¿No lo tienes? Descárgalo de <https://github.com/Genymobile/scrcpy/releases>, descomprime el
ZIP y, al pulsar el botón, selecciona el `scrcpy.exe` de esa carpeta (se recordará).
La app usa su propio `adb` para lanzarlo y evitar conflictos de versión.

## Uso

1. Conecta el teléfono por USB.
2. Abre `ADB_Toolbox.exe`.
3. Pulsa **⟳** para detectar dispositivos y selecciónalo en la lista superior.
   - El punto se pone **verde** cuando hay un dispositivo activo.
4. Pulsa el botón de la acción deseada. La salida aparece en la **Consola** inferior.

Las capturas y grabaciones se guardan en `%USERPROFILE%\Pictures\ADB_Toolbox`.

## Tamaño de la ventana

Todas las páginas caben enteras en el tamaño por defecto (940x760). Si encoges la
ventana, la página que no quepa saca una barra de desplazamiento y la esconde sola en
cuanto vuelve a haber sitio, así que no se queda contenido inalcanzable.

## Pruebas

```bat
py -3 tests\run.py
```

No hace falta ningún dispositivo conectado: las pruebas levantan la aplicación y
sustituyen `adb` por un doble que registra qué comandos se le habrían mandado al
equipo. Comprueban, entre otras cosas, que las reglas de campo del TV Box siguen en pie
(nunca `wm size reset`, comprobar `disp_cap` antes de cambiar la salida de video) y que
ni el texto que envías al equipo ni el token de la app de señalización acaban escritos
en la consola.

Las de **Preparar TV Box** simulan una p291 y una RK322x con estado (paquetes,
prioridades del filtro HOME, reinicio, instalación por push) y comprueban cada
salvaguarda: nada se desinstala, un `pm` por llamada, la lista negra del núcleo, el
dueño de Home, `TV_INPUT_HARDWARE`, el WebView de la RK322x, que el lanzador de serie
sólo se desactiva con el nuevo en primer plano y que un modelo desconocido sólo hace
inventario y copia.

## Ejecutar desde el código

Necesitas Python 3 para Windows (probado con 3.14):

```bat
git clone https://github.com/Keespp/ADB-Toolbox.git
cd ADB-Toolbox
py -3 -m pip install -r requirements.txt
py -3 adb_toolbox.py
```

## Recompilar el ejecutable

Si modificas `adb_toolbox.py`:

```bat
build.bat
```

O manualmente:

```bat
py -3 -m pip install -r requirements.txt pyinstaller
py -3 -m PyInstaller --noconfirm --onefile --windowed --name ADB_Toolbox ^
  --collect-all customtkinter --collect-all PIL --exclude-module numpy adb_toolbox.py
```

El resultado queda en `dist\ADB_Toolbox.exe`.

## Notas

- Los comandos destructivos (desinstalar, borrar datos, apagar, reiniciar) piden **confirmación**.
- Si una app es **administrador de dispositivos**, la desinstalación normal falla
  (`DELETE_FAILED_DEVICE_POLICY_MANAGER`). En ese caso se le quita el permiso de
  administrador (`dpm remove-active-admin`) y se reintenta, avisando en la consola. Si la
  app es **propietario del dispositivo** (device owner), no se puede quitar por adb y se
  informa de ello.
- Cada comando se ejecuta en segundo plano; la interfaz no se congela.
- Copiar la captura al portapapeles usa el formato nativo de Windows (CF_DIB), así que puedes
  pegarla directamente en Paint, Word, chats, etc.

## Licencia

[MIT](LICENSE) © 2026 Keesp. Puedes usarlo, modificarlo y redistribuirlo libremente,
manteniendo el aviso de copyright.
