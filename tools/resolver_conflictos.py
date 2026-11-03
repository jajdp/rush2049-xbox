#!/usr/bin/env python3
"""Resuelve los cuatro conflictos del parche UWP de worleydl sobre Mario Party.

Son todos del mismo tipo: el lado «ours» trae el soporte de la pagina web (bloques
__EMSCRIPTEN__) que worleydl no tenia, y el lado «theirs» trae el cambio de plataforma.
Hay que quedarse con LOS DOS, condicionando el de worleydl a _UWP para que el mismo arbol
siga compilando tambien para escritorio -- que es lo primero que pide la receta: sin el
camino de PC no hay donde comparar un fallo grafico.

Uso:  py -3.13 resolver_conflictos.py <arbol>
"""
import sys
from pathlib import Path

RESOLUCIONES = [
    # (archivo, texto con los marcadores, texto resuelto)
    (
        'lib/rt64/src/hle/rt64_application.cpp',
        '''<<<<<<< ours
#if defined(__EMSCRIPTEN__)
#   include <emscripten/threading.h>
#   include "plume_device_thread.h"
#endif
=======
#define UWP_SHADERS 1
#include "hle/rt64_uwp_mods.h"
bool showing_inspector = false;
>>>>>>> theirs
''',
        '''#if defined(__EMSCRIPTEN__)
#   include <emscripten/threading.h>
#   include "plume_device_thread.h"
#endif

#ifdef _UWP
#   define UWP_SHADERS 1
#   include "hle/rt64_uwp_mods.h"
#endif
// Fuera del #ifdef: el inspector lo usa en los dos caminos (lineas 751 y 755).
bool showing_inspector = false;
''',
    ),
    (
        'lib/rt64/src/hle/rt64_application_window.cpp',
        '''<<<<<<< ours
#   if defined(__EMSCRIPTEN__)
        // A page can't ask the display. The swap chain times the browser's animation frames instead (displayTiming),
        // and the present queue takes the smaller of the two rates.
        refreshRate = UINT32_MAX;
#   elif defined(_WIN32)
=======
#   if defined(_WIN32)
// DLW: Snag refresh rate from libuwp
#if 0
>>>>>>> theirs
''',
        '''#   if defined(__EMSCRIPTEN__)
        // A page can't ask the display. The swap chain times the browser's animation frames instead (displayTiming),
        // and the present queue takes the smaller of the two rates.
        refreshRate = UINT32_MAX;
#   elif defined(_WIN32)
// DLW: Snag refresh rate from libuwp
// ⚠ worleydl dejo aqui un «#if 0», que mata el camino de escritorio: el enlace del PC falla
// con «undefined symbol: uwp_GetRefreshRate». Va condicionado a _UWP.
#ifndef _UWP
''',
    ),
    (
        'lib/N64ModernRuntime/librecomp/include/librecomp/addresses.hpp',
        '''<<<<<<< ours
#ifdef __EMSCRIPTEN__
    // A 32-bit address space can't reserve 4 GiB, and WebAssembly memory has no page protection to catch stray
    // accesses with anyway.
    constexpr size_t allocation_size = mem_size;
#else
    constexpr size_t allocation_size = 4096ULL * 1024ULL * 1024ULL;
#endif
=======
    // DLW: Trimmed to 512MB, 4k 4x MSAA is memory hungry
    constexpr size_t allocation_size = 512ULL * 1024ULL * 1024ULL;
>>>>>>> theirs
''',
        '''#ifdef __EMSCRIPTEN__
    // A 32-bit address space can't reserve 4 GiB, and WebAssembly memory has no page protection to catch stray
    // accesses with anyway.
    constexpr size_t allocation_size = mem_size;
#elif defined(_UWP)
    // DLW: Trimmed to 512MB, 4k 4x MSAA is memory hungry
    constexpr size_t allocation_size = 512ULL * 1024ULL * 1024ULL;
#else
    constexpr size_t allocation_size = 4096ULL * 1024ULL * 1024ULL;
#endif
''',
    ),
    (
        'lib/N64ModernRuntime/librecomp/src/recomp.cpp',
        '''<<<<<<< ours
std::string current_game_mode_id;
=======
extern "C" __declspec(dllimport) void uwp_ProcessEvents();

>>>>>>> theirs
''',
        '''std::string current_game_mode_id;

#ifdef _UWP
// De libuwp: bombea los eventos de la CoreWindow desde el bucle de la interfaz.
extern "C" __declspec(dllimport) void uwp_ProcessEvents();
#endif

''',
    ),
    (
        'lib/N64ModernRuntime/librecomp/src/recomp.cpp',
        '''        ultramodern::sleep_milliseconds(1);
        uwp_ProcessEvents();
''',
        '''        ultramodern::sleep_milliseconds(1);
#ifdef _UWP
        uwp_ProcessEvents();
#endif
''',
    ),
]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    arbol = Path(sys.argv[1])
    fallos = 0
    for rel, viejo, nuevo in RESOLUCIONES:
        p = arbol / rel
        t = p.read_text(encoding='utf-8')
        if viejo not in t:
            if nuevo.split('\n')[0] in t and '<<<<<<<' not in t:
                print(f'  ya resuelto: {rel}')
            else:
                print(f'  ERROR: no encuentro el conflicto en {rel}')
                fallos += 1
            continue
        t = t.replace(viejo, nuevo, 1)
        tmp = p.with_suffix(p.suffix + '.tmp')
        tmp.write_text(t, encoding='utf-8')
        tmp.replace(p)
        print(f'  resuelto: {rel}')

    # Comprobacion final: que no quede ningun marcador.
    for rel in {r for r, _, _ in RESOLUCIONES}:
        t = (arbol / rel).read_text(encoding='utf-8')
        for marca in ('<<<<<<<', '=======\n', '>>>>>>>'):
            if marca.strip() in t and marca != '=======\n':
                print(f'  ⚠ quedan marcadores en {rel}')
                fallos += 1
                break
    return 1 if fallos else 0


if __name__ == '__main__':
    raise SystemExit(main())
