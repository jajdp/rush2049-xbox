# Cómo funciona el port, y las doce trampas

*(English: [HOW-IT-WORKS.md](HOW-IT-WORKS.md))*

## La forma: dos compilaciones, no una

| | Qué se construye | Cómo |
|---|---|---|
| 1 | **El juego, como bibliotecas estáticas** | Ninja + clang-cl, como objetivo de **escritorio**, con `-DUWP_BUILD=ON` |
| 2 | **El appx** | El proyecto `uwp/`, con el generador de Visual Studio — el único proyecto `WindowsStore` de verdad |

**Por qué no una sola.** MSBuild solo ofrece el toolset `v143` para «Application Type = UWP», no
`ClangCL`, así que pedir `-T ClangCL` contra `WindowsStore` da `error MSB8020`. Y compilar el
juego con `cl.exe` tampoco vale: el ecosistema está escrito para clang — opciones `-Wno-*` en
ultramodern y recompinput, `C4146` convertido en error en rabbitizer.

Así que el juego se compila exactamente igual que para el escritorio, con clang-cl, y **lo que lo
vuelve UWP es la macro `_UWP`** que definen los parches, no el SDK de la Store. El proyecto del
appx enlaza los `.lib` resultantes y pone el punto de entrada.

## Qué hubo que cambiarle al juego

| Archivo | Cambio |
|---|---|
| `CMakeLists.txt` | La opción `UWP_BUILD`: define `_UWP`, convierte el ejecutable en biblioteca estática y deja fuera lo que es solo del `.exe` (opciones de enlazado, el icono `.rc`, el enlace con el SDL2 de escritorio y la copia de las DLL) |
| `src/main.cpp` | Bajo `_UWP`, `main()` pasa a ser `rush2049_uwp_main()` y se exporta con `extern "C"` |
| `src/main.cpp` | `SDL_INIT_HAPTIC` fuera, bajo la misma condición que el proyecto ya tenía para la compilación web |
| `uwp/` (nuevo) | `main.cpp`, `CMakeLists.txt`, `Package.appxmanifest`, `Assets/` y `patches/` |

Los tres los hace [`tools/parche_uwp_build.py`](../tools/parche_uwp_build.py), por anclas
exactas, y es idempotente.

## Las bibliotecas: este juego viaja gratis

El trabajo de plataforma es de **worleydl**, y lo que decide cuánto de él sirve es qué commits de
las bibliotecas fija el juego. Rush 2049 fija unos lo bastante cercanos a sus forks como para que
sus parches entren con `git apply --3way` y dejen **cuatro conflictos, todos del mismo tipo** —
que es la única razón por la que este port salió en una tarde en vez de en una semana.

| Biblioteca | Rush 2049 fija | Frente a los parches de worleydl |
|---|---|---|
| `rt64` | `5473732` | los parches UWP aplican con `--3way`, 2 conflictos |
| `N64ModernRuntime` | `cdf5abb` | 2 conflictos, los dos del tipo «quedarse con los dos lados» |
| `RecompFrontend` | `b2c5c18` | ningún conflicto |
| `N64Recomp-browser` | `14241d9` (v0.159.0) | la capa web; cada proyecto aplica la suya |

### Los cuatro conflictos, y por qué son todos el mismo

Los cuatro se resuelven **quedándose con los dos lados**, con el de worleydl bajo `#ifdef _UWP`
para que el árbol siga compilando para escritorio. Lo hace
[`tools/resolver_conflictos.py`](../tools/resolver_conflictos.py) — y como cada línea que casa
está en las bibliotecas, no hay nada suyo que sea de este juego.

| Archivo | Qué se hace |
|---|---|
| `rt64_application.cpp` | El `#include "hle/rt64_uwp_mods.h"` bajo `#ifdef _UWP`; `showing_inspector` se queda global, porque lo usan los dos caminos |
| `rt64_application_window.cpp` | ⚠ worleydl dejó un **`#if 0`** donde iba un `#ifdef`, y eso mata el camino de escritorio (`undefined symbol: uwp_GetRefreshRate`). Pasa a `#ifndef _UWP` |
| `addresses.hpp` | Tres ramas: `mem_size` en Emscripten, **512 MB** en UWP y 4 GB en escritorio |
| `recomp.cpp` | `uwp_ProcessEvents()` —su declaración y su llamada en el bucle de la interfaz— bajo `#ifdef _UWP` |

