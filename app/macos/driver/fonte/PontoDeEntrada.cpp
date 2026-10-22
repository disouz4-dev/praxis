// Praxis — driver de áudio do macOS
// Licença MIT (veja LICENSE na raiz do projeto).
//
// Função de fábrica que o coreaudiod chama ao carregar PraxisAudio.driver.
// O nome dela está no Info.plist, na chave CFPlugInFactories. É o único
// símbolo exportado pelo binário do driver.

#include "DispositivoLaco.hpp"

#include <CoreAudio/AudioServerPlugIn.h>

extern "C" __attribute__((visibility("default"))) void* PraxisAudioFabrica(
    CFAllocatorRef alocador,
    CFUUIDRef tipoUUID)
{
    // Só atende pedidos do tipo "Audio Server Plug-in"
    // (443ABAB8-E7B3-491A-B985-BEB9187030DB).
    if (!CFEqual(tipoUUID, kAudioServerPlugInTypeUUID)) {
        return nullptr;
    }

    // Guardado num estático para viver enquanto o coreaudiod mantiver o
    // plug-in carregado.
    static std::shared_ptr<aspl::Driver> driver = praxis::CriarDriverPraxis();

    return driver->GetReference();
}
