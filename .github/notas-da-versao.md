## Novidades da 0.4.0

### A sua voz, clonada, dentro do Praxis
- **Grave uma vez (~30 s) e o Praxis clona a sua voz sozinho**, sem internet. Sem a voz gravada ele não traduz (a premissa: a tradução sai na sua voz).
- **Voz fiel** (OmniVoice) na **placa de vídeo**, por **Vulkan**: AMD, Intel e NVIDIA no Windows e no Linux, e AMD nos Macs Intel (pelo MoltenVK). Pronúncia medida com 0% de palavras erradas em inglês.
- **Voz leve**: ajuste fino da voz Supertonic à sua impressão de voz, feito no próprio computador, sem placa — simultânea em qualquer máquina.
- **Escolha automática**: na primeira vez, o Praxis mede a sua placa. Se ela gera a voz fiel rápido o bastante para tradução simultânea (ex.: RTX 3050), usa a fiel; se não (ex.: Radeon Pro 5500M de 2019), usa a leve. A tela diz qual e por quê; dá para forçar qualquer uma.
- Nos Macs com duas placas, a AMD fica ligada durante a tradução (antes, cada frase depois de uma pausa custava 1,2 s a mais).

### Tela nova
- **Tela principal** com só o que importa: idiomas, voz da tradução, a conversa e o botão de começar.
- **⚙ Configurações** em cartões: seu computador, áudio, sua voz, na chamada, mais opções.
- **Monitor de uso sempre à vista**: processador, cada placa de vídeo (uso e memória ocupada) e memória, **pelo nome**. O Praxis identifica o hardware sozinho — inclusive o tipo da memória (DDR4, DDR5…), a velocidade e o fabricante.
- **Monitoria** (ouvir a própria tradução) no painel da conversa, ligando e desligando sem parar a tradução.
- Gravação da voz: para sozinha aos 90 s e guarda; não abre o microfone duas vezes.

### Mais rápido e mais certo
- Atraso típico da tradução com voz: **3,7 s → 1,2 s** (com placa) — corta o silêncio das pontas de cada pedaço e acelera a voz mais cedo, até 1,2×.
- Tradução simultânea não perde mais frases nem fala frases inventadas pelo tradutor (espanhol 14,9% → 1,9% de erro, alemão 9,8% → 2,3%).
- A voz é gerada numa tarefa própria: o reconhecimento da fala seguinte não espera por ela.
- Erros da tela também vão para o monitor de erros (ⓘ Sobre → relatório).

## Instalar

| Sistema | Pelo terminal (sempre a versão mais nova) | Ou baixe aqui embaixo |
|---|---|---|
| **Linux** (Debian, Ubuntu, Mint e derivados) | `curl -fsSL https://disouz4-dev.github.io/praxis/install.sh \| bash` | `praxis_*_amd64.deb` (abra com dois cliques) |
| **Windows 10/11** | no PowerShell: `irm https://disouz4-dev.github.io/praxis/install.ps1 \| iex` — instala também o microfone virtual **Praxis Mic** | `Praxis_*_x64-setup.exe` (instale também o [VB-Cable](https://vb-audio.com/Cable/)) |
| **macOS** | em preparação | — |

Depois de instalado, **o Praxis se atualiza sozinho**: no Linux pela atualização do sistema (ou pelo aviso na janela) e no Windows pelo aviso na janela. A versão instalada e o botão "Verificar atualização" ficam em ⓘ Sobre.

No app de chamada (Discord, Meet, Zoom, WhatsApp…), escolha o microfone **Praxis Mic**. Guia completo: https://disouz4-dev.github.io/praxis/