⚠ **Los 512 MB se investigaron y NO eran la causa de nada aquí.** Encajaban con el fallo que tuvo
parado este port una tarde: el heap pide `0x1F000000` sobre un offset de `0x01000000`, que son
justo esos 512 MB sin una página de guarda detrás. Se subieron a 4 GB, se recompiló y se
reinstaló, y **el fallo fue idéntico** — 4,16 s en vez de 3,92. El cambio se dejó puesto porque
es inocuo, pero la causa estaba en otro sitio: las opciones de vídeo.

## ⚠ Las cuatro cosas que costaron un intento cada una

### 1. El proyecto aplica 24 parches propios, y van primero

`tools/apply_runtime_patches.sh`, en el repositorio del juego, parchea los submódulos: primero el
soporte web de `N64Recomp-browser` y luego los `runtime-patches/` propios de este juego. Sin eso,
el código del juego llama a cosas que las bibliotecas no tienen:

```text
ultramodern::set_vi_rate
common/rt64_gpu_timings.h
```

Es el mecanismo del propio proyecto y vive en el repositorio del propio proyecto; nada de este
repositorio lo sustituye. `compilar.ps1` solo lo ejecuta, como paso `runtime`.

⚠ **Tiene que correr antes que los parches de worleydl.** El script averigua cuáles de sus
parches están ya aplicados revirtiéndolos, del más nuevo al más viejo, sobre una copia aparte —y
se detiene antes de tocar un submódulo que tenga otros cambios encima—. Si se aplican antes los
UWP, se niega a funcionar.

Esos 24 parches merecen además una lectura si anda detrás de un fallo gráfico: `rt64-0008`
implementa `G_CULLDL`, que el RT64 de origen trata como una no-operación, y `rt64-0005` es el que
dice qué pasa cuando una textura no está en la caché — *«undefined to read, whatever a driver
does with it»*. Esa frase es la explicación entera del fallo del estadio de Stunt de más abajo.

### 2. Dónde están las anclas, y por qué la herramienta no toma más que el árbol

`main()` está en `src/main.cpp`, no bajo `src/main/`. Y el bloque del ejecutable de escritorio del
`CMakeLists.txt` llega más lejos de lo que uno espera: además del `POST_BUILD` de las DLL y del
enlace con el SDL2 de escritorio, incluye el icono `.rc` y `/SUBSYSTEM:WINDOWS` — y todo eso tiene
que quedar fuera de una compilación como bibliotecas estáticas. Las dos cosas son de **este**
`CMakeLists.txt` y de **este** `main.cpp`, así que
[`parche_uwp_build.py`](../tools/parche_uwp_build.py) toma el árbol y ningún otro argumento: no
hay nada que parametrizar.

### 3. El nombre de la ROM no lleva versión

El runtime guarda la ROM como `<game_id>.z64`, y el `game_id` de este juego es
`rush2049.n64.us` a secas, así que el archivo es **`rush2049.n64.us.z64`** — sin `1.0`, sin
sufijo, sin nada. Otros proyectos sobre este mismo runtime sí le ponen versión, que es justo por
lo que vale la pena decirlo. Si se equivoca, el launcher se queda en «Load ROM» sin una palabra
en el registro.

### 4. El clon deja submódulos a medias

`git clone --recurse-submodules` dejó seis vacíos —`json`, `plainargs`, `spirv-cross`, `stb`,
`xxHash`, `zstd`— **sin dar error**, y el configure murió mucho después con *«does not contain a
CMakeLists.txt file»*. `compilar.ps1` repite `submodule update --init --recursive` hasta que
ninguna carpeta de `lib/rt64/src/contrib` quede vacía.

## Las doce trampas

