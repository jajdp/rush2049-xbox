#!/usr/bin/env python3
"""Los tres cambios que el juego necesita para la compilacion UWP.

Mismo arreglo que en los forks UWP de worleydl y en los ports de Mario Party de la casa:
  - con -DUWP_BUILD=ON el juego produce BIBLIOTECAS ESTATICAS en vez de un .exe, y define
    _UWP, que es lo que enciende los parches de plataforma (no el SDK de la Store);
  - lo que es solo del ejecutable de escritorio (las opciones de enlazado, el icono .rc, el
    enlace con el SDL2 de escritorio y la copia de las DLL) queda fuera;
  - main() pasa a llamarse rush2049_uwp_main() y se exporta, para que uwp\\main.cpp la llame
    despues de que SDL cree la CoreWindow.

⚠ Las anclas son las de ESTE arbol y no valen para otro juego de la familia, que reparte sus
archivos de otra forma:

  - main() vive en src/main.cpp, no en src/main/main.cpp;
  - el comentario del bloque WIN32 del CMakeLists esta redactado distinto;
  - el bloque del ejecutable de escritorio llega mas lejos: ademas del POST_BUILD de las DLL y
    del enlace con SDL2, incluye el icono .rc y las opciones /SUBSYSTEM:WINDOWS.

Uso:  py -3.13 -X utf8 parche_uwp_build.py <arbol>
      p. ej.  C:\\rush2049\\src

El <arbol> es la raiz del checkout del juego, la que tiene CMakeLists.txt y src\\main.cpp.
No hay ninguna ruta por defecto a proposito: el argumento es obligatorio.

Es idempotente: pasarlo dos veces no cambia nada la segunda.
"""
import sys
from pathlib import Path

OBJETIVO = 'Rush2049Recompiled'
PREFIJO = 'rush2049'


def escribir(p: Path, texto: str) -> None:
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(texto, encoding='utf-8')
    tmp.replace(p)


def parchear_cmake(arbol: Path) -> bool:
    p = arbol / 'CMakeLists.txt'
    t = p.read_text(encoding='utf-8')
    if 'UWP_BUILD' in t:
        print('  CMakeLists: ya estaba')
        return True

    # 1. La opcion, justo despues del bloque WIN32 que ya existe al principio.
    ancla = ('# Opt out of the constexpr mutex constructor on Windows to avoid vcredist issues.\n'
             'if (WIN32)\n'
             '    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR")\n'
             'endif()\n')
    if t.count(ancla) != 1:
        print(f'  ERROR: el bloque WIN32 del principio aparece {t.count(ancla)} veces')
        return False
    nuevo = ancla + '''
# Xbox Series / Windows Store: el juego se construye como bibliotecas estaticas y uwp\\ las enlaza
# en el appx. Lo que vuelve UWP a este codigo es la macro _UWP, no el SDK de la Store: MSBuild no
# tiene toolset ClangCL para «Application Type = UWP» (solo v143), asi que -T ClangCL da MSB8020,
# y con cl.exe se cae el ecosistema entero, escrito para clang.
option(UWP_BUILD "Solo bibliotecas estaticas; el ejecutable sale del proyecto uwp/." OFF)
if (UWP_BUILD)
    add_compile_definitions(_UWP)
endif()
'''
    t = t.replace(ancla, nuevo)

    # 2. El objetivo: ejecutable en escritorio, biblioteca estatica en UWP.
    ancla = f'add_executable({OBJETIVO})\n'
    if t.count(ancla) != 1:
        print(f'  ERROR: «add_executable({OBJETIVO})» aparece {t.count(ancla)} veces')
        return False
    t = t.replace(ancla, f'''# El ejecutable (una biblioteca estatica en la compilacion UWP: el punto de entrada lo pone uwp/).
if (NOT UWP_BUILD)
    add_executable({OBJETIVO})
else()
    add_library({OBJETIVO} STATIC)
endif()
''')

    # 3. Lo que es solo del ejecutable de escritorio: desde el POST_BUILD de las DLL hasta las
    #    opciones de enlazado, el icono .rc incluido.
    ancla = f'    add_custom_command(TARGET {OBJETIVO} POST_BUILD'
    i = t.find(ancla)
    if i < 0:
        print('  ERROR: no encuentro el POST_BUILD de las DLL')
        return False
    fin_marca = f'    target_link_options({OBJETIVO} PRIVATE /SUBSYSTEM:WINDOWS /ENTRY:mainCRTStartup)\n'
    j = t.find(fin_marca, i)
    if j < 0:
        print('  ERROR: no encuentro el target_link_options de escritorio')
        return False
    j += len(fin_marca)
    bloque = t[i:j]
    sangrado = '\n'.join(('    ' + l) if l.strip() else l for l in bloque.rstrip('\n').split('\n'))
    t = t[:i] + ('''    # Las DLL, el icono .rc, el SDL2 de escritorio y las opciones de enlazado son del .exe, que
    # la compilacion UWP no produce: alli los pone uwp/CMakeLists.txt desde el paquete de worleydl.
    if (NOT UWP_BUILD)
''' + sangrado + '''
    endif()
''') + t[j:]

    escribir(p, t)
    print('  CMakeLists: parcheado')
    return True


