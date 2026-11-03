# Construir el port y meterlo en la consola

*(English: [INSTALL.md](INSTALL.md))*

⚠ **Lea «Hasta dónde llega este port» y la tabla de opciones de vídeo del
[`README.es.md`](../README.es.md) antes de dedicarle una tarde a esto.** Tres de las opciones de
vídeo del juego tienen que quedarse apagadas, y una de ellas no mata el juego: deja sin textura
sin decir nada.

## 0. Dónde se escriben las órdenes

> **Dónde se escribe:** en **PowerShell** —pulse la tecla **Windows**, escriba `powershell` y
> pulse **Enter** sobre *Windows PowerShell*—, en una ventana **normal**: no hace falta
> «ejecutar como administrador», desde la carpeta de este repositorio.

**No hace falta administrador** — y en el paso del certificado, usar una ventana de
administrador lo **estropea**, porque el certificado acaba en la cuenta que ejecutó la orden.
**PowerShell 7 no es necesario**, y los ejemplos llevan `-ExecutionPolicy Bypass` porque un
Windows recién instalado se niega a ejecutar un `.ps1`.

Cómo saber si una orden funcionó: escriba `$?` justo después. Responde `True` o `False` sobre la
orden anterior.

## 1. Lo que hace falta antes

| | Para qué |
|---|---|
| **Visual Studio** con las herramientas de C++ y **C++ Clang tools for Windows** | El entorno de MSVC (`vcvars64`), **clang-cl**, **Ninja** y el appx. El año da igual; lo que importa es que exista `vcvars64.bat` y que `clang-cl.exe` esté en `VC\Tools\Llvm\x64\bin` |
| **Su ROM** de *San Francisco Rush 2049* (USA), SHA-1 `3f99351d7bb61656614bdb2aa1a90cfe55d1922c` | El recompilador la traduce a C. No hay soporte para otra región ni otra revisión |
| **MSYS2**, entorno CLANG64 | El único clang de aquí con **backend MIPS**, que es lo que necesita `patches/`, más `make` |
| **LLVM 19** (solo por `ld.lld.exe`) | ⚠ LLD 22 rechaza `-nostdlib`; ver la trampa 2 de [`HOW-IT-WORKS.es.md`](HOW-IT-WORKS.es.md) |
| **Los forks UWP de worleydl y su paquete `uwp-dep`, rama `rt64`** | SDL2 para WinRT, `libuwp`, freetype, dxil y dxcompiler, y los parches de plataforma |
| **Git y Python 3.13** | Clonar, parchear y las herramientas de aquí |
| **CMake 3.x** | ⚠ CMake 4 rechaza algunos submódulos de este proyecto |
| **Una Xbox Series X en modo desarrollador** y un certificado autofirmado | Instalar y firmar |
| **Unos 3 GB de disco** | El árbol, sus submódulos y dos compilaciones |

## 2. La receta

```powershell
powershell -ExecutionPolicy Bypass -File tools\compilar.ps1 -Arbol C:\rush -Rom "C:\roms\rush2049.z64"
```

Eso ejecuta todos los pasos en orden. Cada uno se puede repetir por separado, que es lo que
ayuda cuando algo falla a mitad:

| `-Paso` | Qué hace |
|---|---|
| `rom` | Ejecuta el `tools/extract.py` del propio proyecto, que escribe en `roms\` las dos copias que necesita |
| `runtime` | ⚠ **El paso que Mario Party no tiene.** El `tools/apply_runtime_patches.sh` del propio proyecto: sus 24 parches a los submódulos, la capa web primero y luego los suyos |
| `parches` | Los tres cambios del juego, los parches UWP de worleydl, las cuatro resoluciones de conflictos y la carpeta de datos |
| `recompilar` | `tools/recompile.sh`: traduce el MIPS de la ROM a C (N64Recomp) y el microcódigo de audio (RSPRecomp). **43 archivos** en `RecompiledFuncs\` |
| `pc` | El ejecutable de **escritorio**. Constrúyalo primero: sin una compilación de PC no hay con qué comparar un fallo gráfico — que es exactamente como se diagnosticó el del estadio de Stunt |
| `libs` | El juego **como bibliotecas estáticas**, con **Ninja y clang-cl** |
| `appx` | El único proyecto `WindowsStore` de verdad: enlaza las bibliotecas y produce el `.msix` |

⚠ **El paso `libs` no puede usar el generador de Visual Studio.** El porqué es la primera
sección de [`HOW-IT-WORKS.es.md`](HOW-IT-WORKS.es.md), y es lo único que hay que saber antes de
empezar.

⚠ **`runtime` va antes de `parches`, no después.** `apply_runtime_patches.sh` averigua cuáles de
sus parches están ya aplicados revirtiéndolos sobre una copia aparte, y se detiene antes de tocar
un submódulo que tenga otros cambios encima. Si aplica primero los de worleydl, se negará a
funcionar.

## 3. El proyecto envoltorio

Este repositorio **no** lleva `uwp/` — deriva del de worleydl y pertenece a sus repositorios.
Lo que tiene que contener, y por qué está cada pieza, se explica en
[`HOW-IT-WORKS.es.md`](HOW-IT-WORKS.es.md): un `WinMain` que llama a `SDL_WinRTRunApp`, la
carpeta de datos por `LocalFolder`, `AddVectoredExceptionHandler` declarado a mano, los
subsistemas levantados uno a uno, y un archivo de registro propio porque el `stderr` del
contenedor es un fail-fast.

⚠ Si parte del envoltorio de Mario Party, lo que hay que cambiar es el proyecto y el objetivo de
CMake, el punto de entrada (`rush2049_uwp_main`), la identidad y el nombre visible del paquete, y
**el nombre del archivo de la ROM** — que es el que muerde, porque aquí no lleva versión.

## 4. Instalarlo en la consola

### Antes de tocar nada: cómo tiene que estar la consola

- **En modo desarrollador**, con Dev Home instalado.
- **Encendida y con su perfil con la sesión iniciada.** ⚠ Sin ningún usuario conectado la
  consola **no lanza aplicaciones**.
- **En la misma red**, con su dirección a mano. El Device Portal escucha en el puerto **11443**
  por HTTPS y pide el usuario y la contraseña que puso en Dev Home.

Abra `https://<ip>:11443`. ⚠ El navegador avisará de que el certificado no es de fiar: es el de
la propia consola. Entre igualmente — en Edge y Chrome, **Opciones avanzadas** → **Continuar a…
(no seguro)**; en Firefox, **Avanzado** → **Aceptar el riesgo y continuar**. Después,
**Mis juegos y aplicaciones → Agregar**.

