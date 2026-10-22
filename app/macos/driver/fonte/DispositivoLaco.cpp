// Praxis — driver de áudio do macOS
// Licença MIT (veja LICENSE na raiz do projeto).

#include "DispositivoLaco.hpp"

#include <aspl/ControlRequestHandler.hpp>
#include <aspl/IORequestHandler.hpp>
#include <aspl/Plugin.hpp>
#include <aspl/Tracer.hpp>

#include <cmath>
#include <vector>

namespace praxis {

namespace {

// Liga as chamadas de entrada e saída do coreaudiod ao anel de amostras.
class ManipuladorLaco : public aspl::ControlRequestHandler, public aspl::IORequestHandler
{
public:
    explicit ManipuladorLaco(std::shared_ptr<AnelAmostras> anel)
        : anel_(std::move(anel))
    {
    }

    // Primeiro cliente começando a tocar ou gravar: o relógio do dispositivo
    // recomeça do zero, então o que estava no anel não vale mais.
    OSStatus OnStartIO() override
    {
        anel_->pedirLimpeza();
        return kAudioHardwareNoError;
    }

    // Saída já misturada de todos os apps que tocam no dispositivo.
    void OnWriteMixedOutput(const std::shared_ptr<aspl::Stream>& stream,
        Float64 zeroTimestamp,
        Float64 timestamp,
        const void* bytes,
        UInt32 bytesCount) override
    {
        const UInt32 quadros = bytesCount / UInt32(sizeof(Float32) * anel_->canais());
        anel_->escrever(std::llround(timestamp), static_cast<const float*>(bytes), quadros);
    }