def parchear_main(arbol: Path) -> bool:
    p = arbol / 'src' / 'main.cpp'
    t = p.read_text(encoding='utf-8')
    if '_uwp_main' in t:
        print('  main.cpp: ya estaba')
        return True
    ancla = 'int main(int argc, char** argv) {\n'
    if t.count(ancla) != 1:
        print(f'  ERROR: «int main(...)» aparece {t.count(ancla)} veces')
        return False
    t = t.replace(ancla, f'''#ifdef _UWP
// En UWP el ejecutable es el envoltorio de uwp/: es suyo el WinMain, entrega el hilo al modelo de
// aplicacion WinRT de SDL (que crea la CoreWindow) y despues llama a esto.
extern "C" int {PREFIJO}_uwp_main(int argc, char** argv) {{
#else
int main(int argc, char** argv) {{
#endif
''')
    escribir(p, t)
    print('  main.cpp: parcheado')
    return True


def parchear_sdl(arbol: Path) -> bool:
    """SDL_INIT_HAPTIC fuera en UWP: el SDL de WinRT no trae vibracion y SDL_Init devuelve -1
    para TODO el conjunto, asi que el juego ni llega a crear la ventana."""
    p = arbol / 'src' / 'main.cpp'
    t = p.read_text(encoding='utf-8')
    if '|| defined(_UWP)' in t:
        print('  SDL_INIT: ya estaba')
        return True
    viejo = ("    // Emscripten's SDL2 is built without haptics, and asking for them there fails the whole call, gamepads with it.\n"
             "    // Nothing uses them: rumble goes through SDL_JoystickRumble.\n"
             "#ifdef __EMSCRIPTEN__\n")
    if t.count(viejo) != 1:
        print(f'  ERROR: el bloque de SDL_INIT aparece {t.count(viejo)} veces')
        return False
    nuevo = ("    // Emscripten's SDL2 is built without haptics, and asking for them there fails the whole call, gamepads with it.\n"
             "    // Nothing uses them: rumble goes through SDL_JoystickRumble.\n"
             "    // The same is true of SDL for WinRT (the Xbox package): «SDL not built with haptic (force feedback)\n"
             "    // support», and SDL_Init returns -1 for the lot, so the window is never created.\n"
             "#if defined(__EMSCRIPTEN__) || defined(_UWP)\n")
    escribir(p, t.replace(viejo, nuevo))
    print('  SDL_INIT: parcheado')
    return True


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    arbol = Path(sys.argv[1])
    ok = parchear_cmake(arbol) and parchear_main(arbol) and parchear_sdl(arbol)
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
