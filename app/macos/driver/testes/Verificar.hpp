// Praxis — driver de áudio do macOS
// Licença MIT (veja LICENSE na raiz do projeto).
//
// Mini estrutura de testes, sem dependências: cada caso é uma função; uma
// verificação que falha imprime arquivo, linha e expressão, e o programa termina
// com código 1 no fim.

#pragma once

#include <cstdio>
#include <functional>
#include <vector>

namespace verificar {

inline int& Falhas()
{
    static int falhas = 0;
    return falhas;
}

struct Caso
{
    const char* nome;
    std::function<void()> corpo;
};

inline std::vector<Caso>& Casos()
{
    static std::vector<Caso> casos;
    return casos;
}

struct Registrar
{
    Registrar(const char* nome, std::function<void()> corpo)
    {
        Casos().push_back({nome, std::move(corpo)});
    }
};

inline int RodarTodos()
{
    int casosComFalha = 0;
    for (const auto& caso : Casos()) {
        const int antes = Falhas();
        caso.corpo();
        const bool ok = Falhas() == antes;
        if (!ok) {
            casosComFalha++;
        }
        std::printf("[%s] %s\n", ok ? " ok " : "FALHOU", caso.nome);
    }
    std::printf("\n%zu casos, %d com falha\n", Casos().size(), casosComFalha);
    return casosComFalha == 0 ? 0 : 1;
}

} // namespace verificar

#define VERIF_JUNTAR2(a, b) a##b
#define VERIF_JUNTAR(a, b) VERIF_JUNTAR2(a, b)

#define CASO(nome)                                                                      \
    static void VERIF_JUNTAR(caso_, __LINE__)();                                        \
    static verificar::Registrar VERIF_JUNTAR(registro_, __LINE__)(                     \
        nome, VERIF_JUNTAR(caso_, __LINE__));                                           \
    static void VERIF_JUNTAR(caso_, __LINE__)()

#define VERIFICAR(expr)                                                                 \
    do {                                                                                \
        if (!(expr)) {                                                                  \
            verificar::Falhas()++;                                                      \
            std::printf("  %s:%d: falhou: %s\n", __FILE__, __LINE__, #expr);            \
        }                                                                               \
    } while (0)
