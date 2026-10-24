// Praxis — driver de áudio do macOS
// Licença MIT (veja LICENSE na raiz do projeto).
//
// Testes do anel de amostras (sem CoreAudio).

#include "AnelAmostras.hpp"
#include "Verificar.hpp"

#include <cstdint>
#include <random>
#include <vector>

using praxis::AnelAmostras;

namespace {

constexpr uint32_t kCanais = 2;

// Valor conhecido para cada (tempo, canal); nunca é zero para tempo >= 0, e é
// exato em ponto flutuante de 32 bits até alguns milhões de quadros.
float Sinal(int64_t tempo, uint32_t canal)
{
    return float(tempo * 2 + canal + 1);
}

std::vector<float> Bloco(int64_t tempo, uint32_t quadros)
{
    std::vector<float> v(size_t(quadros) * kCanais);
    for (uint32_t i = 0; i < quadros; i++) {
        for (uint32_t c = 0; c < kCanais; c++) {
            v[size_t(i) * kCanais + c] = Sinal(tempo + i, c);
        }
    }
    return v;
}

std::vector<float> Ler(AnelAmostras& anel, int64_t tempo, uint32_t quadros)
{
    // Começa com lixo para garantir que a leitura preenche tudo.
    std::vector<float> v(size_t(quadros) * kCanais, -12345.0f);
    anel.ler(tempo, v.data(), quadros);
    return v;
}

bool IgualAoSinal(const std::vector<float>& v, int64_t tempo, uint32_t de, uint32_t ate)
{
    for (uint32_t i = de; i < ate; i++) {
        for (uint32_t c = 0; c < kCanais; c++) {
            if (v[size_t(i) * kCanais + c] != Sinal(tempo + i, c)) {
                return false;
            }
        }
    }
    return true;
}

bool Silencio(const std::vector<float>& v, uint32_t de, uint32_t ate)
{
    for (size_t k = size_t(de) * kCanais; k < size_t(ate) * kCanais; k++) {
        if (v[k] != 0.0f) {
            return false;
        }
    }
    return true;
}

} // namespace

CASO("escrita e leitura no mesmo tempo devolvem as mesmas amostras")
{
    AnelAmostras anel(4096, kCanais);
    const auto b = Bloco(1000, 256);
    anel.escrever(1000, b.data(), 256);

    const auto lido = Ler(anel, 1000, 256);
    VERIFICAR(IgualAoSinal(lido, 1000, 0, 256));

    // Pedaço do meio.
    const auto meio = Ler(anel, 1100, 50);
    VERIFICAR(IgualAoSinal(meio, 1100, 0, 50));
}

CASO("anel novo e vazio: só silêncio")
{
    AnelAmostras anel(1024, kCanais);
    const auto lido = Ler(anel, 0, 512);
    VERIFICAR(Silencio(lido, 0, 512));
    const auto lido2 = Ler(anel, 987654, 100);
    VERIFICAR(Silencio(lido2, 0, 100));
}

CASO("volta do anel: leitura atravessando o fim do vetor é contínua")
{
    AnelAmostras anel(1024, kCanais);
    // Escreve 3 voltas inteiras e mais um pouco, em blocos de 100.
    for (int64_t t = 0; t < 3 * 1024 + 300; t += 100) {
        const auto b = Bloco(t, 100);
        anel.escrever(t, b.data(), 100);
    }
    // Bloco que começa 50 quadros antes do fim do vetor e termina 50 depois.
    const int64_t t0 = 3 * 1024 - 50;
    const auto lido = Ler(anel, t0, 100);
    VERIFICAR(IgualAoSinal(lido, t0, 0, 100));

    // Escrita que também atravessa a volta.
    AnelAmostras anel2(1024, kCanais);
    const auto b = Bloco(1000, 100); // posições 1000..1023 e 0..75
    anel2.escrever(1000, b.data(), 100);
    const auto lido2 = Ler(anel2, 1000, 100);
    VERIFICAR(IgualAoSinal(lido2, 1000, 0, 100));
}

