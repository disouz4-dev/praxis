# Praxis — driver de áudio do macOS (PraxisAudio.driver)
# Licença MIT.
#
# Gera um "Audio Server Plug-in" (plug-in carregado pelo coreaudiod, o servidor
# de áudio do macOS) com dois dispositivos de laço: "Praxis Mic" e
# "Praxis Speaker". Use ./construir.sh em vez de chamar o CMake direto.

cmake_minimum_required(VERSION 3.16)

# Binário universal (Intel e Apple Silicon) e macOS mínimo. Precisam ser
# definidos antes de project().
if(NOT CMAKE_OSX_ARCHITECTURES)
  set(CMAKE_OSX_ARCHITECTURES "x86_64;arm64" CACHE STRING "Arquiteturas" FORCE)
endif()
if(NOT CMAKE_OSX_DEPLOYMENT_TARGET)
  set(CMAKE_OSX_DEPLOYMENT_TARGET "10.15" CACHE STRING "macOS mínimo" FORCE)
endif()

project(PraxisAudio CXX)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE "Release")
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ---------------------------------------------------------------------------
# Identidade do driver (não mudar sem motivo: o macOS e os apps guardam estes
# valores).

set(PRAXIS_DRIVER_NOME "PraxisAudio")
set(PRAXIS_DRIVER_ID "dev.disouz4.praxis.audio")
set(PRAXIS_DRIVER_VERSAO "1.0.0")
# Identificador da fábrica do plug-in (gerado uma vez com uuidgen).
set(PRAXIS_FABRICA_UUID "24624C93-A0AF-4B71-BD63-5B2A9285AD31")
# Função de fábrica exportada (fonte/PontoDeEntrada.cpp).
set(PRAXIS_FABRICA_FUNCAO "PraxisAudioFabrica")

# ---------------------------------------------------------------------------
# libASPL (MIT, https://github.com/gavv/libASPL), presa na versão v3.1.2.
# Baixada pelo git na primeira construção, dentro da pasta de construção.

set(LIBASPL_REPOSITORIO "https://github.com/gavv/libASPL.git"
  CACHE STRING "Endereço git da libASPL")
set(LIBASPL_VERSAO "47f688ed6bb637ab8b7f4b36864734b2b1f69b6b"
  CACHE STRING "Commit da libASPL (tag v3.1.2)")

set(LIBASPL_PREFIXO "${CMAKE_CURRENT_BINARY_DIR}/libASPL-prefixo")
set(LIBASPL_BIBLIOTECA "${LIBASPL_PREFIXO}/lib/libASPL.a")

string(REPLACE ";" "|" ARQUITETURAS_LISTA "${CMAKE_OSX_ARCHITECTURES}")

include(ExternalProject)
ExternalProject_Add(libASPL_externa
  GIT_REPOSITORY "${LIBASPL_REPOSITORIO}"
  GIT_TAG "${LIBASPL_VERSAO}"
  GIT_SHALLOW OFF
  UPDATE_DISCONNECTED ON
  SOURCE_DIR "${CMAKE_CURRENT_BINARY_DIR}/libASPL-fonte"
  BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/libASPL-construcao"
  INSTALL_DIR "${LIBASPL_PREFIXO}"
  LIST_SEPARATOR "|"
  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=<INSTALL_DIR>
    -DCMAKE_BUILD_TYPE=Release
    -DCMAKE_OSX_ARCHITECTURES=${ARQUITETURAS_LISTA}
    -DCMAKE_OSX_DEPLOYMENT_TARGET=${CMAKE_OSX_DEPLOYMENT_TARGET}
    -DCMAKE_OSX_SYSROOT=${CMAKE_OSX_SYSROOT}
  BUILD_BYPRODUCTS "${LIBASPL_BIBLIOTECA}"
  LOG_DOWNLOAD ON
  LOG_CONFIGURE ON
  LOG_BUILD ON
  LOG_INSTALL ON
)

add_library(libASPL STATIC IMPORTED)
set_target_properties(libASPL PROPERTIES IMPORTED_LOCATION "${LIBASPL_BIBLIOTECA}")
add_dependencies(libASPL libASPL_externa)
file(MAKE_DIRECTORY "${LIBASPL_PREFIXO}/include")
target_include_directories(libASPL INTERFACE "${LIBASPL_PREFIXO}/include")

