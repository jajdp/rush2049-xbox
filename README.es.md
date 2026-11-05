# San Francisco Rush 2049 en Xbox — el port UWP

Cómo llevar **San Francisco Rush 2049: Recompiled**
([`n64hub/rush-2049-recomp`](https://github.com/n64hub/rush-2049-recomp)) — una recompilación
estática sobre **N64Recomp + RT64** — a una **Xbox Series X en modo desarrollador**.

*(English: [README.md](README.md))*

**El trabajo de plataforma no es de este repositorio.** Los forks UWP de RT64, N64ModernRuntime
y RecompFrontend son de [**worleydl**](https://github.com/worleydl), y este juego fija commits de
las bibliotecas lo bastante cercanos a los suyos como para que sus parches entren dejando
**cuatro conflictos y ninguna otra cosa**, los cuatro del mismo tipo. Esa es la razón entera de
que este port saliera en una tarde. Lo que añade este repositorio es lo que hubo que cambiar
**para este juego**: sus tres cambios de código, el orden en que van los parches, los ajustes de
vídeo que la consola aguanta y el registro de lo que salió mal.

⚠ **Ojo con el nombre.** Este es *San Francisco Rush 2049* (2000), **no** *Rush 2: Extreme Racing
USA* (1998). Otro juego, otro proyecto de recompilación y otro autor — si viene buscando *Rush
2*, esta no es la receta.

## En qué consola se probó

**Una Xbox Series X**, en modo desarrollador. Las dos consolas donde se compiló y se probó son
Series X, así que es el único hardware que cubre lo de aquí.

**Una Series S no se ha probado nunca, ni una vez.** Es otra máquina: menos memoria disponible
para un juego y una GPU más floja. Puede que funcione, puede que vaya más lento o puede que ni
arranque; aquí no se ha medido nada sobre ella.

## Hasta dónde llega este port

Construido desde la **v0.1.46** del juego. Medido en una Xbox Series X el 2026-11-02, con la
vuelta completa a Circuit confirmada el 2026-11-05:

| | |
|---|---|
| ✅ Arranca, dibuja y responde al mando | Paquete «Rush 2049 Recomp» 0.1.0.3, instalado por el Device Portal |
| ✅ **Jugado de punta a punta**, con mando en la mano | Las seis pistas de Circuit terminadas, y el estadio de Stunt con sus saltos: no solo la demo de atracción |
| ✅ **56–60 FPS** | Medidos con un contador pintado sobre el fotograma, en **R3**. El juego no trae ninguno; este es una herramienta de diagnóstico y está descrito en [`docs/HOW-IT-WORKS.es.md`](docs/HOW-IT-WORKS.es.md), no incluido aquí |
| ✅ El launcher sale | Start Game / Controls / Settings / Mods / Exit |
| ✅ La ROM se valida sola | Desde `LocalState`, sin ningún diálogo |
| ✅ **Los mods cargan**, el menú de trucos incluido | [Hotwire 2049](https://github.com/Deozaan/Rush2049RecompCheatsMod) pone CHEATS en el menú principal |
| ⚠ Tres opciones de vídeo tienen que quedarse apagadas | Matan el juego o estropean el escenario — la tabla de abajo |

**Lo que NO se afirma aquí:** que todos los modos funcionen. Las seis pistas de Circuit se han
recorrido de punta a punta en la consola; **Ghost Race, Battle y los modos de pantalla partida
no se han medido allí en absoluto.**

## ⚠ Las opciones de vídeo que esta consola aguanta

Es la parte que más costó y la que más conviene saber antes de empezar. Hay que dejar cuatro
opciones en paz; **todo lo demás puede quedarse encendido, la alta resolución incluida**, que es
la que de verdad se nota.

```jsonc
// LocalState\graphics.json  — tools/graphics-xbox.json es este archivo, listo para subir
"res_option":      "Auto",       // ✅ la resolución del televisor
"msaa_option":     "None",       // ❌ el suavizado NO cabe junto a la alta resolución
"hires_font":      "Off",        // ❌ mata el juego a los 4 s
"hires_title":     "Original",   // ❌ mata el juego a los 4 s
"scenery_culling": "Original",   // ❌ «Off» tampoco le cabe — ver abajo
// y todo lo demás encendido:
"ar_option": "Expand", "menu_ratio": "Expand", "game_frame_rate": "60",
"input_lag": "Reduced", "draw_distance": "Far", "level_of_detail": "High"
```

| Opción | Qué pasa en la consola |
|---|---|
| `hires_font`, `hires_title` | Excepción de C++ sin capturar (`0xE06D7363`) **a los 4 segundos**, justo después de cargar el overlay 1. Las dos generan texturas en tiempo de ejecución y las registran en RT64 como un paquete de texturas integrado |
| `res_option=Auto` **+** `msaa_option=MSAA2X` | Lectura nula (`0xC0000005 … read 0x0000000000000000`) **a los 21 segundos**: un framebuffer a la resolución del televisor *por cada muestra de MSAA* es más de lo que el contenedor concede. Por separado, cada una aguanta |
| `scenery_culling=Off` | No mata el juego: **deja sin textura**. En el estadio de Stunt, al saltar alto, sale una banda gris lisa sobre la grada. `Off` dibuja todos los objetos de escenario desde cualquier tramo de pista, y cuando la geometría lejana aparece de golpe sus texturas ya no están en la caché. Un hueco de textura es *«undefined to read, whatever a driver does with it»*, y el driver del GDK lo pinta gris donde el del escritorio no |

⚠ **Y la lección de método, que es la parte reutilizable:** una prueba de 40 segundos no sirve
para dar por buena una opción de vídeo. Las dos `hires` mueren a los 4 s, pero res+MSAA tarda
21 s, y con todo encendido a la vez el juego murió a los 15 s. Hay que probar **al menos 3
minutos** y, cuando cada pieza pasa por separado, **probar también el conjunto**: los fallos de
memoria de GPU son acumulativos y no se ven de a una.

## Qué es este repositorio

**Una receta, no un producto.** Aquí no hay ROM, ni código recompilado, ni ejecutable, ni
`.msix` — y es a propósito, no un olvido.

| Pieza | Qué es |
|---|---|
| [`tools/compilar.ps1`](tools/compilar.ps1) | **La receta entera**, en siete pasos que se pueden repetir de uno en uno: ROM, parches del proyecto, parches UWP, recompilar, la compilación de escritorio, bibliotecas estáticas, appx |
| [`tools/parche_uwp_build.py`](tools/parche_uwp_build.py) | Los tres cambios que necesita **el juego mismo**: la opción `UWP_BUILD`, renombrar `main()` y `SDL_INIT_HAPTIC`. Por anclas exactas, idempotente. ⚠ **Las anclas son las de este juego**, y por eso no toma más argumento que el árbol |
| [`tools/resolver_conflictos.py`](tools/resolver_conflictos.py) | Los cuatro conflictos que dan los parches UWP de worleydl. Lo que casa está en las bibliotecas, no en el juego, así que resolvió este árbol sin tocarlo |
| [`tools/parche_data_path.py`](tools/parche_data_path.py) | Define `recompui_uwp_data_path`. **Sin él el appx no enlaza** |
| [`tools/graphics-xbox.json`](tools/graphics-xbox.json) | Los ajustes de arriba, listos para subir a `LocalState` |
| [`docs/HOW-IT-WORKS.es.md`](docs/HOW-IT-WORKS.es.md) | Las dos compilaciones, lo que este juego hace distinto, y las trampas |
| [`docs/INSTALL.es.md`](docs/INSTALL.es.md) | Lo que hace falta, las órdenes, y cómo meterlo en la consola |

El juego es **GPL-3.0**, así que su código se puede citar y los cambios que se le hacen están
publicados aquí. Qué se cita, cuánto y de dónde está medido en [`NOTICE.es.md`](NOTICE.es.md).

## Las dos cosas que hay que entender antes de intentarlo

**1. El generador de Visual Studio NO sirve para las bibliotecas del juego.** MSBuild solo tiene
el toolset `v143` para «Application Type = UWP», no `ClangCL`, así que `-T ClangCL` con
`WindowsStore` da `error MSB8020`; y con `cl.exe` se cae el ecosistema entero, que está escrito
para clang. El camino bueno es **Ninja + clang-cl**, con las bibliotecas como objetivo de
**escritorio**: lo que las vuelve UWP es la macro `_UWP` que definen los parches. El único
proyecto `WindowsStore` de verdad es el del appx.

**2. El trabajo de plataforma sale de los forks de worleydl**, no de aquí: `rt64-dev` (rama
`uwp-dk64`), `N64ModernRuntime-dev` (`uwp-rebase`), `RecompFrontend-dev` (`uwp-compat`) y el
paquete [`worleydl/uwp-dep`](https://github.com/worleydl/uwp-dep), **rama `rt64`**.

**Los commits que fija este juego** son lo que decide cuánto del trabajo de worleydl sale gratis,
así que son lo primero que hay que mirar en cualquier árbol que se vaya a parchear. Si coinciden,
todo lo de abajo vale tal como está escrito; si no, los conflictos estarán en otro sitio.

| Biblioteca | Commit que fija | Frente a los parches UWP de worleydl |
|---|---|---|
| `rt64` | `5473732` | entran con `--3way`, **2 conflictos** |
| `N64ModernRuntime` | `cdf5abb` | **2 conflictos**, los dos de «quedarse con los dos lados» |
| `RecompFrontend` | `b2c5c18` | ninguno |
| `N64Recomp-browser` | `14241d9` (v0.159.0) | la capa web; este proyecto la parchea él mismo, en el paso `runtime` |

## ⚠ Las cuatro cosas que costaron un intento fallido cada una

Ninguna está en los parches de worleydl ni en el README del juego: son lo que hubo que averiguar
aquí:

| | En qué consiste |
|---|---|
| 1 | **Hay que correr `tools/apply_runtime_patches.sh` antes de compilar, y antes que los parches de worleydl.** El proyecto aplica **24 parches propios** a sus submódulos —la capa web primero y luego los suyos— y sin ellos el código del juego llama a cosas que las bibliotecas no tienen (`ultramodern::set_vi_rate`, `common/rt64_gpu_timings.h`). Su script averigua lo ya aplicado revirtiéndolo, así que se niega a correr sobre un submódulo que tenga otros cambios encima |
| 2 | **Dónde están las anclas.** `main()` está en `src/main.cpp`, no bajo `src/main/`, y el bloque del ejecutable de escritorio del `CMakeLists.txt` llega más lejos de lo que uno espera: además de copiar las DLL y enlazar con el SDL2 de escritorio, incluye el icono `.rc` y `/SUBSYSTEM:WINDOWS`. Todo eso tiene que quedar fuera de la compilación como bibliotecas, y por eso `parche_uwp_build.py` es de este árbol |
| 3 | ⚠ **El nombre de la ROM en `LocalState` no lleva versión.** El runtime la guarda como `<game_id>.z64`, y aquí el `game_id` es `rush2049.n64.us` a secas: el archivo es **`rush2049.n64.us.z64`** — sin `1.0`, sin sufijo, sin nada. Con cualquier otro nombre el launcher se queda en «Load ROM» sin decir por qué |
| 4 | **`git clone --recurse-submodules` se dejó seis submódulos a medias** (`json`, `plainargs`, `spirv-cross`, `stb`, `xxHash`, `zstd`), sin avisar, y el configure murió después con *«does not contain a CMakeLists.txt file»*. Hay que repetir `git submodule update --init --recursive` hasta que ninguna carpeta de `lib/rt64/src/contrib` quede vacía |

## Lo que no es

No hay **ROM**, ni código recompilado, ni ejecutable, ni appx, ni arte del juego. Tampoco los
parches de worleydl —están en sus repositorios—, ni el paquete UWP, ni el proyecto envoltorio
`uwp/`, que deriva del suyo. Ni el contador de FPS: es una herramienta de diagnóstico y no una
parte del port, así que [`docs/HOW-IT-WORKS.es.md`](docs/HOW-IT-WORKS.es.md) explica cómo
funciona y dónde engancha —con detalle suficiente para escribirlo— en vez de distribuirlo. Lo que
hay aquí es la receta, las cuatro herramientas, los ajustes de vídeo que funcionan y el registro
de lo que salió mal.

## Créditos y licencia

**Casi nada de lo que hace que esto funcione es nuestro.** Este repositorio es una receta que une el trabajo de otros; sin cualquiera de estas piezas no habría port.

| Qué hace | Quién lo hizo | Licencia |
|---|---|---|
| **[rush-2049-recomp](https://github.com/n64hub/rush-2049-recomp)** — recompila *San Francisco Rush 2049* | **n64hub** | GPL-3.0 |
| **[uwp-dep](https://github.com/worleydl/uwp-dep)** — Dawn, SDL3, nod y dxcompiler **compilados para UWP**: la única razón por la que algo de esto corre en una Xbox | **Daniel Worley** (worleydl) | libuwp: zlib, © 2025 |
| **[N64ModernRuntime](https://github.com/N64Recomp/N64ModernRuntime)** — el runtime sobre el que corren esas recompilaciones | the **N64Recomp** project | GPL-3.0 |
| **[RecompFrontend](https://github.com/N64Recomp/RecompFrontend)** — los menús y la configuración dentro del juego | the **N64Recomp** project | GPL-3.0 |
| **[N64Recomp](https://github.com/N64Recomp/N64Recomp)** — recompila estáticamente juegos de N64 a ejecutables nativos | **Mr-Wiseguy** and the N64Recomp project | MIT |
| **[rt64](https://github.com/rt64/rt64)** — el renderizador de N64, con sus mejoras | the **RT64** project | MIT |
| **[SDL](https://github.com/libsdl-org/SDL)** — ventana, mando y audio | **Sam Lantinga** and the SDL contributors | zlib |

Mención especial a **Daniel Worley**: las compilaciones UWP de `uwp-dep` son lo que hace posible este port a Xbox. No las hicimos nosotros, las usamos.

**La receta de empaquetado, las herramientas y esta documentación** son de **Recompilaciones**.


Receta y herramientas de **Recompilaciones**, bajo la **[GPL-3.0](LICENSE)** — la licencia del
proyecto del juego que esta receta parchea,
[`n64hub/rush-2049-recomp`](https://github.com/n64hub/rush-2049-recomp), y la de
[N64ModernRuntime](https://github.com/N64Recomp/N64ModernRuntime) y
[RecompFrontend](https://github.com/N64Recomp/RecompFrontend), de los que las resoluciones de
conflictos citan líneas. [N64Recomp](https://github.com/N64Recomp/N64Recomp) y
[RT64](https://github.com/rt64/rt64) son MIT. Los forks UWP sobre los que construye la receta son
de **worleydl**. El mod de trucos que se nombra arriba es de **Deozaan** y no se distribuye aquí.

El proyecto del juego está **escrito por IA** y lo dice él mismo; lo dirige y lo prueba una
persona. Es lo que declaran sus autores, no una afirmación de aquí.

*San Francisco Rush 2049* es © Atari Games / Midway. Este proyecto no está afiliado con ellos,
ni con Microsoft, ni con los autores de N64Recomp, RT64, el proyecto del juego o los forks UWP.
Titulares de derechos: **jajdpmail@gmail.com**.
