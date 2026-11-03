<#
.SYNOPSIS
    Construye el port UWP (Xbox Series X en modo desarrollador) de San Francisco Rush 2049:
    Recompiled.

.DESCRIPTION
    Dos compilaciones, como en los forks UWP de worleydl para la familia N64Recomp:

      1. el juego con -DUWP_BUILD=ON produce BIBLIOTECAS ESTATICAS en vez de un .exe, con
         Ninja + clang-cl y como objetivo de ESCRITORIO: lo que lo vuelve UWP es la macro _UWP
         que definen los parches, no el SDK de la Store;
      2. uwp\ las enlaza con el paquete SDL2/libuwp/dxc de worleydl y genera el appx, que es el
         unico proyecto WindowsStore de verdad.

    ⚠ Y una cosa que este juego hace distinto de Mario Party: antes de nada hay que correr el
    tools/apply_runtime_patches.sh DEL PROPIO PROYECTO, que aplica sus 24 parches a los
    submodulos. Sin ellos el codigo del juego llama a cosas que las bibliotecas no tienen
    (ultramodern::set_vi_rate, common/rt64_gpu_timings.h). Es el paso «runtime», y va ANTES que
    los parches UWP: ese script se detiene si el submodulo ya tiene otros cambios encima.

    El porque de cada decision, y las trampas, en docs\HOW-IT-WORKS.md.

    Cada paso se salta si ya esta hecho, asi que el guion se puede repetir.

.PARAMETER Arbol
    Carpeta de trabajo. OBLIGATORIA: con los submodulos y los dos builds pasa de 3 GB, asi que
    no vive dentro de este repositorio.

.PARAMETER Rom
    Tu ROM de San Francisco Rush 2049 (USA), SHA-1
    3f99351d7bb61656614bdb2aa1a90cfe55d1922c. OBLIGATORIA. Aqui no se distribuye ninguna.

.PARAMETER Version
    Etiqueta del juego que se clona. Se fija a proposito: el proyecto publica casi a diario y
    sin esto el arbol saldria distinto cada vez.

.PARAMETER Msys2
    MSYS2, entorno CLANG64: el unico clang con backend MIPS que hace falta para patches\, y el
    make que pide su Makefile. Trampa 1 de HOW-IT-WORKS.

.PARAMETER Lld19
    ld.lld.exe de un LLVM 19. ⚠ NO vale el de MSYS2 (LLD 22): ya no acepta «-nostdlib», que es
    lo que pasa patches\Makefile. Trampa 2 de HOW-IT-WORKS.

.PARAMETER ParchesUwp
    Carpeta con los .patch UWP de worleydl (rt64-uwp.patch, N64ModernRuntime-uwp.patch,
    RecompFrontend-uwp.patch). No se distribuyen aqui: estan en sus repositorios, y el README
    dice cuales.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tools\compilar.ps1 -Arbol C:\rush -Rom "C:\roms\rush2049.z64"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Arbol,
    [Parameter(Mandatory)][string]$Rom,
    [ValidateSet('todos', 'rom', 'runtime', 'parches', 'recompilar', 'pc', 'libs', 'appx')]
    [string]$Paso = 'todos',
    [string]$Version = 'v0.1.46',
    [string]$Repositorio = 'https://github.com/n64hub/rush-2049-recomp.git',
    [string]$Msys2 = 'C:\msys64',
    [string]$Lld19 = '',
    [string]$ParchesUwp = ''
)

$ErrorActionPreference = 'Stop'
$src = Join-Path $Arbol 'src'
$here = $PSScriptRoot
$objetivo = 'Rush2049Recompiled'

function Paso([string]$t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan }
function Hacer([string]$n) { $Paso -eq 'todos' -or $Paso -eq $n }

# bash: el de Git for Windows sirve para los dos scripts del proyecto que son de shell.
function Buscar-Bash {
    $bash = 'C:\Program Files\Git\bin\bash.exe'
    if (-not (Test-Path $bash)) { throw "No esta bash de Git for Windows en $bash" }
    return $bash
}