CASO("sem estalos: escritor e leitor com blocos de tamanhos aleatórios, muitas voltas")
{
    AnelAmostras anel(2048, kCanais);
    std::mt19937 gerador(1234);
    std::uniform_int_distribution<uint32_t> tamanho(1, 700);

    // O escritor vai à frente; o leitor segue com atraso de ~1000 quadros,
    // como no coreaudiod (o tempo de saída fica à frente do de entrada).
    int64_t tempoEscrita = 0;
    int64_t tempoLeitura = -1000;
    bool tudoCerto = true;
    int64_t lidosComSinal = 0;

    while (tempoEscrita < 200000) {
        const uint32_t ne = tamanho(gerador);
        const auto b = Bloco(tempoEscrita, ne);
        anel.escrever(tempoEscrita, b.data(), ne);
        tempoEscrita += ne;

        while (tempoLeitura + 700 < tempoEscrita - 200) {
            const uint32_t nl = tamanho(gerador);
            const auto lido = Ler(anel, tempoLeitura, nl);
            for (uint32_t i = 0; i < nl; i++) {
                const int64_t t = tempoLeitura + i;
                for (uint32_t c = 0; c < kCanais; c++) {
                    const float esperado = t < 0 ? 0.0f : Sinal(t, c);
                    if (lido[size_t(i) * kCanais + c] != esperado) {
                        tudoCerto = false;
                    }
                }
                if (t >= 0) {
                    lidosComSinal++;
                }
            }
            tempoLeitura += nl;
        }
    }
    VERIFICAR(tudoCerto);
    VERIFICAR(lidosComSinal > 190000);
}

CASO("leitor mais rápido que o escritor: o que ainda não foi escrito sai como silêncio")
{
    AnelAmostras anel(1024, kCanais);
    // Duas voltas antigas para encher o vetor de dados velhos.
    for (int64_t t = 0; t < 2048; t += 128) {
        const auto b = Bloco(t, 128);
        anel.escrever(t, b.data(), 128);
    }
    // Leitor pede [1948, 2148): 100 quadros escritos e 100 ainda não.
    const auto lido = Ler(anel, 1948, 200);
    VERIFICAR(IgualAoSinal(lido, 1948, 0, 100));
    VERIFICAR(Silencio(lido, 100, 200)); // nada de sobra da volta anterior

    // Leitor totalmente à frente.
    const auto frente = Ler(anel, 2500, 300);
    VERIFICAR(Silencio(frente, 0, 300));

    // O escritor alcança: agora o trecho aparece certo.
    const auto b = Bloco(2048, 200);
    anel.escrever(2048, b.data(), 200);
    const auto depois = Ler(anel, 2048, 200);
    VERIFICAR(IgualAoSinal(depois, 2048, 0, 200));
}

CASO("silêncio quando para de tocar e quando o trecho já foi sobrescrito")
{
    AnelAmostras anel(1024, kCanais);
    const auto b = Bloco(0, 3000); // maior que o anel: fica só o fim
    anel.escrever(0, b.data(), 3000);

    // Depois do último quadro escrito: silêncio para sempre.
    const auto depois = Ler(anel, 3000, 512);
    VERIFICAR(Silencio(depois, 0, 512));

    // Os últimos 1024 quadros estão lá.
    const auto fim = Ler(anel, 3000 - 1024, 1024);
    VERIFICAR(IgualAoSinal(fim, 3000 - 1024, 0, 1024));

    // Antes disso foi sobrescrito: silêncio, não dados de outra volta.
    const auto velho = Ler(anel, 1000, 500);
    VERIFICAR(Silencio(velho, 0, 500));

    // Leitura que pega um pouco de cada lado do início do trecho válido.
    const auto borda = Ler(anel, 3000 - 1024 - 10, 20);
    VERIFICAR(Silencio(borda, 0, 10));
    VERIFICAR(IgualAoSinal(borda, 3000 - 1024 - 10, 10, 20));
}