| # | Qué pasa |
|---|---|
| 1 | **`patches/` necesita un clang con backend MIPS.** El clang-cl de Visual Studio no lo tiene; el clang de CLANG64 de MSYS2 sí |
| 2 | ⚠ **Pero el enlazador no puede ser LLD 22**: ya no acepta `-nostdlib`, que es lo que pasa `patches/Makefile`. LLD 19 sí |
| 3 | ⚠ **`vcvars64.bat` rehace el `PATH` y deja fuera el git de Windows.** El git de MSYS2 responde en rutas Unix y el configure muere en una fusión a tres bandas. Hay que volver a poner `C:\Program Files\Git\cmd`, explícitamente, antes que MSYS2 |
| 4 | ⚠ **`clone --recurse-submodules` deja submódulos a medias, en silencio.** Repetir hasta que ninguno esté vacío |
| 5 | **`git apply --3way` quiere el estado en el índice**: `add -A` antes… y `reset` después |
| 6 | **Un símbolo duplicado entre el parche y el juego** (`osPfsIsPlug_recomp`). Gana el del juego |
| 7 | **`AddVectoredExceptionHandler` no está declarado para UWP** — `error C3861`. Hay que declararlo a mano |
| 8 | ⚠ **`recompui_uwp_data_path` no está en ningún parche de worleydl.** Nada se queja hasta que enlaza el appx, al final del todo: `LNK2019` |
| 9 | ⚠ **`SDL_INIT_HAPTIC` no existe en el SDL de WinRT**, y `SDL_Init` devuelve -1 **para todo el conjunto**, así que la ventana no llega a crearse |
| 10 | ⚠ **El modo portable no sirve para esquivar la carpeta de datos.** `FOLDERID_LocalAppData` devuelve una carpeta que el Device Portal no expone; tiene que ser `LocalFolder` |
| 11 | ⚠ **El nombre del archivo de la ROM aquí no lleva versión.** Nombre equivocado, «Load ROM» en silencio |
| 12 | ⚠ **Los parches propios del proyecto van antes que los de worleydl**, o su script se niega a correr |

## ⚠ Las opciones de vídeo, que es donde se fue el tiempo de verdad

Tres opciones del propio juego no pueden quedarse encendidas, y averiguarlo costó dos rondas de
medición porque **la primera usó pruebas demasiado cortas**.

| Qué estaba encendido | Cómo muere |
|---|---|
| `hires_font` | Excepción de C++ sin capturar `0xE06D7363` a los **4,06 s** |
| `hires_title` | La misma excepción a los **4,03 s** |
| `res_option=Auto` **+** `msaa_option=MSAA2X` | `0xC0000005 … (read 0x0000000000000000)` a los **21,19 s** |

