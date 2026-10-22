# Lista de verificação do Praxis (aplicativo em Rust)

Rodar **inteira** antes de cada versão. Marcar ✅ (passou), ❌ (falhou, com o defeito) ou ⏳ (ainda não testado). Guardar a prova: foto da janela e o registro de eventos (`PRAXIS_REGISTRO=arquivo`).

Onde testar:
- **Simulador** (`app/desktop/qa/simulador.html`, servido em `app/desktop`): a interface real com um motor de mentira; cenários `?cenario=ok | erro-inicio | erro-saida | atualizacao`.
- **lab2** (Linux, RTX 3050, placa de som Scarlett 2i2 de 32 bits): o aplicativo instalado pelo `.deb`.
- **Máquina virtual Windows 11** (sem placa de vídeo): o aplicativo instalado pelo `install.ps1`.

## 1. Instalação e atualização

| Item | Linux | Windows |
|---|---|---|
| Instalar pelo pacote (`.deb` / `.exe`) | ✅ 0.3.0 | ✅ 0.3.3 (pelo `install.ps1`) |
| Instalar pelo terminal (`install.sh` / `install.ps1`) | ⏳ (pede a senha do usuário) | ✅ 0.3.3 em 7 s, comando da página (`github.io/praxis/install.ps1`) |
| Bibliotecas da placa de vídeo baixadas e conferidas | ✅ | — (sem placa) |
| Microfone virtual instalado (VB-Cable) | — | ✅ (já instalado: detectado e mantido) |
| Atalho no menu de aplicativos e ícone | ⏳ | ✅ Menu Iniciar e área de trabalho; abre pelo ícone sem erro |
| Aviso de versão nova na janela | ✅ simulador | ⏳ |
| Botão "Atualizar": senha → atualiza → reabre | ⏳ | ⏳ |
| Atualização pelo sistema (`apt upgrade`) | ⏳ | — |
| Falha na atualização mostra o motivo e permite tentar de novo | ✅ simulador | ⏳ |
| Desinstalar remove tudo (inclui as bibliotecas da placa) | ⏳ | ✅ pasta, atalho e registro removidos |

## 2. Telas e navegação

| Item | Resultado |
|---|---|
| Abre nas configurações | ✅ |
| Iniciar → painel de tradução; configurações somem | ✅ |
| Parar → volta às configurações | ✅ (corrigido; antes ficava preso) |
| Erro ao iniciar → mensagem + volta às configurações + tentar de novo | ✅ |
| Erro durante a tradução → mensagem + volta às configurações | ✅ (corrigido) |
| Iniciar/parar 3 vezes seguidas | ✅ |
| Fechar e reabrir: configurações mantidas | ⏳ |
| Fechar durante a tradução remove os dispositivos virtuais | ✅ lab2 |

## 3. Botões e opções

| Item | Resultado |
|---|---|
| Idiomas: listas, idioma bloqueado desativado com motivo | ✅ |
| Mesmo idioma nos dois lados: aviso + Iniciar desativado | ✅ |
| Bilateral com idioma bloqueado do outro lado: aviso | ✅ |
| Microfone e saída: listas | ✅ |
| Ouvir a tradução / Estou de fone / Bilateral: salvam a configuração | ✅ |
| Tema claro/escuro | ✅ |
| Idioma da interface: todos os textos traduzidos | ✅ (corrigido: 39 textos em 14 idiomas) |
| Avançado: modelos oferecidos | ✅ (corrigido: turbo, large-v3, small; o Parakeet é escolhido sozinho por idioma) |
| Diagnóstico do reconhecedor | ✅ |

## 4. Tradução de verdade (equipamento real)

| Item | Linux | Windows |
|---|---|---|
| pt→en, saída só no microfone virtual | ✅ áudio claro | ✅ janela chega a "Traduzindo" (CABLE Output); motor traduz 3 frases reais, simultâneo em 3 de 3; fecha em 0,7 s |
| Ouvir a tradução na própria saída (Scarlett, 32 bits) | ❌ "formato não suportado: I32" (corrigido, falta reconferir) | ⏳ |
| Bilateral (a outra pessoa traduzida na minha saída) | ❌ mesmo defeito (falta reconferir) | ⏳ |
| Sem fone: a trava de eco não deixa a tradução voltar pelo microfone | ⏳ | ⏳ |
| Primeira vez sem internet: mensagem clara | ⏳ | ⏳ |
| Download interrompido: tenta de novo e retoma | ⏳ | ⏳ |

## 5. O que falta no aplicativo (existia na versão em Python ou é esperado)

1. **Modos de ativação**: só fala detectada automaticamente; faltam "falar segurando uma tecla" e "só acima de um volume".
2. **Escolha da voz** de saída (e testar a voz antes).
3. **Clonar a própria voz** (OmniVoice).
4. **Medidor de volume do microfone** (para saber se está ouvindo).
5. **Atualizar a lista de dispositivos** sem reabrir (ex.: plugou um fone depois).
6. **Trocar os idiomas de lado** com um botão.
7. **Mensagens do motor** (progresso e erros) só em português.
8. **macOS**: não há instalador do aplicativo novo.
9. **Windows**: bibliotecas da placa de vídeo NVIDIA e atualização automática pelo próprio aplicativo.
10. **Volume da tradução** na própria saída.
11. **Tradução sem placa de vídeo**: o modo automático escolhe o Argos, que come palavras ("you do not necessarily a yacht"). Medir o NLLB no processador e trocar se couber no tempo.
