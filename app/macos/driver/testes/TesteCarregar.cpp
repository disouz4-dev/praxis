// Praxis — driver de áudio do macOS
// Licença MIT (veja LICENSE na raiz do projeto).
//
// Carrega o PraxisAudio.driver já construído do mesmo jeito que o coreaudiod:
// pelo mecanismo de plug-ins do CoreFoundation, procurando no Info.plist uma
// fábrica do tipo "Audio Server Plug-in" e chamando essa fábrica. Depois
// inicializa o plug-in com um "hospedeiro" falso e consulta as propriedades
// pela interface em C, como o coreaudiod faria. Nada é instalado.
//
// Uso: teste_carregar /caminho/para/PraxisAudio.driver

#include "Verificar.hpp"

#include <CoreAudio/AudioServerPlugIn.h>
#include <CoreFoundation/CoreFoundation.h>

#include <string>
#include <vector>

namespace {

const char* gCaminho = nullptr;

// ---- Hospedeiro falso (o papel do coreaudiod) ------------------------------

OSStatus HospedeiroPropriedadesMudaram(AudioServerPlugInHostRef,
    AudioObjectID,
    UInt32,
    const AudioObjectPropertyAddress*)
{
    return kAudioHardwareNoError;
}

OSStatus HospedeiroLer(AudioServerPlugInHostRef, CFStringRef, CFPropertyListRef* saida)
{
    *saida = nullptr;
    return kAudioHardwareUnspecifiedError; // nada guardado
}

OSStatus HospedeiroGravar(AudioServerPlugInHostRef, CFStringRef, CFPropertyListRef)
{
    return kAudioHardwareNoError;
}

OSStatus HospedeiroApagar(AudioServerPlugInHostRef, CFStringRef)
{
    return kAudioHardwareNoError;
}

OSStatus HospedeiroPedirMudanca(AudioServerPlugInHostRef, AudioObjectID, UInt64, void*)
{
    return kAudioHardwareNoError;
}

AudioServerPlugInHostInterface gHospedeiro = {
    HospedeiroPropriedadesMudaram,
    HospedeiroLer,
    HospedeiroGravar,
    HospedeiroApagar,
    HospedeiroPedirMudanca,
};

// ---- Utilidades ------------------------------------------------------------

std::string Texto(CFStringRef s)
{
    if (!s) {
        return "";
    }
    char buf[512] = {};
    CFStringGetCString(s, buf, sizeof(buf), kCFStringEncodingUTF8);
    return buf;
}

AudioServerPlugInDriverRef CarregarDriver(CFPlugInRef* plugInSaida)
{
    CFStringRef caminho =
        CFStringCreateWithCString(nullptr, gCaminho, kCFStringEncodingUTF8);
    CFURLRef url =
        CFURLCreateWithFileSystemPath(nullptr, caminho, kCFURLPOSIXPathStyle, true);
    CFRelease(caminho);

    CFPlugInRef plugIn = CFPlugInCreate(nullptr, url);
    CFRelease(url);
    *plugInSaida = plugIn;
    if (!plugIn) {
        return nullptr;
    }

    CFArrayRef fabricas =
        CFPlugInFindFactoriesForPlugInTypeInPlugIn(kAudioServerPlugInTypeUUID, plugIn);
    if (!fabricas || CFArrayGetCount(fabricas) != 1) {
        if (fabricas) {
            CFRelease(fabricas);
        }
        return nullptr;
    }
    CFUUIDRef fabrica = (CFUUIDRef)CFArrayGetValueAtIndex(fabricas, 0);
    void* instancia = CFPlugInInstanceCreate(nullptr, fabrica, kAudioServerPlugInTypeUUID);
    CFRelease(fabricas);

    return static_cast<AudioServerPlugInDriverRef>(instancia);
}

template <typename T>
bool LerPropriedade(AudioServerPlugInDriverRef d,
    AudioObjectID objeto,
    AudioObjectPropertySelector seletor,
    AudioObjectPropertyScope escopo,
    std::vector<T>& saida)
{
    AudioObjectPropertyAddress endereco = {seletor, escopo, kAudioObjectPropertyElementMain};
    UInt32 tamanho = 0;
    if ((*d)->GetPropertyDataSize(d, objeto, 0, &endereco, 0, nullptr, &tamanho) !=
        kAudioHardwareNoError) {
        return false;
    }
    saida.resize(tamanho / sizeof(T));
    UInt32 usado = 0;
    if ((*d)->GetPropertyData(
            d, objeto, 0, &endereco, 0, nullptr, tamanho, &usado, saida.data()) !=
        kAudioHardwareNoError) {
        return false;
    }
    saida.resize(usado / sizeof(T));
    return true;
}

std::string LerTexto(AudioServerPlugInDriverRef d,
    AudioObjectID objeto,
    AudioObjectPropertySelector seletor)
{
    std::vector<CFStringRef> v;
    if (!LerPropriedade(d, objeto, seletor, kAudioObjectPropertyScopeGlobal, v) ||
        v.size() != 1) {
        return "";
    }
    std::string s = Texto(v[0]);
    if (v[0]) {
        CFRelease(v[0]);
    }
    return s;
}

} // namespace

