// Praxis — driver de áudio do macOS
// Licença MIT (veja LICENSE na raiz do projeto).
//
// Dispositivo de laço: um dispositivo virtual com uma saída e uma entrada. Tudo
// o que os apps tocam na saída aparece na entrada do mesmo dispositivo.
// Construído sobre a biblioteca libASPL (MIT, https://github.com/gavv/libASPL).

#pragma once

#include "AnelAmostras.hpp"

#include <aspl/Context.hpp>
#include <aspl/Device.hpp>
#include <aspl/Driver.hpp>
#include <aspl/Stream.hpp>

#include <memory>
#include <string>

namespace praxis {

// Formato fixo dos dois dispositivos: 2 canais, número de ponto flutuante de
// 32 bits, intercalado. Taxas aceitas: 48 kHz (padrão) e 44,1 kHz.
constexpr UInt32 kCanais = 2;
constexpr Float64 kTaxaPadrao = 48000.0;
constexpr Float64 kTaxasAceitas[] = {44100.0, 48000.0};

// Tamanho do anel: 2^16 quadros (cerca de 1,4 s a 48 kHz). Não influencia a
// demora do laço, só o quanto de folga existe entre escrita e leitura.
constexpr UInt32 kCapacidadeAnel = 65536;

// Fabricante mostrado ao usuário.
inline const char* const kFabricante = "Praxis";

// Identificador de modelo comum aos dois dispositivos.
inline const char* const kModeloUID = "dev.disouz4.praxis.laco";

// Nomes e identificadores únicos e estáveis (não mudar: os apps guardam o
// dispositivo escolhido por este identificador).
inline const char* const kNomeMic = "Praxis Mic";
inline const char* const kUIDMic = "dev.disouz4.praxis.mic";
inline const char* const kNomeSpeaker = "Praxis Speaker";
inline const char* const kUIDSpeaker = "dev.disouz4.praxis.speaker";

//! Descrição do formato de 32 bits em ponto flutuante na taxa pedida.
AudioStreamBasicDescription FormatoLaco(Float64 taxa);

//! Dispositivo de laço. Mantém a taxa do dispositivo e a de todos os seus fluxos
//! (entrada e saída) sempre iguais, e esvazia o anel quando a taxa muda.
class DispositivoLaco : public aspl::Device
{
public:
    DispositivoLaco(std::shared_ptr<const aspl::Context> contexto,
        const aspl::DeviceParameters& parametros,
        std::shared_ptr<AnelAmostras> anel);

    std::shared_ptr<AnelAmostras> Anel() const
    {
        return anel_;
    }

protected:
    OSStatus SetNominalSampleRateImpl(Float64 taxa) override;

private:
    void AlinharFluxos(Float64 taxa);

    std::shared_ptr<AnelAmostras> anel_;
};

//! Fluxo (entrada ou saída) do dispositivo de laço. Quando um app muda o formato
//! do fluxo para outra taxa, a taxa do dispositivo inteiro acompanha.
class FluxoLaco : public aspl::Stream
{
public:
    FluxoLaco(std::shared_ptr<const aspl::Context> contexto,
        std::shared_ptr<DispositivoLaco> dispositivo,
        const aspl::StreamParameters& parametros);

protected:
    OSStatus SetPhysicalFormatImpl(const AudioStreamBasicDescription& formato) override;
    OSStatus SetVirtualFormatImpl(const AudioStreamBasicDescription& formato) override;

private:
    void PropagarTaxa(Float64 taxa);

    std::weak_ptr<DispositivoLaco> dispositivo_;
};

//! Cria um dispositivo de laço completo (fluxo de saída, fluxo de entrada,
//! manipulador de entrada e saída ligado ao anel).
std::shared_ptr<DispositivoLaco> CriarDispositivoLaco(
    std::shared_ptr<const aspl::Context> contexto,
    const std::string& nome,
    const std::string& uid);

//! Cria o driver inteiro do Praxis: um plug-in com "Praxis Mic" e
//! "Praxis Speaker".
std::shared_ptr<aspl::Driver> CriarDriverPraxis();

} // namespace praxis