# --- el entorno de MSVC, que clang-cl necesita para INCLUDE/LIB del SDK -----------------------
function Import-EntornoVS {
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (-not (Test-Path $vswhere)) { throw 'No esta vswhere: instala Visual Studio con las herramientas de C++.' }
    $vs = & $vswhere -latest -products * -property installationPath
    $bat = Join-Path $vs 'VC\Auxiliary\Build\vcvars64.bat'
    if (-not (Test-Path $bat)) { throw "No esta vcvars64.bat en $bat" }
    $llvm = Join-Path $vs 'VC\Tools\Llvm\x64\bin'
    if (-not (Test-Path (Join-Path $llvm 'clang-cl.exe'))) {
        throw 'Falta clang-cl: instala «C++ Clang tools for Windows» en Visual Studio.'
    }
    cmd /c "call `"$bat`" > nul 2>&1 && set" | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$' -and $matches[1] -ne 'PSModulePath') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
        }
    }
    # clang-cl de VS al frente, y MSYS2 AL FINAL: si fuera al principio, su propio clang-cl
    # (que no es compatible con MSVC) ganaria la busqueda y la build principal se rompe.
    #
    # ⚠ Y el git de Windows ANTES que MSYS2, explicitamente. vcvars64 rehace el PATH entero y
    # deja fuera «C:\Program Files\Git\cmd», asi que el primer git que se encuentra es el de
    # MSYS2, que devuelve las rutas al estilo Unix (/c/...). Trampa 3 de HOW-IT-WORKS.
    $git = 'C:\Program Files\Git\cmd'
    $env:PATH = "$llvm;$git;$env:PATH;$Msys2\usr\bin;$Msys2\clang64\bin"
    Write-Host "  clang-cl: $(Join-Path $llvm 'clang-cl.exe')"
}

# --- 0. el arbol ------------------------------------------------------------------------------
if (-not (Test-Path $src)) {
    Paso "Clonando el juego en $Version"
    New-Item -ItemType Directory -Force $Arbol | Out-Null
    git clone --recurse-submodules $Repositorio $src
    git -C $src checkout --quiet $Version
}

# ⚠ Trampa 4: «clone --recurse-submodules» deja submodulos a medias SIN AVISAR, y el configure
# muere mucho despues con «does not contain a CMakeLists.txt file». Se repite hasta que ninguna
# carpeta de contrib quede vacia.
$contrib = Join-Path $src 'lib\rt64\src\contrib'
for ($i = 1; $i -le 5; $i++) {
    git -C $src submodule update --init --recursive --quiet
    $vacias = @()
    if (Test-Path $contrib) {
        $vacias = Get-ChildItem $contrib -Directory | Where-Object {
            -not (Get-ChildItem $_.FullName -Force -ErrorAction SilentlyContinue)
        }
    }
    if (-not $vacias) { break }
    Write-Host "  submodulos a medias ($($vacias.Count)), reintento $i : $($vacias.Name -join ', ')" -ForegroundColor Yellow
}

# --- 1. la ROM --------------------------------------------------------------------------------
# El proyecto trae su propio extractor, que escribe las dos copias que necesita en roms\.
if (Hacer 'rom') {
    Paso 'La ROM'
    if (-not (Test-Path -LiteralPath $Rom)) { throw "No esta la ROM: $Rom" }
    $sha1 = (Get-FileHash -LiteralPath $Rom -Algorithm SHA1).Hash.ToLower()
    Write-Host "  SHA-1 $sha1"
    if ($sha1 -ne '3f99351d7bb61656614bdb2aa1a90cfe55d1922c') {
        Write-Host '  OJO: no es la ROM USA que este port soporta.' -ForegroundColor Yellow
    }
    Push-Location $src
    try {
        py -3.13 -I tools\extract.py $Rom
        if ($LASTEXITCODE -ne 0) { throw "tools\extract.py fallo con $LASTEXITCODE" }
    }
    finally { Pop-Location }
    Get-ChildItem (Join-Path $src 'roms') -File | Select-Object Name, Length | Format-Table -AutoSize
}

# --- 2. los parches del propio proyecto -------------------------------------------------------
# ⚠ ANTES que los de worleydl: apply_runtime_patches.sh comprueba que puede revertir lo que ya
# hay, y se detiene si el submodulo tiene otros cambios encima. Esto es lo que en Mario Party
# hacia sellar.cmake, pero aqui el proyecto lo trae resuelto y explicito.
if (Hacer 'runtime') {
    Paso 'Los 24 parches propios del proyecto (apply_runtime_patches.sh)'
    $bash = Buscar-Bash
    $srcUnix = $src -replace '\\', '/'
    & $bash -c "cd '$srcUnix' && bash tools/apply_runtime_patches.sh"
    if ($LASTEXITCODE -ne 0) { throw "apply_runtime_patches.sh fallo con $LASTEXITCODE" }
}

# --- 3. los parches UWP -----------------------------------------------------------------------
# Tres cosas, en este orden: lo que necesita el juego mismo, los parches UWP de worleydl sobre
# los submodulos, y la resolucion de los cuatro conflictos que dan.
if (Hacer 'parches') {
    Paso 'Parcheando para UWP'

    Write-Host '  el juego (UWP_BUILD, el punto de entrada y SDL_INIT_HAPTIC):'
    py -3.13 -X utf8 (Join-Path $here 'parche_uwp_build.py') $src
    if ($LASTEXITCODE -ne 0) { throw 'parche_uwp_build.py fallo' }

    if ($ParchesUwp) {
        if (-not (Test-Path $ParchesUwp)) { throw "No esta la carpeta de parches: $ParchesUwp" }
        foreach ($n in 'rt64', 'N64ModernRuntime', 'RecompFrontend') {
            $lib = Join-Path $src "lib\$n"
            $parche = Join-Path $ParchesUwp "$n-uwp.patch"
            if (-not (Test-Path $parche)) { Write-Host "  OJO: falta $parche"; continue }
            # --3way pide que el estado este en el indice... y hay que deshacerlo despues.
            # Las dos mitades de la trampa 5.
            git -C $lib add -A | Out-Null
            $excluir = if ($n -eq 'rt64') { @('--exclude=src/contrib/plume') } else { @() }
            git -C $lib apply --3way --whitespace=nowarn @excluir $parche
            git -C $lib reset | Out-Null
            Write-Host "  $n : parche UWP aplicado (o ya estaba)"
        }
        Write-Host '  los cuatro conflictos:'
        py -3.13 -X utf8 (Join-Path $here 'resolver_conflictos.py') $src
        if ($LASTEXITCODE -ne 0) { throw 'resolver_conflictos.py fallo' }
    }
    else {
        Write-Host '  OJO: sin -ParchesUwp no se aplican los parches de plataforma.' -ForegroundColor Yellow
        Write-Host '       Estan en los repositorios de worleydl; ver docs\INSTALL.md.' -ForegroundColor Yellow
    }

    # La carpeta de datos del contenedor. Va aparte de los parches de worleydl porque NO es suya:
    # sin esto el appx no enlaza (LNK2019: recompui_uwp_data_path). Trampa 8 de HOW-IT-WORKS.
    Write-Host '  la carpeta de datos (LocalFolder):'
    py -3.13 -X utf8 (Join-Path $here 'parche_data_path.py') $src
    if ($LASTEXITCODE -ne 0) { throw 'parche_data_path.py fallo' }
}

Import-EntornoVS

# --- 4. traducir la ROM a C -------------------------------------------------------------------
if (Hacer 'recompilar') {
    Paso 'Traduciendo el codigo de la ROM (N64Recomp + RSPRecomp)'
    $bash = Buscar-Bash
    # bash -c (no -lc): el perfil de login rehace el PATH y se pierde el entorno de MSVC.
    $srcUnix = $src -replace '\\', '/'
    & $bash -c "cd '$srcUnix' && tools/recompile.sh -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl"
    if ($LASTEXITCODE -ne 0) { throw "recompile.sh fallo con $LASTEXITCODE" }
    $n = (Get-ChildItem (Join-Path $src 'RecompiledFuncs') -File -ErrorAction SilentlyContinue).Count
    Write-Host "  RecompiledFuncs: $n archivos"
}

# Los dos compiladores que pide patches\: MIPS de MSYS2, y el enlazador de LLVM 19 (trampas 1 y 2).
$mipsCC = Join-Path $Msys2 'clang64\bin\clang.exe'
if (-not $Lld19) {
    $cand = Get-ChildItem 'C:\', 'D:\', 'F:\' -Filter 'llvm-19*' -Directory -ErrorAction SilentlyContinue |
            ForEach-Object { Join-Path $_.FullName 'bin\ld.lld.exe' } | Where-Object { Test-Path $_ } |
            Select-Object -First 1
    if ($cand) { $Lld19 = $cand }
}
$patchesArgs = @()
if ((Test-Path $mipsCC) -and $Lld19 -and (Test-Path $Lld19)) {
    $patchesArgs = @("-DPATCHES_C_COMPILER=$mipsCC", "-DPATCHES_LD=$Lld19")
}
elseif (Hacer 'pc') {
    Write-Host '  OJO: sin clang de MSYS2 y ld.lld de LLVM 19, patches\ no compila.' -ForegroundColor Yellow
}

# --- 5. el ejecutable de escritorio -----------------------------------------------------------
# Primero el PC: sin el camino de escritorio no hay donde comparar un fallo grafico. En este port
# eso fue justo lo que resolvio el del estadio de Stunt (README, «scenery_culling»).
if (Hacer 'pc') {
    Paso 'Compilando para Windows (clang-cl + ninja)'
    $build = Join-Path $Arbol 'build-pc'
    cmake -S $src -B $build -G Ninja -DCMAKE_BUILD_TYPE=Release `
        -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl `
        @patchesArgs -DCMAKE_NINJA_CMCLDEPS_RC=OFF
    if ($LASTEXITCODE -ne 0) { throw 'cmake configure (pc) fallo' }
    ninja -C $build $objetivo
    if ($LASTEXITCODE -ne 0) { throw 'ninja (pc) fallo' }
    Write-Host "  $build\$objetivo.exe" -ForegroundColor Green
}

# --- 6. el juego como bibliotecas estaticas ---------------------------------------------------
# ⚠ Ninja + clang-cl, NO el generador de Visual Studio: MSBuild solo tiene el toolset v143 para
# «Application Type = UWP», asi que -T ClangCL da MSB8020, y con cl.exe se cae el ecosistema.
if (Hacer 'libs') {
    Paso 'Compilando el juego para UWP (bibliotecas estaticas)'
    $build = Join-Path $Arbol 'build-uwp'
    cmake -S $src -B $build -G Ninja -DCMAKE_BUILD_TYPE=Release -DUWP_BUILD=ON `
        -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl `
        @patchesArgs -DCMAKE_NINJA_CMCLDEPS_RC=OFF
    if ($LASTEXITCODE -ne 0) { throw 'cmake configure (uwp) fallo' }
    ninja -C $build
    if ($LASTEXITCODE -ne 0) { throw 'ninja (uwp) fallo' }
    $libs = (Get-ChildItem -Recurse $build -Filter *.lib).Count
    Write-Host "  $libs bibliotecas estaticas en $build" -ForegroundColor Green
}

# --- 7. el appx -------------------------------------------------------------------------------
if (Hacer 'appx') {
    Paso 'Generando el appx'
    $uwp = Join-Path $src 'uwp'
    if (-not (Test-Path (Join-Path $uwp 'CMakeLists.txt'))) {
        throw "No esta el proyecto envoltorio en $uwp. Deriva del de worleydl; ver docs\INSTALL.md."
    }
    $build = Join-Path $Arbol 'build-appx'
    # ⚠ La ruta se arma ANTES: «-DRECOMP_DIR=(Join-Path …)» lo parte PowerShell en dos
    # argumentos y cmake acaba viendo el directorio como posicional.
    $recompDir = Join-Path $Arbol 'build-uwp'
    cmake -S $uwp -B $build -G 'Visual Studio 17 2022' -A x64 "-DRECOMP_DIR=$recompDir"
    if ($LASTEXITCODE -ne 0) { throw 'cmake configure (appx) fallo' }
    # AppxPackageValidationEnabled=false: MSBuild rechaza imagenes de mas de 204.800 B con
    # APPX3207, que es una regla de la Tienda y no de la consola.
    cmake --build $build --config Release -- /p:AppxPackageValidationEnabled=false
    if ($LASTEXITCODE -ne 0) { throw 'MSBuild (appx) fallo' }
    Get-ChildItem -Recurse $build -Include *.appx, *.msix -ErrorAction SilentlyContinue |
        Select-Object FullName, Length | Format-Table -AutoSize
}

Write-Host "`nListo." -ForegroundColor Green
