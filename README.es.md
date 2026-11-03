# San Francisco Rush 2049 en Xbox — el port UWP

Cómo llevar **San Francisco Rush 2049: Recompiled**
([`n64hub/rush-2049-recomp`](https://github.com/n64hub/rush-2049-recomp)) — una recompilación
estática sobre **N64Recomp + RT64** — a una **Xbox Series X en modo desarrollador**.

*(English: [README.md](README.md))*

Es la misma receta publicada para los tres ports de Mario Party
([`marioparty-xbox`](https://github.com/jajdp/marioparty-xbox) y sus hermanos), y eso es
justamente lo bueno: el juego es del mismo autor y fija **los mismos tres commits de las
bibliotecas**, así que el trabajo de plataforma vale tal cual. Lo que sí hubo que cambiar para
este juego está más abajo, y es casi todo lo que añade este repositorio.

⚠ **Ojo con el nombre.** Este es *San Francisco Rush 2049* (2000). El otro port de Rush de este
catálogo, [`rush2-xbox`](https://github.com/jajdp/rush2-xbox), es *Rush 2: Extreme Racing USA*
(1998) — un juego distinto y de otro autor.

## En qué consola se probó

**Una Xbox Series X**, en modo desarrollador. Las dos consolas donde se compiló y se probó son
Series X, así que es el único hardware que cubre lo de aquí.

**Una Series S no se ha probado nunca, ni una vez.** Es otra máquina: menos memoria disponible
para un juego y una GPU más floja. Puede que funcione, puede que vaya más lento o puede que ni
arranque; aquí no se ha medido nada sobre ella.

## Hasta dónde llega este port

Construido desde la **v0.1.46** del juego. Medido en una Xbox Series X el 2026-11-02:

| | |
|---|---|
| ✅ Arranca, dibuja y responde al mando | Paquete «Rush 2049 Recomp» 0.1.0.3, instalado por el Device Portal |
| ✅ **Jugado de verdad**, con mando en la mano | El estadio de Stunt, con saltos incluidos: no solo la demo de atracción |
| ✅ **56–60 FPS** | El contador del propio juego, que este port añade en **R3** |
| ✅ El launcher sale | Start Game / Controls / Settings / Mods / Exit |
| ✅ La ROM se valida sola | Desde `LocalState`, sin ningún diálogo |
| ✅ **Los mods cargan**, el menú de trucos incluido | [Hotwire 2049](https://github.com/Deozaan/Rush2049RecompCheatsMod) pone CHEATS en el menú principal |
| ⚠ Tres opciones de vídeo tienen que quedarse apagadas | Matan el juego o estropean el escenario — la tabla de abajo |

**Lo que NO se afirma aquí:** que todas las pistas y todos los modos funcionen de punta a punta.
Lo medido es el arranque, el estadio de Stunt jugado con mando, los mods cargando y la tasa de
fotogramas.

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
| [`tools/compilar.ps1`](tools/compilar.ps1) | **La receta entera**, en seis pasos que se pueden repetir de uno en uno: ROM, parches del proyecto, recompilar, parches, bibliotecas estáticas, appx |
| [`tools/parche_uwp_build.py`](tools/parche_uwp_build.py) | Los tres cambios que necesita **el juego mismo**: la opción `UWP_BUILD`, renombrar `main()` y `SDL_INIT_HAPTIC`. Por anclas exactas, idempotente. ⚠ **Las anclas de este juego**, que no son las de Mario Party |
| [`tools/resolver_conflictos.py`](tools/resolver_conflictos.py) | Los cuatro conflictos que dan los parches UWP de worleydl. Byte a byte el publicado en `marioparty-xbox`: resolvió este árbol sin tocarlo |
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

**Y la buena noticia, que es por lo que este port salió en una tarde:** Rush 2049 fija
exactamente los mismos commits de las bibliotecas que Mario Party, así que los parches de
worleydl y las cuatro resoluciones de conflictos ya escritas valen sin tocar nada.

| Biblioteca | Rush 2049 | Mario Party |
|---|---|---|
| `rt64` | `5473732` | `5473732` ✓ |
| `N64ModernRuntime` | `cdf5abb` | `cdf5abb` ✓ |
| `RecompFrontend` | `b2c5c18` | `b2c5c18` ✓ |
| `N64Recomp-browser` | `14241d9` (v0.159.0) | `889b627` (v0.156.0) — distinto, pero cada proyecto aplica el suyo |

## ⚠ Lo que este juego hace distinto de Mario Party

Cuatro cosas, y cada una costó un intento fallido:

| | Qué cambia |
|---|---|
| 1 | **Hay que correr `tools/apply_runtime_patches.sh` antes de compilar.** El proyecto aplica **24 parches propios** a sus submódulos —la capa web primero y luego los suyos— y sin ellos el código del juego llama a cosas que las bibliotecas no tienen (`ultramodern::set_vi_rate`, `common/rt64_gpu_timings.h`). Es el equivalente del `sellar.cmake` de Mario Party en esta familia, pero explícito y más limpio — por eso **aquí no hay `sellar.cmake`** |
| 2 | **Otro reparto de archivos.** `main()` está en `src/main.cpp`, no en `src/main/main.cpp`, y el comentario del bloque `WIN32` está redactado distinto, así que `parche_uwp_build.py` necesita **anclas propias**. El bloque del ejecutable de escritorio llega además más lejos: incluye el icono `.rc` y `/SUBSYSTEM:WINDOWS` |
| 3 | ⚠ **El nombre de la ROM en `LocalState` no lleva versión.** El runtime la guarda como `<game_id>.z64`, y aquí el `game_id` es `rush2049.n64.us` a secas: el archivo es **`rush2049.n64.us.z64`**. El de Mario Party incluye un `.1.0`. Con el nombre equivocado el launcher se queda en «Load ROM» sin decir por qué |
| 4 | **`git clone --recurse-submodules` se dejó seis submódulos a medias** (`json`, `plainargs`, `spirv-cross`, `stb`, `xxHash`, `zstd`), sin avisar, y el configure murió después con *«does not contain a CMakeLists.txt file»*. Hay que repetir `git submodule update --init --recursive` hasta que ninguna carpeta de `lib/rt64/src/contrib` quede vacía |

## Lo que no es

No hay **ROM**, ni código recompilado, ni ejecutable, ni appx, ni arte del juego. Tampoco los
parches de worleydl —están en sus repositorios—, ni el paquete UWP, ni el proyecto envoltorio
`uwp/`, que deriva del suyo. Ni el parche del contador de FPS, que es un añadido de este
catálogo y vive con los proyectos de Mario Party para los que se escribió. Lo que hay aquí es la
receta, las cuatro herramientas, los ajustes de vídeo que funcionan y el registro de lo que salió
mal.

## Créditos y licencia

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
