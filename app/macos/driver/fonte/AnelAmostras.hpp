// Praxis — driver de áudio do macOS
// Licença MIT (veja LICENSE na raiz do projeto).
//
// Anel de amostras do laço: o que é tocado na saída do dispositivo é guardado
// aqui e devolvido na entrada do mesmo dispositivo.
//
// O anel é indexado pelo "tempo em amostras" que o servidor de áudio do macOS
// (coreaudiod) informa em cada ciclo de entrada e saída:
//   - a escrita (saída) chega com o tempo do quadro que vai ser tocado;
//   - a leitura (entrada) chega com o tempo do quadro que já "foi gravado".
// Como o tempo de saída está sempre um pouco à frente do tempo de entrada, o
// que foi escrito no tempo T é lido quando a entrada alcança T. A demora entre
// tocar e gravar fica em torno de dois ciclos de áudio (poucos milissegundos).
//
// Garantias:
//   - silêncio quando ninguém está tocando: tempos que nunca foram escritos, ou
//     já sobrescritos por uma volta inteira do anel, são lidos como zero;
//   - sem estalos na volta do anel: a cópia é dividida em dois pedaços quando
//     atravessa o fim do vetor, então a sequência de amostras é contínua;
//   - leitor mais rápido que o escritor: o trecho ainda não escrito sai como
//     zero, nunca como sobra de uma volta antiga;
//   - buraco na escrita (o app parou de tocar e voltou depois): o intervalo
//     pulado é preenchido com zero, para não reaparecer áudio velho.
//
// Fio de execução: escrever() e ler() são chamados pelo fio de tempo real do
// dispositivo (o coreaudiod serializa as operações de entrada e saída de um
// mesmo dispositivo). pedirLimpeza() pode vir de qualquer fio: ela só marca um
// pedido atômico, atendido na próxima escrita ou leitura. Nada aqui aloca
// memória ou trava depois do construtor.
//
// Este arquivo não depende do CoreAudio, para poder ser testado sozinho.

#pragma once

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <cstring>
#include <vector>

namespace praxis {

class AnelAmostras
{
public:
    //! @param capacidadeQuadros quantos quadros (um quadro = uma amostra de cada
    //!        canal) o anel guarda. Deve ser bem maior que a distância entre o
    //!        tempo de saída e o de entrada (alguns milhares de quadros).
    //! @param canais número de canais intercalados (2 = estéreo).
    AnelAmostras(uint32_t capacidadeQuadros, uint32_t canais)
        : capacidade_(capacidadeQuadros > 0 ? capacidadeQuadros : 1)
        , canais_(canais > 0 ? canais : 1)
        , amostras_(size_t(capacidade_) * canais_, 0.0f)
    {
    }

    uint32_t capacidade() const
    {
        return capacidade_;
    }

    uint32_t canais() const
    {
        return canais_;
    }

    //! Pede para esvaziar o anel (por exemplo, quando o primeiro cliente começa a
    //! tocar ou gravar, ou quando a taxa de amostragem muda). Seguro em qualquer
    //! fio; atendido na próxima escrita ou leitura.
    void pedirLimpeza()
    {
        limpezaPedida_.store(true, std::memory_order_release);
    }

    //! Escreve @p quadros quadros intercalados a partir do tempo @p tempo.
    void escrever(int64_t tempo, const float* dados, uint32_t quadros)
    {
        atenderLimpeza();

        if (quadros == 0 || dados == nullptr) {
            return;
        }

        // Bloco maior que o anel: só os últimos "capacidade" quadros cabem.
        if (quadros > capacidade_) {
            const uint32_t pular = quadros - capacidade_;
            dados += size_t(pular) * canais_;
            tempo += pular;
            quadros = capacidade_;
        }

        const int64_t fimNovo = tempo + quadros;

        if (vazio_) {
            inicio_ = tempo;
            fim_ = tempo;
            vazio_ = false;
        } else if (tempo > fim_ + int64_t(capacidade_) ||
                   fimNovo < fim_ - int64_t(capacidade_)) {
            // Salto grande para frente (pausa longa) ou para trás (relógio
            // reiniciado): nada do que está guardado continua valendo.
            inicio_ = tempo;
            fim_ = tempo;
        } else if (tempo > fim_) {
            // Buraco curto: preenche com silêncio para não sobrar áudio de uma
            // volta antiga entre o fim anterior e o começo deste bloco.
            zerarIntervalo(fim_, tempo);
            fim_ = tempo;
        }

        copiarParaAnel(tempo, dados, quadros);

        if (tempo < inicio_) {
            inicio_ = tempo;
        }
        fim_ = std::max(fim_, fimNovo);
        inicio_ = std::max(inicio_, fim_ - int64_t(capacidade_));
    }