find_library(BIBLIOTECA_CoreFoundation CoreFoundation REQUIRED)
find_library(BIBLIOTECA_CoreAudio CoreAudio REQUIRED)

set(AVISOS -Wall -Wextra -Wno-unused-parameter)

# ---------------------------------------------------------------------------
# Núcleo: dispositivos de laço (usado pelo driver e pelos testes).

add_library(praxis_nucleo STATIC
  fonte/DispositivoLaco.cpp
)
target_include_directories(praxis_nucleo PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/fonte")
target_link_libraries(praxis_nucleo PUBLIC libASPL ${BIBLIOTECA_CoreFoundation})
target_compile_options(praxis_nucleo PRIVATE ${AVISOS})
option(PRAXIS_DIAGNOSTICO "Liga o registro detalhado da libASPL no registro do sistema" OFF)
if(PRAXIS_DIAGNOSTICO)
  target_compile_definitions(praxis_nucleo PRIVATE PRAXIS_DIAGNOSTICO=1)
else()
  target_compile_definitions(praxis_nucleo PRIVATE PRAXIS_DIAGNOSTICO=0)
endif()
set_target_properties(praxis_nucleo PROPERTIES CXX_VISIBILITY_PRESET hidden)

# ---------------------------------------------------------------------------
# O driver: um "Mach-O bundle" dentro da pasta PraxisAudio.driver.

configure_file(Info.plist.in "${CMAKE_CURRENT_BINARY_DIR}/Info.plist" @ONLY)

add_library(${PRAXIS_DRIVER_NOME} MODULE
  fonte/PontoDeEntrada.cpp
)
target_link_libraries(${PRAXIS_DRIVER_NOME} PRIVATE praxis_nucleo)
target_compile_options(${PRAXIS_DRIVER_NOME} PRIVATE ${AVISOS})
# Exporta só a função de fábrica; o resto fica escondido.
target_link_options(${PRAXIS_DRIVER_NOME} PRIVATE
  "LINKER:-exported_symbol,_${PRAXIS_FABRICA_FUNCAO}"
  "LINKER:-dead_strip"
)
set_target_properties(${PRAXIS_DRIVER_NOME} PROPERTIES
  OUTPUT_NAME "${PRAXIS_DRIVER_NOME}"
  PREFIX ""
  SUFFIX ""
  BUNDLE TRUE
  BUNDLE_EXTENSION "driver"
  MACOSX_BUNDLE_INFO_PLIST "${CMAKE_CURRENT_BINARY_DIR}/Info.plist"
  CXX_VISIBILITY_PRESET hidden
)

# ---------------------------------------------------------------------------
# Testes (rodam aqui, sem instalar nada).

enable_testing()

add_executable(teste_anel testes/TesteAnel.cpp)
target_include_directories(teste_anel PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/fonte")
target_compile_options(teste_anel PRIVATE ${AVISOS})
add_test(NAME anel_de_amostras COMMAND teste_anel)

add_executable(teste_dispositivo testes/TesteDispositivo.cpp)
target_link_libraries(teste_dispositivo PRIVATE praxis_nucleo ${BIBLIOTECA_CoreAudio})
target_compile_options(teste_dispositivo PRIVATE ${AVISOS})
add_test(NAME dispositivos_de_laco COMMAND teste_dispositivo)

# Carrega o PraxisAudio.driver construído do mesmo jeito que o coreaudiod
# (pacote + função de fábrica do Info.plist) e confere a interface do plug-in.
add_executable(teste_carregar testes/TesteCarregar.cpp)
target_link_libraries(teste_carregar PRIVATE ${BIBLIOTECA_CoreFoundation} ${BIBLIOTECA_CoreAudio})
target_compile_options(teste_carregar PRIVATE ${AVISOS})
add_dependencies(teste_carregar ${PRAXIS_DRIVER_NOME})
# Fica numa subpasta: se o executável estiver na mesma pasta do .driver, o
# CoreFoundation trata essa pasta como o pacote principal e não carrega o
# plug-in.
foreach(alvo teste_anel teste_dispositivo teste_carregar)
  set_target_properties(${alvo} PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/testes")
endforeach()
add_test(NAME carregar_driver
  COMMAND teste_carregar "${CMAKE_CURRENT_BINARY_DIR}/${PRAXIS_DRIVER_NOME}.driver")
