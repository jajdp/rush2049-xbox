#!/usr/bin/env python3
"""La carpeta de datos del contenedor: sin esto, el appx no enlaza.

El envoltorio de uwp\\main.cpp escribe la ruta de LocalFolder --lo que el Device Portal llama
LocalState-- en una variable global, y el frontend la lee en get_app_folder_path. Esa variable
la DEFINE este cambio, en RecompFrontend. Sin el, el enlace del appx muere con:

    main.obj : error LNK2019: unresolved external symbol recompui_uwp_data_path

Por que una variable global y no preguntarle a SDL: las bibliotecas del juego se compilan con el
SDL2 **de escritorio** (el FetchContent del CMakeLists del juego), cuyas cabeceras no declaran
SDL_WinRTGetFSPathUTF8 ni SDL_WINRT_PATH_LOCAL_FOLDER. El SDL de WinRT solo entra al enlazar el
appx, que es otra compilacion. Es la trampa 9 de docs/HOW-IT-WORKS.md.

Idempotente: si la variable ya esta, no toca nada.

Uso:  py -3.13 parche_data_path.py <arbol>
      El <arbol> es la raiz del checkout del juego, la que tiene lib/RecompFrontend.
"""
import sys
from pathlib import Path

DEFINICION = '''#ifdef _UWP
// La carpeta de datos del contenedor (LocalFolder), en UTF-8. La escribe el envoltorio de
// uwp\\main.cpp antes de entrar al juego, y se pasa por aqui y no preguntandole a SDL porque
// estas bibliotecas se compilan con el SDL2 **de escritorio** (el FetchContent del CMakeLists
// del juego), cuyas cabeceras no declaran SDL_WinRTGetFSPathUTF8 ni SDL_WINRT_PATH_LOCAL_FOLDER:
// el SDL de WinRT solo entra al enlazar el appx. Vacia, no se usa.
extern "C" char recompui_uwp_data_path[512] = {};
#endif
'''

USO = '''#ifdef _UWP
        // ⚠ Xbox Series (contenedor de aplicacion). Aqui no valen ninguno de los dos caminos de
        // abajo: FOLDERID_LocalAppData devuelve «…\\AC\\<id>», que el Device Portal no expone, de
        // modo que no habria forma de subir la ROM ni de leer la configuracion; y el modo
        // portatil tampoco sirve de rodeo, porque el driver de video WinRT de SDL cambia el
        // directorio de trabajo a la carpeta de instalacion, que es de solo lectura. La unica
        // carpeta que vale es LocalFolder, que es lo que el portal llama LocalState.
        if (recompui_uwp_data_path[0] != '\\0') {
            return std::filesystem::path{ recompui_uwp_data_path };
        }
#endif
'''


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    p = Path(sys.argv[1]) / 'lib' / 'RecompFrontend' / 'recompui' / 'src' / 'util' / 'file.cpp'
    if not p.is_file():
        print(f'  ERROR: no esta {p}')
        return 1
    t = p.read_text(encoding='utf-8')

    if 'recompui_uwp_data_path' in t:
        print('  file.cpp: ya estaba')
        return 0

    # 1. La definicion, junto al include de nfd (que el parche de la web condiciona).
    for ancla in ('#ifndef __EMSCRIPTEN__\n#include "nfd.h"\n', '#include "nfd.h"\n'):
        if t.count(ancla) == 1:
            t = t.replace(ancla, DEFINICION + ancla, 1)
            break
    else:
        print('  ERROR: no encuentro donde poner la definicion (el include de nfd.h)')
        return 1

    # 2. El uso, antes de que mire portable.txt: en el contenedor ese camino no sirve.
    ancla = '        // directly check for portable.txt'
    if t.count(ancla) != 1:
        print(f'  ERROR: «{ancla.strip()}» aparece {t.count(ancla)} veces')
        return 1
    t = t.replace(ancla, USO + ancla, 1)

    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(t, encoding='utf-8')
    tmp.replace(p)
    print('  file.cpp: parcheado')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