    //! Lê @p quadros quadros intercalados a partir do tempo @p tempo em
    //! @p destino. O que não estiver guardado no anel sai como silêncio.
    //! A leitura não apaga nada: vários apps podem gravar o mesmo trecho.
    void ler(int64_t tempo, float* destino, uint32_t quadros)
    {
        atenderLimpeza();

        if (quadros == 0 || destino == nullptr) {
            return;
        }

        const int64_t fimPedido = tempo + quadros;

        if (vazio_) {
            std::memset(destino, 0, size_t(quadros) * canais_ * sizeof(float));
            return;
        }

        const int64_t a = std::max(tempo, inicio_);
        const int64_t b = std::min(fimPedido, fim_);

        if (a >= b) {
            std::memset(destino, 0, size_t(quadros) * canais_ * sizeof(float));
            return;
        }

        // Antes do trecho válido: silêncio.
        if (a > tempo) {
            std::memset(destino, 0, size_t(a - tempo) * canais_ * sizeof(float));
        }

        copiarDoAnel(a, destino + size_t(a - tempo) * canais_, uint32_t(b - a));

        // Depois do trecho válido (ainda não escrito): silêncio.
        if (fimPedido > b) {
            std::memset(destino + size_t(b - tempo) * canais_,
                0,
                size_t(fimPedido - b) * canais_ * sizeof(float));
        }
    }

    //! Tempo logo depois do último quadro escrito (só para testes e
    //! diagnóstico).
    int64_t fimEscrito() const
    {
        return fim_;
    }

private:
    uint32_t posicao(int64_t tempo) const
    {
        const int64_t c = capacidade_;
        int64_t r = tempo % c;
        if (r < 0) {
            r += c;
        }
        return uint32_t(r);
    }

    void atenderLimpeza()
    {
        if (limpezaPedida_.exchange(false, std::memory_order_acq_rel)) {
            vazio_ = true;
            inicio_ = 0;
            fim_ = 0;
            // Não é preciso zerar o vetor: com o anel vazio nada é lido dele, e
            // os buracos futuros são zerados na escrita.
        }
    }

    void zerarIntervalo(int64_t de, int64_t ate)
    {
        int64_t n = ate - de;
        if (n <= 0) {
            return;
        }
        if (n > int64_t(capacidade_)) {
            de = ate - capacidade_;
            n = capacidade_;
        }
        uint32_t pos = posicao(de);
        uint32_t restante = uint32_t(n);
        while (restante > 0) {
            const uint32_t pedaco = std::min(restante, capacidade_ - pos);
            std::memset(&amostras_[size_t(pos) * canais_],
                0,
                size_t(pedaco) * canais_ * sizeof(float));
            restante -= pedaco;
            pos = 0;
        }
    }

    void copiarParaAnel(int64_t tempo, const float* dados, uint32_t quadros)
    {
        uint32_t pos = posicao(tempo);
        uint32_t restante = quadros;
        while (restante > 0) {
            const uint32_t pedaco = std::min(restante, capacidade_ - pos);
            std::memcpy(&amostras_[size_t(pos) * canais_],
                dados,
                size_t(pedaco) * canais_ * sizeof(float));
            dados += size_t(pedaco) * canais_;
            restante -= pedaco;
            pos = 0;
        }
    }

    void copiarDoAnel(int64_t tempo, float* destino, uint32_t quadros) const
    {
        uint32_t pos = posicao(tempo);
        uint32_t restante = quadros;
        while (restante > 0) {
            const uint32_t pedaco = std::min(restante, capacidade_ - pos);
            std::memcpy(destino,
                &amostras_[size_t(pos) * canais_],
                size_t(pedaco) * canais_ * sizeof(float));
            destino += size_t(pedaco) * canais_;
            restante -= pedaco;
            pos = 0;
        }
    }

    const uint32_t capacidade_;
    const uint32_t canais_;
    std::vector<float> amostras_;

    // Trecho válido: [inicio_, fim_), com fim_ - inicio_ <= capacidade_.
    bool vazio_ = true;
    int64_t inicio_ = 0;
    int64_t fim_ = 0;

    std::atomic<bool> limpezaPedida_{false};
};

} // namespace praxis
