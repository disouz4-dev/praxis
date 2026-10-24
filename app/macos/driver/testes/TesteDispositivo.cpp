// Praxis — driver de áudio do macOS
// Licença MIT (veja LICENSE na raiz do projeto).
//
// Testes dos dispositivos montados com a libASPL, sem instalar o driver: o
// teste faz o papel do coreaudiod, chamando as mesmas operações de entrada e
// saída que ele chama (começar, escrever a mistura, ler a entrada).

#include "DispositivoLaco.hpp"
#include "Verificar.hpp"

#include <aspl/Plugin.hpp>

#include <CoreAudio/AudioServerPlugIn.h>

#include <cmath>
#include <vector>

namespace {

std::shared_ptr<aspl::Device> AcharPorUID(const std::shared_ptr<aspl::Plugin>& plugin,
    const std::string& uid)
{
    for (UInt32 i = 0; i < plugin->GetDeviceCount(); i++) {
        auto d = plugin->GetDeviceByIndex(i);
        if (d && d->GetDeviceUID() == uid) {
            return d;
        }
    }
    return nullptr;
}

float Sinal(int64_t tempo, UInt32 canal)
{
    // Senoide de 440 Hz em 48 kHz, canais com fases diferentes.
    return float(0.5 * std::sin(2.0 * M_PI * 440.0 * double(tempo) / 48000.0 + canal));
}

// Simula o coreaudiod: a cada ciclo, escreve a saída misturada no tempo de
// saída e lê a entrada no tempo de entrada (que fica atrás).
struct Simulador
{
    std::shared_ptr<aspl::Device> saida;   // dispositivo onde se toca
    std::shared_ptr<aspl::Device> entrada; // dispositivo de onde se grava
    UInt32 quadrosPorCiclo = 512;
    Float64 adiantamentoSaida = 1024; // tempo de saída à frente do "agora"
    Float64 atrasoEntrada = 512;      // tempo de entrada atrás do "agora"

    void Ciclo(Float64 agora, bool tocar, std::vector<float>& lido)
    {
        AudioServerPlugInIOCycleInfo info = {};
        info.mOutputTime.mSampleTime = agora + adiantamentoSaida;
        info.mInputTime.mSampleTime = agora - atrasoEntrada;
        info.mOutputTime.mFlags = kAudioTimeStampSampleTimeValid;
        info.mInputTime.mFlags = kAudioTimeStampSampleTimeValid;

        if (tocar) {
            std::vector<float> bloco(size_t(quadrosPorCiclo) * praxis::kCanais);
            for (UInt32 i = 0; i < quadrosPorCiclo; i++) {
                for (UInt32 c = 0; c < praxis::kCanais; c++) {
                    bloco[size_t(i) * praxis::kCanais + c] =
                        Sinal(int64_t(info.mOutputTime.mSampleTime) + i, c);
                }
            }
            auto fluxoSaida = saida->GetStreamByIndex(aspl::Direction::Output, 0);
            saida->DoIOOperation(saida->GetID(),
                fluxoSaida->GetID(),
                1,
                kAudioServerPlugInIOOperationWriteMix,
                quadrosPorCiclo,
                &info,
                bloco.data(),
                nullptr);
        }

        lido.assign(size_t(quadrosPorCiclo) * praxis::kCanais, -9.0f);
        auto fluxoEntrada = entrada->GetStreamByIndex(aspl::Direction::Input, 0);
        entrada->DoIOOperation(entrada->GetID(),
            fluxoEntrada->GetID(),
            2,
            kAudioServerPlugInIOOperationReadInput,
            quadrosPorCiclo,
            &info,
            lido.data(),
            nullptr);
    }
};

bool TudoSilencio(const std::vector<float>& v)
{
    for (float x : v) {
        if (x != 0.0f) {
            return false;
        }
    }
    return true;
}

} // namespace