    // Entrada pedida por um app que grava do dispositivo.
    void OnReadClientInput(const std::shared_ptr<aspl::Client>& client,
        const std::shared_ptr<aspl::Stream>& stream,
        Float64 zeroTimestamp,
        Float64 timestamp,
        void* bytes,
        UInt32 bytesCount) override
    {
        const UInt32 quadros = bytesCount / UInt32(sizeof(Float32) * anel_->canais());
        anel_->ler(std::llround(timestamp), static_cast<float*>(bytes), quadros);

        // Sobra de bytes que não forma um quadro inteiro (não deve acontecer):
        // silêncio, para nunca entregar memória com lixo.
        const UInt32 usados = quadros * UInt32(sizeof(Float32) * anel_->canais());
        if (usados < bytesCount) {
            std::memset(static_cast<char*>(bytes) + usados, 0, bytesCount - usados);
        }
    }

private:
    std::shared_ptr<AnelAmostras> anel_;
};

std::vector<AudioValueRange> TaxasDoDispositivo()
{
    std::vector<AudioValueRange> taxas;
    for (Float64 taxa : kTaxasAceitas) {
        taxas.push_back(AudioValueRange{taxa, taxa});
    }
    return taxas;
}

std::vector<AudioStreamRangedDescription> FormatosDoFluxo()
{
    std::vector<AudioStreamRangedDescription> formatos;
    for (Float64 taxa : kTaxasAceitas) {
        AudioStreamRangedDescription f = {};
        f.mFormat = FormatoLaco(taxa);
        f.mSampleRateRange.mMinimum = taxa;
        f.mSampleRateRange.mMaximum = taxa;
        formatos.push_back(f);
    }
    return formatos;
}

} // namespace

AudioStreamBasicDescription FormatoLaco(Float64 taxa)
{
    AudioStreamBasicDescription f = {};
    f.mSampleRate = taxa;
    f.mFormatID = kAudioFormatLinearPCM;
    f.mFormatFlags =
        kAudioFormatFlagIsFloat | kAudioFormatFlagsNativeEndian | kAudioFormatFlagIsPacked;
    f.mBitsPerChannel = 32;
    f.mChannelsPerFrame = kCanais;
    f.mBytesPerFrame = kCanais * sizeof(Float32);
    f.mFramesPerPacket = 1;
    f.mBytesPerPacket = f.mBytesPerFrame;
    return f;
}

// ---------------------------------------------------------------------------
// DispositivoLaco

DispositivoLaco::DispositivoLaco(std::shared_ptr<const aspl::Context> contexto,
    const aspl::DeviceParameters& parametros,
    std::shared_ptr<AnelAmostras> anel)
    : aspl::Device(std::move(contexto), parametros)
    , anel_(std::move(anel))
{
}

OSStatus DispositivoLaco::SetNominalSampleRateImpl(Float64 taxa)
{
    const OSStatus estado = aspl::Device::SetNominalSampleRateImpl(taxa);
    if (estado != kAudioHardwareNoError) {
        return estado;
    }

    anel_->pedirLimpeza();
    AlinharFluxos(taxa);

    return kAudioHardwareNoError;
}

void DispositivoLaco::AlinharFluxos(Float64 taxa)
{
    // Dentro de uma mudança de configuração, a libASPL aplica os pedidos
    // "Async" na hora; fora dela, enfileira no coreaudiod. Nos dois casos o
    // resultado é o dispositivo e os fluxos com a mesma taxa.
    for (auto direcao : {aspl::Direction::Output, aspl::Direction::Input}) {
        const UInt32 n = GetStreamCount(direcao);
        for (UInt32 i = 0; i < n; i++) {
            auto fluxo = GetStreamByIndex(direcao, i);
            if (!fluxo) {
                continue;
            }
            if (fluxo->GetPhysicalFormat().mSampleRate != taxa) {
                fluxo->SetPhysicalFormatAsync(FormatoLaco(taxa));
            }
            if (fluxo->GetVirtualFormat().mSampleRate != taxa) {
                fluxo->SetVirtualFormatAsync(FormatoLaco(taxa));
            }
        }
    }
}

// ---------------------------------------------------------------------------
// FluxoLaco

FluxoLaco::FluxoLaco(std::shared_ptr<const aspl::Context> contexto,
    std::shared_ptr<DispositivoLaco> dispositivo,
    const aspl::StreamParameters& parametros)
    : aspl::Stream(std::move(contexto), dispositivo, parametros)
    , dispositivo_(dispositivo)
{
}

OSStatus FluxoLaco::SetPhysicalFormatImpl(const AudioStreamBasicDescription& formato)
{
    const OSStatus estado = aspl::Stream::SetPhysicalFormatImpl(formato);
    if (estado == kAudioHardwareNoError) {
        PropagarTaxa(formato.mSampleRate);
    }
    return estado;
}

OSStatus FluxoLaco::SetVirtualFormatImpl(const AudioStreamBasicDescription& formato)
{
    const OSStatus estado = aspl::Stream::SetVirtualFormatImpl(formato);
    if (estado == kAudioHardwareNoError) {
        PropagarTaxa(formato.mSampleRate);
    }
    return estado;
}

void FluxoLaco::PropagarTaxa(Float64 taxa)
{
    // Se a taxa já é a do dispositivo, a libASPL não faz nada ("valor não
    // mudou"), o que encerra a propagação entre dispositivo e fluxos.
    if (auto dispositivo = dispositivo_.lock()) {
        dispositivo->SetNominalSampleRateAsync(taxa);
    }
}

// ---------------------------------------------------------------------------
// Montagem

std::shared_ptr<DispositivoLaco> CriarDispositivoLaco(
    std::shared_ptr<const aspl::Context> contexto,
    const std::string& nome,
    const std::string& uid)
{
    aspl::DeviceParameters parametros;
    parametros.Name = nome;
    parametros.Manufacturer = kFabricante;
    parametros.DeviceUID = uid;
    parametros.ModelUID = kModeloUID;
    parametros.SampleRate = UInt32(kTaxaPadrao);
    parametros.ChannelCount = kCanais;
    // Pode ser escolhido como saída ou entrada padrão pelo usuário, mas nunca
    // recebe os sons de alerta do sistema (eles vazariam para a chamada).
    parametros.CanBeDefault = true;
    parametros.CanBeDefaultForSystemSounds = false;
    // Demora mínima: o laço é só memória.
    parametros.Latency = 0;
    parametros.SafetyOffset = 0;
    // Uma marca de tempo do relógio a cada 1 s de áudio na taxa padrão.
    parametros.ZeroTimeStampPeriod = UInt32(kTaxaPadrao);
    // O coreaudiod mistura todos os apps que tocam e entrega uma só saída.
    parametros.EnableMixing = true;

    auto anel = std::make_shared<AnelAmostras>(kCapacidadeAnel, kCanais);
    auto dispositivo = std::make_shared<DispositivoLaco>(contexto, parametros, anel);

    dispositivo->SetAvailableSampleRatesAsync(TaxasDoDispositivo());

    for (auto direcao : {aspl::Direction::Output, aspl::Direction::Input}) {
        aspl::StreamParameters fluxoParametros;
        fluxoParametros.Direction = direcao;
        fluxoParametros.StartingChannel = 1;
        fluxoParametros.Format = FormatoLaco(kTaxaPadrao);

        auto fluxo = std::make_shared<FluxoLaco>(contexto, dispositivo, fluxoParametros);
        fluxo->SetAvailablePhysicalFormatsAsync(FormatosDoFluxo());
        fluxo->SetAvailableVirtualFormatsAsync(FormatosDoFluxo());

        dispositivo->AddStreamAsync(fluxo);
    }

    auto manipulador = std::make_shared<ManipuladorLaco>(anel);
    dispositivo->SetControlHandler(manipulador);
    dispositivo->SetIOHandler(manipulador);

    return dispositivo;
}

std::shared_ptr<aspl::Driver> CriarDriverPraxis()
{
    // Registro de diagnóstico: desligado por padrão (a libASPL registraria cada
    // consulta de propriedade no registro do sistema). Para depurar depois de
    // instalar, construa com ./construir.sh --diagnostico e veja com
    //   log stream --predicate 'process == "coreaudiod"' | grep -i praxis
#if PRAXIS_DIAGNOSTICO
    auto registro = std::make_shared<aspl::Tracer>(aspl::Tracer::Mode::Syslog);
#else
    auto registro = std::make_shared<aspl::Tracer>(aspl::Tracer::Mode::Noop);
#endif
    auto contexto = std::make_shared<aspl::Context>(registro);

    aspl::PluginParameters pluginParametros;
    pluginParametros.Manufacturer = kFabricante;
    auto plugin = std::make_shared<aspl::Plugin>(contexto, pluginParametros);

    plugin->AddDevice(CriarDispositivoLaco(contexto, kNomeMic, kUIDMic));
    plugin->AddDevice(CriarDispositivoLaco(contexto, kNomeSpeaker, kUIDSpeaker));

    return std::make_shared<aspl::Driver>(contexto, plugin);
}

} // namespace praxis