Las dos opciones `hires` fallan **igual**, en el mismo punto —justo después de cargar el overlay
1— y comparten mecanismo: las dos generan texturas en tiempo de ejecución y las registran en RT64
como un paquete de texturas integrado. Escribir sí escriben: las carpetas `hires_font\` y
`hires_title\` aparecen dentro de `LocalState`. Lo que revienta es cargarlas de vuelta.

La tercera es una excepción **de otra naturaleza**. Una lectura nula es la firma de una reserva
de memoria de GPU que falló y cuyo resultado nadie comprobó, y encaja: un framebuffer a la
resolución del televisor **por cada muestra de MSAA** es más de lo que concede el contenedor UWP.
Por separado, cada opción aguanta.

⚠ **Y esta es la lección de método.** Cada opción pasó una prueba de 40 segundos por su cuenta.
Con todas encendidas a la vez —menos las dos `hires`— el juego murió a los **15,2 s**. La prueba
corta estaba repartiendo aprobados falsos. Repitiéndola a 3 y 4 minutos, mirando cada 30 s, la
pareja culpable salió enseguida. **Tres minutos como mínimo, y probar el conjunto además de las
piezas**: los fallos de memoria de GPU son acumulativos y no se ven de a una.

### La cuarta opción, que no mata el juego: deja sin textura

`scenery_culling` es una opción del propio port, y `Off` es el ajuste más caro que hay: dibuja
**todos los objetos de escenario desde cualquier tramo de pista**, saltándose la tabla de
visibilidad del juego. En un escritorio eso cuesta fotogramas. En la consola produjo algo más
raro: en el **estadio de Stunt**, al saltar alto, aparecía una banda gris lisa sobre la grada que
se movía con la altura del coche.

Qué era, medido sobre capturas de las dos máquinas: la banda es un **color plano exacto,
(124,126,124)**, de unos 30 píxeles, justo donde el PC dibuja la celosía del techo con su
textura. O sea que a la geometría no le faltaba nada: **se estaba dibujando una superficie sin su
textura**. Que es lo que describe `rt64-0005`: un hueco de textura es *«undefined to read,
whatever a driver does with it»*. El driver de D3D12 del GDK pinta ese gris; el del escritorio
no.

**Y la parte que merece guardarse:** el mismo mod y el mismo ejecutable corrían en las dos
máquinas, así que la diferencia no podía ser el mod — era carga. `Off` más un mod que reescribe
memoria en cada retrace era más de lo que la consola tenía de margen, y cuando la geometría
lejana aparecía de golpe sus texturas ya no estaban en la caché. Poner `scenery_culling` en
`Original` lo arregló **con el mod todavía encendido**. Un fallo gráfico que solo sale en la
consola casi nunca es «la consola».

## El proyecto envoltorio

No está en este repositorio — deriva del de worleydl. Lo que tiene que hacer:

| Pieza | Por qué |
|---|---|
| `WinMain` → `SDL_WinRTRunApp` | El hilo es del contenedor; SDL crea la `CoreWindow` y después llama a `rush2049_uwp_main` |
| La carpeta de datos por `LocalFolder` | Trampa 10: es la única que expone el Device Portal |
| `AddVectoredExceptionHandler` declarado a mano | Trampa 7 |
| Los subsistemas de SDL levantados uno a uno | Para que uno que falla no se lleve a los demás — trampa 9 |
| Un archivo de registro propio | El `stderr` del contenedor es un fail-fast: sin esto no hay ningún mensaje de caída |

## Los dos interruptores, y el contador de FPS

Dos archivos opcionales en `LocalState` hacen posible probar sin mando:

| Archivo | Qué hace |
|---|---|
| `autoarranque.txt` | El envoltorio añade `--boot`, el interruptor de desarrollo del propio proyecto: entra a la ROM en el primer fotograma del launcher |
| `fps.txt` | Un contador, si le añadió uno, arranca encendido |

El contador **no está en este repositorio**: es una herramienta de diagnóstico, no una parte del
port, y nunca se midió como una de las piezas de aquí. En su lugar van todas las decisiones que
lleva dentro — suficiente para escribirlo en una tarde, que vale la pena, porque sin un contador
no hay forma de saber si un cambio sirvió de algo.

| Decisión | Por qué |
|---|---|
| Engancharlo en el `draw_hook` de `RecompFrontend` | Es el único punto que corre una vez por fotograma **presentado**: RT64 lo llama con el framebuffer del swap chain, justo antes de presentar |
| No contar los fotogramas del juego | Ese número casi no se movería. RT64 interpola hasta la tasa de la pantalla, y lo que hay que saber es qué llega a la pantalla |
| Pintar con `clearColor` y rectángulos | Rectángulos de color sólido sobre el framebuffer activo: sin pipeline, sin shaders, sin texturas, sin nada que haya que portar. Con dígitos de siete segmentos sobra, y se ven igual en el PC y en la consola |
| Llamar antes a `setFramebuffer` | Sin ningún menú abierto no hay framebuffer puesto, y `clearColor` actúa sobre el activo. El propio renderizador de la interfaz hace lo mismo antes de dibujar |
| Ponerlo en **R3**, leído directo de SDL | El mando de N64 no tiene ese botón, así que no lo usa ni el juego ni el frontend — y leer SDL directamente, en vez de pasar por el mapeo de acciones, no se lo quita a nadie |
| Darle además un interruptor por archivo (`fps.txt`) | ⚠ En la consola no hay forma de pulsar R3 desde el Device Portal, y subir un archivo cuesta segundos. Hay que buscarlo en la **carpeta de datos**, no en el directorio de trabajo: el juego se cambia a su carpeta de instalación, que en una consola es de solo lectura. La de datos es `LocalState`, que es la que expone el portal |