CASO("o driver tem exatamente Praxis Mic e Praxis Speaker, fabricante Praxis")
{
    auto driver = praxis::CriarDriverPraxis();
    auto plugin = driver->GetPlugin();
    VERIFICAR(plugin->GetDeviceCount() == 2);
    VERIFICAR(plugin->GetManufacturer() == "Praxis");

    auto mic = AcharPorUID(plugin, "dev.disouz4.praxis.mic");
    auto speaker = AcharPorUID(plugin, "dev.disouz4.praxis.speaker");
    VERIFICAR(mic != nullptr);
    VERIFICAR(speaker != nullptr);
    if (!mic || !speaker) {
        return;
    }
    VERIFICAR(mic->GetName() == "Praxis Mic");
    VERIFICAR(speaker->GetName() == "Praxis Speaker");
    VERIFICAR(mic->GetManufacturer() == "Praxis");
    VERIFICAR(speaker->GetManufacturer() == "Praxis");
    VERIFICAR(mic->GetModelUID() == "dev.disouz4.praxis.laco");
    VERIFICAR(!mic->GetCanBeDefaultSystemDevice());
}

CASO("cada dispositivo tem uma saída e uma entrada, 2 canais, ponto flutuante 32 bits, 48 kHz")
{
    auto driver = praxis::CriarDriverPraxis();
    auto plugin = driver->GetPlugin();
    for (UInt32 i = 0; i < plugin->GetDeviceCount(); i++) {
        auto d = plugin->GetDeviceByIndex(i);
        VERIFICAR(d->GetStreamCount(aspl::Direction::Output) == 1);
        VERIFICAR(d->GetStreamCount(aspl::Direction::Input) == 1);
        VERIFICAR(d->GetNominalSampleRate() == 48000.0);

        const auto taxas = d->GetAvailableSampleRates();
        VERIFICAR(taxas.size() == 2);

        for (auto direcao : {aspl::Direction::Output, aspl::Direction::Input}) {
            auto f = d->GetStreamByIndex(direcao, 0);
            const auto fmt = f->GetPhysicalFormat();
            VERIFICAR(fmt.mSampleRate == 48000.0);
            VERIFICAR(fmt.mFormatID == kAudioFormatLinearPCM);
            VERIFICAR((fmt.mFormatFlags & kAudioFormatFlagIsFloat) != 0);
            VERIFICAR(fmt.mBitsPerChannel == 32);
            VERIFICAR(fmt.mChannelsPerFrame == 2);
            VERIFICAR(fmt.mBytesPerFrame == 8);
            VERIFICAR(f->GetVirtualFormat().mSampleRate == 48000.0);
            VERIFICAR(f->GetAvailablePhysicalFormats().size() == 2);
        }
    }
}

CASO("laço: o que é tocado na saída do Praxis Mic sai na entrada do Praxis Mic")
{
    auto driver = praxis::CriarDriverPraxis();
    auto mic = AcharPorUID(driver->GetPlugin(), praxis::kUIDMic);

    VERIFICAR(mic->StartIO(mic->GetID(), 1) == kAudioHardwareNoError);
    VERIFICAR(mic->StartIO(mic->GetID(), 2) == kAudioHardwareNoError);

    Simulador sim;
    sim.saida = mic;
    sim.entrada = mic;

    // 400 ciclos de 512 quadros = 204800 quadros, mais de 3 voltas do anel.
    std::vector<float> lido;
    bool sinalCerto = true;
    int ciclosComSinal = 0;
    for (int k = 0; k < 400; k++) {
        const Float64 agora = Float64(k) * sim.quadrosPorCiclo;
        sim.Ciclo(agora, true, lido);
        const int64_t tempoEntrada = int64_t(agora - sim.atrasoEntrada);
        // A entrada só tem sinal depois que o tempo de entrada alcança o
        // primeiro tempo de saída escrito (1024).
        if (tempoEntrada >= int64_t(sim.adiantamentoSaida)) {
            ciclosComSinal++;
            for (UInt32 i = 0; i < sim.quadrosPorCiclo; i++) {
                for (UInt32 c = 0; c < praxis::kCanais; c++) {
                    if (lido[size_t(i) * praxis::kCanais + c] != Sinal(tempoEntrada + i, c)) {
                        sinalCerto = false;
                    }
                }
            }
        } else {
            VERIFICAR(TudoSilencio(lido));
        }
    }
    VERIFICAR(sinalCerto);
    VERIFICAR(ciclosComSinal > 390);

    // Para de tocar: depois que a entrada passa do último tempo escrito, só
    // silêncio.
    bool silencioDepois = true;
    for (int k = 400; k < 420; k++) {
        const Float64 agora = Float64(k) * sim.quadrosPorCiclo;
        sim.Ciclo(agora, false, lido);
        const Float64 tempoEntrada = agora - sim.atrasoEntrada;
        if (tempoEntrada >= 400.0 * sim.quadrosPorCiclo + sim.adiantamentoSaida &&
            !TudoSilencio(lido)) {
            silencioDepois = false;
        }
    }
    VERIFICAR(silencioDepois);

    VERIFICAR(mic->StopIO(mic->GetID(), 1) == kAudioHardwareNoError);
    VERIFICAR(mic->StopIO(mic->GetID(), 2) == kAudioHardwareNoError);
}

