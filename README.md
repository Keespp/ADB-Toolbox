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
| 📦 **Aplicaciones** | Desinstalar APK, instalar APK, extraer el APK instalado, abrir una app, ver y cambiar sus permisos, **listar las apps con su versión** (solo las tuyas o todas, incluidas las del sistema), forzar detención, borrar datos |
| 📋 **Registros** | Extraer el logcat completo, el de una app concreta o sólo los errores; traer los registros que el equipo guarda en disco; generar el bugreport de Android; limpiar el buffer |
| 🛠️ **Desarrollador** | Límites de diseño, overdraw GPU, mostrar toques, ubicación del puntero, animaciones, no mantener actividades, permanecer activo al cargar, perfil de renderizado GPU (todos alternables ON/OFF) |
| ⚡ **Energía** | Reiniciar, recovery, bootloader, apagar, pantalla ON/OFF |
| 🌐 **Red** | Habilitar ADB por WiFi (puerto 5555), conectar por IP, **emparejar por WiFi (Android 11+)** |
| 📺 **TV Box** | Signage p291: fix completo, fecha y hora, resolución, diagnóstico, reiniciar la app — [ver abajo](#sección-tv-box-signage-p291) |

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
- Cada comando se ejecuta en segundo plano; la interfaz no se congela.
- Copiar la captura al portapapeles usa el formato nativo de Windows (CF_DIB), así que puedes
  pegarla directamente en Paint, Word, chats, etc.

## Licencia

[MIT](LICENSE) © 2026 Keesp. Puedes usarlo, modificarlo y redistribuirlo libremente,
manteniendo el aviso de copyright.
