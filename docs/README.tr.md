# ✦ Praxis

> **Bir mesaj. Her dil.**

<div align="center">

[🇧🇷 Português](../README.md) · [🇺🇸 English](README.en.md) · [🇪🇸 Español](README.es.md) · [🇫🇷 Français](README.fr.md) · [🇩🇪 Deutsch](README.de.md) · [🇮🇹 Italiano](README.it.md) · [🇷🇺 Русский](README.ru.md) · [🇨🇳 中文](README.zh.md) · [🇳🇱 Nederlands](README.nl.md) · [🇵🇱 Polski](README.pl.md) · [🇺🇦 Українська](README.uk.md) · **[🇹🇷 Türkçe](README.tr.md)** · [🇸🇦 العربية](README.ar.md) · [🇮🇳 हिन्दी](README.hi.md)

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://github.com/disouz4-dev/praxis)
[![License](https://img.shields.io/badge/Lisans-MIT-green)](LICENSE)
[![Offline](https://img.shields.io/badge/100%25-çevrimdışı-success)](https://github.com/disouz4-dev/praxis)

</div>

---

İletişim her zaman insanlığın en güçlü aracı olmuştur. Yine de dil, insanlar, kültürler ve fikirler arasındaki en büyük engellerden biri olmaya devam etmektedir.

**Praxis** bunu değiştirmek için yapıldı.

Fikir basit: iki kişinin her biri kendi dilinde doğal bir sohbet yapmasına izin vermek, diğeri ise her şeyi kendi ana dilinde duyarken — gerçek zamanlı olarak.

---

## Vizyon

Dünyanın her yerindeki insanlar arasında bağlamı, duyguyu ve akıcılığı koruyarak doğal konuşmalar yapabilen gerçek zamanlı bir sesli çeviri platformu oluşturmak.

## Misyon

Fikirlerin, bilginin ve ilişkilerin dil engeli olmadan sınırları aşabilmesi için dilsel engelleri ortadan kaldırmak.

## İlkeler

- Teknoloji insanları bir araya getirmelidir.
- Her sesin anlaşılmaya hakkı vardır.
- Dil bağlantıları sınırlamamalıdır.
- Çeviri o kadar doğal olmalıdır ki konuşmadan kaybolur.
- Bir mesaj herhangi bir dilde herkese ulaşabilir.

---

## Nasıl çalışır

Praxis işletim sisteminde bir **sanal mikrofon** oluşturur. Kendi dilinizde konuşursunuz; ses zaten çevrilmiş olarak çıkar — Discord, WhatsApp, Google Meet, OBS veya herhangi bir başka uygulamada seçilmeye hazır.

```
Gerçek mikrofon  →  VAD  →  Whisper ASR  →  Argos Translate  →  Piper TTS
                                                                        ↓
                                                       Sanal sink (Praxis_Out)
                                                                        ↓
                                                Praxis_Microfone  ←  Discord / Meet / OBS
```

Her şey **%100 yerel** çalışır — internet yok, bulut yok, hiçbir şey makinenizden çıkmaz.

---

## Etkinleştirme modları

| Mod | Açıklama |
|-----|----------|
| **Otomatik VAD** | Silero VAD konuştuğunuzu algılar ve otomatik olarak etkinleşir |
| **Gate eşiği** | Yalnızca ses seviyesi eşiğinin üzerinde etkinleşir |
| **Bas-Konuş (PTT)** | İletmek için bir düğmeye (klavye veya fare) basılı tutun |

---

## Desteklenen diller

### Çıktı dili (mevcut Piper sesiyle)

| Dil | Kod | Mevcut sesler |
|-----|-----|--------------|
| Português | `pt` | Faber, Cadu (BR) · Tugão (PT) |
| English | `en` | Lessac, Ryan (US) · Alan, Alba (GB) |
| Español | `es` | Sharvard (ES) · ALD (MX) |
| Français | `fr` | Siwis, Gilles |
| Deutsch | `de` | Thorsten, Karlsson, MLS |
| Italiano | `it` | Paola, Riccardo |
| Русский | `ru` | Dmitri, Irina |
| 中文 | `zh` | Huayan |
| Nederlands | `nl` | MLS |
| Polski | `pl` | Gosia |
| Українська | `uk` | Lada |
| Türkçe | `tr` | DFKI |
| العربية | `ar` | Kareem |
| हिन्दी | `hi` | Rohan |

### Giriş dili (Whisper tarafından tanınan)

Português · English · Español · Français · Deutsch · Italiano · 日本語 · 中文 · 한국어 · Русский · العربية · हिन्दी · Nederlands · Polski · Українська · Türkçe — ve Whisper'ın desteklediği düzinelerce başka dil.

> İki İngilizce olmayan dil arasındaki çeviri **otomatik İngilizce pivot** kullanır (örn. pt→it, pt→en→it şeklinde gider).

---

## Kurulum

```bash
git clone https://github.com/disouz4-dev/praxis.git
cd praxis
chmod +x install.sh && ./install.sh
```

Yükleyici yalıtılmış bir sanal ortam oluşturur, tüm bağımlılıkları (PyTorch, Whisper, Argos, Piper) yükler ve `praxis` komutunu global olarak kullanılabilir hale getirir.

### Gereksinimler

- PulseAudio veya PipeWire ile Linux
- Python 3.10+
- `pulseaudio-utils` (`pactl`, `parec`)
- CUDA'lı NVIDIA GPU (önerilir) veya CPU

---

## Kullanım

```bash
praxis
```

Yapılandırma penceresinde şunları seçin:
1. **Etkinleştirme modu** (VAD / Gate / PTT)
2. **Giriş mikrofonu**
3. **Kaynak ve hedef dil**
4. **Çıktı sesi** (⬇ İndir düğmesiyle ek sesler indirin)
5. **✦ Başlat**'a tıklayın

Arama uygulamanızda ses giriş cihazı olarak **Praxis_Microfone**'u seçin.

---

## Teknik boru hattı

| Aşama | Araç | Ayrıntılar |
|-------|------|-----------|
| Konuşma segmentasyonu | **Silero VAD** | Sessizliğe (200ms) veya maks. süreye (4s) göre kesme |
| Transkripsiyon | **faster-whisper** | Varsayılan `small` model; GPU int8_float16 / CPU int8 |
| Çeviri | **Argos Translate** | %100 çevrimdışı; ilk kullanımda dil çiftlerini indirir |
| Konuşma sentezi | **Piper TTS** | Hafif `.onnx` modeller; cümle başına paralel sentez |
| Ses çıktısı | **pacat + PulseAudio** | Sanal sink'e doğrudan enjeksiyon |

---

## Ses klonlama (OmniVoice)

**"Sesimi klonla"** sekmesi, herhangi bir sesi saniyeler içinde klonlamanıza olanak tanır — sadece 5–15 saniyelik bir ses klibi kaydedin veya içe aktarın. Eğitim yok, bekleme yok.

### Nasıl kullanılır

1. **🎙 Sesimi klonla** sekmesini açın
2. Profil için bir ad girin (örn. `Diego`)
3. **Seçenek A — Kaydet:** mikrofon düğmesine tıklayın ve kısa genel bir metin okuyun
   **Seçenek B — İçe aktar:** "Ses içe aktar"a tıklayın ve herhangi bir WAV/MP3/OGG/OPUS/M4A/FLAC/AAC dosyası seçin (WhatsApp sesli mesajları dahil)
4. Klonlanan sesi duymak için **Test**'e tıklayın
5. Varsayılan çıktı olarak etkinleştirmek için **Kullan**'a tıklayın

> Referans ses, en iyi klonlama kalitesi için otomatik olarak 15 saniyeye kısaltılır.

---

## Yol haritası

- [x] OmniVoice ile sıfır atışlı ses klonlama (eğitim gerektirmez)
- [x] Harici ses içe aktarma (WAV/MP3/OGG/OPUS/M4A ve daha fazlası)
- [ ] Tam çift yönlü çeviri (karşı tarafı da çevrilmiş duyma)
- [ ] Duraklatma/devam ettirme için sistem tepsisi simgesi ve global kısayol
- [ ] Daha da düşük gecikme için akış ses-to-ses
- [ ] `.deb` / `.desktop` paketleme
- [ ] Sunum ve konferanslar için LAN sunucu modu

---

<div align="center">

**Bir mesaj. Her dil.**

</div>