CASO("os dois dispositivos são separados: tocar no Mic não aparece no Speaker")
{
    auto driver = praxis::CriarDriverPraxis();
    auto mic = AcharPorUID(driver->GetPlugin(), praxis::kUIDMic);
    auto speaker = AcharPorUID(driver->GetPlugin(), praxis::kUIDSpeaker);
    mic->StartIO(mic->GetID(), 1);
    speaker->StartIO(speaker->GetID(), 2);

    Simulador sim;
    sim.saida = mic;
    sim.entrada = speaker;
    std::vector<float> lido;
    bool silencio = true;
    for (int k = 0; k < 50; k++) {
        sim.Ciclo(Float64(k) * sim.quadrosPorCiclo, true, lido);
        if (!TudoSilencio(lido)) {
            silencio = false;
        }
    }
    VERIFICAR(silencio);

    // E o Speaker também faz laço sozinho.
    Simulador sim2;
    sim2.saida = speaker;
    sim2.entrada = speaker;
    bool temSinal = false;
    for (int k = 0; k < 50; k++) {
        sim2.Ciclo(Float64(k) * sim2.quadrosPorCiclo, true, lido);
        if (!TudoSilencio(lido)) {
            temSinal = true;
        }
    }
    VERIFICAR(temSinal);
}

CASO("ninguém tocando: a entrada é silêncio")
{
    auto driver = praxis::CriarDriverPraxis();
    auto mic = AcharPorUID(driver->GetPlugin(), praxis::kUIDMic);
    mic->StartIO(mic->GetID(), 2);
    Simulador sim;
    sim.saida = mic;
    sim.entrada = mic;
    std::vector<float> lido;
    bool silencio = true;
    for (int k = 0; k < 20; k++) {
        sim.Ciclo(Float64(k) * sim.quadrosPorCiclo, false, lido);
        if (!TudoSilencio(lido)) {
            silencio = false;
        }
    }
    VERIFICAR(silencio);
}

CASO("trocar a taxa para 44,1 kHz muda o dispositivo e os dois fluxos juntos")
{
    auto driver = praxis::CriarDriverPraxis();
    auto mic = AcharPorUID(driver->GetPlugin(), praxis::kUIDMic);
    auto saida = mic->GetStreamByIndex(aspl::Direction::Output, 0);
    auto entrada = mic->GetStreamByIndex(aspl::Direction::Input, 0);

    VERIFICAR(mic->SetNominalSampleRateAsync(44100.0) == kAudioHardwareNoError);
    VERIFICAR(mic->GetNominalSampleRate() == 44100.0);
    VERIFICAR(saida->GetPhysicalFormat().mSampleRate == 44100.0);
    VERIFICAR(entrada->GetPhysicalFormat().mSampleRate == 44100.0);
    VERIFICAR(saida->GetVirtualFormat().mSampleRate == 44100.0);
    VERIFICAR(entrada->GetVirtualFormat().mSampleRate == 44100.0);

    // Um app muda o formato do fluxo de entrada de volta para 48 kHz: o
    // dispositivo e o outro fluxo acompanham.
    VERIFICAR(entrada->SetPhysicalFormatAsync(praxis::FormatoLaco(48000.0)) ==
              kAudioHardwareNoError);
    VERIFICAR(mic->GetNominalSampleRate() == 48000.0);
    VERIFICAR(saida->GetPhysicalFormat().mSampleRate == 48000.0);
    VERIFICAR(saida->GetVirtualFormat().mSampleRate == 48000.0);

    // Taxa não aceita é recusada.
    VERIFICAR(mic->SetNominalSampleRateAsync(96000.0) != kAudioHardwareNoError);
    VERIFICAR(mic->GetNominalSampleRate() == 48000.0);
}

int main()
{
    return verificar::RodarTodos();
}
