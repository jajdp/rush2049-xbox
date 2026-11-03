# Aviso

*(English: [NOTICE.md](NOTICE.md))*

## Sin afiliación

Este proyecto no está afiliado con **Atari Games** ni con **Midway**, titulares de los derechos
de *San Francisco Rush 2049*; ni con **Microsoft**; ni con los autores de
[N64Recomp](https://github.com/N64Recomp/N64Recomp), [RT64](https://github.com/rt64/rt64),
[N64ModernRuntime](https://github.com/N64Recomp/N64ModernRuntime),
[RecompFrontend](https://github.com/N64Recomp/RecompFrontend), el proyecto del juego
[`n64hub/rush-2049-recomp`](https://github.com/n64hub/rush-2049-recomp), los forks UWP de
**worleydl** o el mod de trucos de **Deozaan**; ni cuenta con su respaldo. Aquí no se vende nada
ni se pide nada a cambio.

## Qué no se distribuye aquí

- **Ni ROM, ni datos del juego, ni arte del juego.** La ROM la pone cada cual; la receta no
  descarga ninguna y este repositorio nunca contuvo una.
- **Ningún código recompilado.** El C que el recompilador saca de la ROM es obra derivada de la
  ROM y se queda en la máquina que lo construyó.
- **Ni ejecutable ni paquete.** Ni `.exe`, ni `.msix`, ni `.appx`.
- **Nada de arte.** Los mosaicos del paquete no están aquí; el arte del juego, menos todavía.
- **Ninguno de los parches de worleydl**, ni su paquete de dependencias UWP. La receta los toma
  de sus repositorios.
- **Ningún proyecto envoltorio.** La carpeta `uwp/` que produce el appx deriva de la suya y
  pertenece a sus repositorios, no a este.
- **Ninguno de los 24 parches propios del proyecto del juego.** Están en su repositorio y la
  receta ejecuta el script del propio proyecto para aplicarlos.
- **Tampoco el mod de trucos.** [Hotwire 2049](https://github.com/Deozaan/Rush2049RecompCheatsMod)
  es obra de Deozaan; el README solo dice de dónde sacarlo y qué hace.

## Cuánto se cita de obra ajena, y por qué

Las herramientas de `tools/` funcionan casando **anclas exactas** en los árboles que parchean:
buscan un texto conocido y ponen otro en su lugar. Esas anclas son líneas de código ajeno, y la
única forma de publicar una herramienta que funcione es publicarlas.

**Cómo se midió.** De cada herramienta se extrajo todo literal de cadena y se partió línea por
línea, y cada línea se buscó **solo en los archivos que esa herramienta declara tocar**, para que
una línea genérica no se atribuya al archivo equivocado. De cada archivo se miraron dos
versiones: la que publica el proyecto (`HEAD`) y la que queda tras aplicar los parches UWP de
worleydl. Una línea que solo aparece en la segunda es el lado *«theirs»* de su parche: un fork
conserva la licencia de su original, así que esas líneas pertenecen al proyecto donde viven y se
listan bajo él.

| Proyecto | Licencia | Líneas citadas | Dónde |
|---|---|---|---|
| [`n64hub/rush-2049-recomp`](https://github.com/n64hub/rush-2049-recomp) | GPL-3.0 | **17** | `parche_uwp_build.py` — las anclas de `CMakeLists.txt` (13) y `src/main.cpp` (4) |
| [`rt64`](https://github.com/rt64/rt64) | MIT | **18** | `resolver_conflictos.py` — los marcadores de conflicto de `rt64_application.cpp` (9) y `rt64_application_window.cpp` (9) |
| [`N64ModernRuntime`](https://github.com/N64Recomp/N64ModernRuntime) | GPL-3.0 | **12** | `resolver_conflictos.py` — `addresses.hpp` (7) y `recomp.cpp` (5) |
| [`RecompFrontend`](https://github.com/N64Recomp/RecompFrontend) | GPL-3.0 | **3** | `parche_data_path.py` — las anclas de `recompui/src/util/file.cpp` |
| | | **50 en total** | |

De esas 50, **24 están en los proyectos tal como se publican** y 26 son el lado *«theirs»* de
los parches de worleydl dentro de `rt64` (17) y `N64ModernRuntime` (9). Algunas llevan por eso
sus comentarios (`// DLW: …`).

Todo lo que las herramientas **escriben** es propio de este proyecto y no está contado arriba.

`tools/graphics-xbox.json` no cita nada: es un archivo de ajustes, y cada valor suyo se midió en
la consola.

### Por qué dos de las herramientas no citan nada de este juego

`resolver_conflictos.py` y `parche_data_path.py` casan texto de las **bibliotecas** —`rt64`,
`N64ModernRuntime` y `RecompFrontend`— y no una sola línea del juego. Por eso todas las líneas
que se les atribuyen arriba son de esos tres proyectos, y por eso resolvieron este árbol sin un
solo cambio: de lo que dependen es de los commits de las bibliotecas que lista el README, no de
Rush 2049. Sus anclas se miden arriba contra **este** árbol, que es el único sobre el que aquí se
dice haber medido nada.

## El proyecto del juego está escrito por IA

[`n64hub/rush-2049-recomp`](https://github.com/n64hub/rush-2049-recomp) declara en su propio
README que está escrito por agentes de IA, dirigido y probado por una persona. Es lo que dicen
sus autores, y se repite aquí porque quien siga esta receta debe saber qué está construyendo; no
es un juicio sobre ello.

## Contacto

Si usted es titular de derechos sobre algo de lo anterior y quiere que se retire, escriba a
**jajdpmail@gmail.com** y se retirará.