CASO("o pacote carrega pela fábrica do Info.plist e responde como Audio Server Plug-in")
{
    CFPlugInRef plugIn = nullptr;
    AudioServerPlugInDriverRef d = CarregarDriver(&plugIn);
    VERIFICAR(plugIn != nullptr);
    VERIFICAR(d != nullptr);
    if (!d) {
        return;
    }

    // A interface pedida pelo coreaudiod.
    void* interface = nullptr;
    VERIFICAR((*d)->QueryInterface(d,
                  CFUUIDGetUUIDBytes(kAudioServerPlugInDriverInterfaceUUID),
                  &interface) == S_OK);
    VERIFICAR(interface == d);
    (*d)->Release(d);

    VERIFICAR((*d)->Initialize(d, &gHospedeiro) == kAudioHardwareNoError);

    // Fabricante do plug-in.
    VERIFICAR(LerTexto(d, kAudioObjectPlugInObject, kAudioObjectPropertyManufacturer) ==
              "Praxis");

    // Lista de dispositivos.
    std::vector<AudioObjectID> dispositivos;
    VERIFICAR(LerPropriedade(d,
        kAudioObjectPlugInObject,
        kAudioPlugInPropertyDeviceList,
        kAudioObjectPropertyScopeGlobal,
        dispositivos));
    VERIFICAR(dispositivos.size() == 2);

    std::vector<std::string> nomes;
    std::vector<std::string> uids;
    for (AudioObjectID id : dispositivos) {
        nomes.push_back(LerTexto(d, id, kAudioObjectPropertyName));
        uids.push_back(LerTexto(d, id, kAudioDevicePropertyDeviceUID));
        VERIFICAR(LerTexto(d, id, kAudioObjectPropertyManufacturer) == "Praxis");

        // Uma entrada e uma saída.
        std::vector<AudioObjectID> fluxosEntrada, fluxosSaida;
        VERIFICAR(LerPropriedade(d,
            id,
            kAudioDevicePropertyStreams,
            kAudioObjectPropertyScopeInput,
            fluxosEntrada));
        VERIFICAR(LerPropriedade(d,
            id,
            kAudioDevicePropertyStreams,
            kAudioObjectPropertyScopeOutput,
            fluxosSaida));
        VERIFICAR(fluxosEntrada.size() == 1);
        VERIFICAR(fluxosSaida.size() == 1);

        std::vector<Float64> taxa;
        VERIFICAR(LerPropriedade(d,
            id,
            kAudioDevicePropertyNominalSampleRate,
            kAudioObjectPropertyScopeGlobal,
            taxa));
        VERIFICAR(taxa.size() == 1 && taxa[0] == 48000.0);
    }

    const bool temMic = (nomes[0] == "Praxis Mic" && uids[0] == "dev.disouz4.praxis.mic") ||
                        (nomes[1] == "Praxis Mic" && uids[1] == "dev.disouz4.praxis.mic");
    const bool temSpeaker =
        (nomes[0] == "Praxis Speaker" && uids[0] == "dev.disouz4.praxis.speaker") ||
        (nomes[1] == "Praxis Speaker" && uids[1] == "dev.disouz4.praxis.speaker");
    VERIFICAR(temMic);
    VERIFICAR(temSpeaker);
    for (size_t i = 0; i < nomes.size(); i++) {
        std::printf("  dispositivo: \"%s\" (%s)\n", nomes[i].c_str(), uids[i].c_str());
    }
}

int main(int argc, char** argv)
{
    if (argc != 2) {
        std::fprintf(stderr, "uso: %s /caminho/PraxisAudio.driver\n", argv[0]);
        return 2;
    }
    gCaminho = argv[1];
    return verificar::RodarTodos();
}