CASO("buraco na escrita: o intervalo pulado vira silêncio, sem áudio velho")
{
    AnelAmostras anel(1024, kCanais);
    const auto b1 = Bloco(0, 1024);
    anel.escrever(0, b1.data(), 1024);

    // O app ficou 476 quadros sem tocar e voltou.
    const auto b2 = Bloco(1500, 100);
    anel.escrever(1500, b2.data(), 100);

    const auto buraco = Ler(anel, 1024, 476);
    VERIFICAR(Silencio(buraco, 0, 476));

    const auto novo = Ler(anel, 1500, 100);
    VERIFICAR(IgualAoSinal(novo, 1500, 0, 100));

    // O que ainda cabe da primeira escrita continua valendo.
    const auto antigo = Ler(anel, 600, 424);
    VERIFICAR(IgualAoSinal(antigo, 600, 0, 424));

    // Pausa maior que o anel inteiro: nada do passado sobra.
    const auto b3 = Bloco(10000, 50);
    anel.escrever(10000, b3.data(), 50);
    const auto antes = Ler(anel, 10000 - 1024, 1024);
    VERIFICAR(Silencio(antes, 0, 1024));
    const auto agora = Ler(anel, 10000, 50);
    VERIFICAR(IgualAoSinal(agora, 10000, 0, 50));
}

CASO("relógio voltando para trás (reinício) descarta o que estava guardado")
{
    AnelAmostras anel(1024, kCanais);
    const auto b1 = Bloco(50000, 512);
    anel.escrever(50000, b1.data(), 512);

    const auto b2 = Bloco(0, 256);
    anel.escrever(0, b2.data(), 256);

    const auto lido = Ler(anel, 0, 256);
    VERIFICAR(IgualAoSinal(lido, 0, 0, 256));
    const auto velho = Ler(anel, 50000, 512);
    VERIFICAR(Silencio(velho, 0, 512));
    const auto entre = Ler(anel, 256, 256);
    VERIFICAR(Silencio(entre, 0, 256));
}

CASO("pedido de limpeza esvazia o anel")
{
    AnelAmostras anel(1024, kCanais);
    const auto b = Bloco(0, 512);
    anel.escrever(0, b.data(), 512);
    anel.pedirLimpeza();

    const auto lido = Ler(anel, 0, 512);
    VERIFICAR(Silencio(lido, 0, 512));

    // Volta a funcionar normalmente depois.
    const auto b2 = Bloco(700, 100);
    anel.escrever(700, b2.data(), 100);
    const auto lido2 = Ler(anel, 650, 150);
    VERIFICAR(Silencio(lido2, 0, 50));
    VERIFICAR(IgualAoSinal(lido2, 650, 50, 150));
}

CASO("dois apps gravando o mesmo trecho recebem o mesmo áudio")
{
    AnelAmostras anel(1024, kCanais);
    const auto b = Bloco(300, 200);
    anel.escrever(300, b.data(), 200);
    const auto primeiro = Ler(anel, 300, 200);
    const auto segundo = Ler(anel, 300, 200);
    VERIFICAR(IgualAoSinal(primeiro, 300, 0, 200));
    VERIFICAR(primeiro == segundo);
}

CASO("reescrita do mesmo trecho substitui o conteúdo")
{
    AnelAmostras anel(1024, kCanais);
    std::vector<float> zeros(200 * kCanais, 0.0f);
    anel.escrever(0, zeros.data(), 200);
    const auto b = Bloco(50, 100);
    anel.escrever(50, b.data(), 100);
    const auto lido = Ler(anel, 0, 200);
    VERIFICAR(Silencio(lido, 0, 50));
    VERIFICAR(IgualAoSinal(lido, 0, 50, 150));
    VERIFICAR(Silencio(lido, 150, 200));
}

int main()
{
    return verificar::RodarTodos();
}