## 5. La ROM, los ajustes y los interruptores, dentro del paquete

⚠ **`LocalState` no existe hasta el primer arranque.** Si sube algo antes, el portal dice que no
encuentra la ruta. Así que: instalar, **abrir el juego una vez**, cerrarlo, y solo entonces subir
con el **Explorador de archivos** del portal:

| Archivo | Por qué |
|---|---|
| `rush2049.n64.us.z64` | ⚠ La ROM, con **exactamente** ese nombre — sin versión. Con cualquier otro, el launcher se queda en «Load ROM» y no dice por qué |
| `graphics.json` | El [`tools/graphics-xbox.json`](../tools/graphics-xbox.json), renombrado. Sin él, los valores por defecto matan el juego antes de 21 segundos |
| `fps.txt` *(opcional)* | El contador de FPS arranca encendido, que en una consola es la única forma de verlo sin un mando delante para pulsar **R3** |
| `autoarranque.txt` *(opcional)* | Entra directo a la ROM, para probar sin nadie delante de la consola |

## Si algo sale mal

| Síntoma | Causa |
|---|---|
| `does not contain a CMakeLists.txt file` en un configure | `clone --recurse-submodules` dejó submódulos a medias. Repita `git submodule update --init --recursive` hasta que ninguna carpeta de `lib/rt64/src/contrib` esté vacía |
| No encuentra `ultramodern::set_vi_rate` o `common/rt64_gpu_timings.h` | Se saltó el paso `runtime`: faltan los 24 parches propios del proyecto |
| `apply_runtime_patches.sh` se detiene diciendo que un parche no aplica | Se ejecutó **después** de los parches de worleydl. Parta de un checkout limpio de los submódulos y ejecútelo primero |
| `error MSB8020` al compilar las bibliotecas | Se usó el generador de Visual Studio: tiene que ser Ninja + clang-cl |
| `lld: error: unknown argument: -nostdlib` | `PATCHES_LD` es un LLD 22. Apúntelo a un `ld.lld.exe` de LLVM 19 |
| `does not match index` en `git apply --3way` | Haga `git add -A` en ese submódulo antes — y `git reset` después |
| `lld-link: error: duplicate symbol: osPfsIsPlug_recomp` | Están definidos el del parche y el del juego. Se queda el del juego |
| `error C3861: AddVectoredExceptionHandler` | No está declarado para UWP: decláraelo a mano en el envoltorio |
| `LNK2019: unresolved external symbol recompui_uwp_data_path` **al enlazar el appx** | No se ejecutó `tools/parche_data_path.py`. Es el único cambio que no está en ningún parche de worleydl, y nada se queja hasta el último paso |
| El enlace deja `uwp_PickMultipleFiles` sin resolver | El paquete UWP es de la rama equivocada: para esta familia es `rt64` |
| Arranca sin vídeo y se cuelga creando la ventana | `SDL_INIT_HAPTIC`: el SDL de WinRT no trae vibración y `SDL_Init` falla para todo el conjunto |
| El launcher se queda en «Load ROM» | El nombre de la ROM. Aquí es `rush2049.n64.us.z64`, sin versión |
| Muere a los ~4 s con `0xE06D7363` | Está encendido `hires_font` o `hires_title` |
| Muere a los ~21 s con `0xC0000005 … read 0x0000...0000` | La alta resolución **y** el MSAA, juntos |
| Una banda gris lisa sobre la grada al saltar en Stunt | `scenery_culling` está en `Off`. Póngalo en `Original` |
| El portal no encuentra la ruta al subir la ROM | `LocalState` no existe hasta el primer arranque (§5) |
| La consola responde `0x800B0100` | El `.msix` no está firmado (abajo) |

## Reinstalar: tres cosas que muerden

1. **MSBuild deja el appx sin firmar.** Fírmelo con un certificado autofirmado cuyo **sujeto sea
   exactamente el `Publisher` del manifiesto** — eso es lo que conserva el nombre de familia del
   paquete, así que la consola lo trata como una actualización y mantiene `LocalState`:
   `signtool sign /fd SHA256 /sha1 <huella> <msix>`.
2. ⚠ **Instalar la misma versión con distinto contenido se rechaza**, con `-2147009285`:
   *«the provided package has the same identity as an already-installed package but the contents
   are different»*. Suba antes el `Identity Version` del manifiesto, y ancle la expresión regular
   que lo hace (`\sVersion="…"`), porque `MinVersion` contiene `Version`. Desinstalar también lo
   resuelve, pero se lleva por delante `LocalState` y la ROM.
3. **Una caché de shaders escrita por una compilación anterior no sirve.** Borre
   `LocalState\shadercache\`; el juego la rehace.
