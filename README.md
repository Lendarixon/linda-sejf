# Linda Sejf — cytuje przepis albo odmawia

**Jak NotebookLM, ale dokumenty nie opuszczają komputera.** Lokalny asystent do własnych dokumentów organizacji
(regulaminy, procedury, umowy, akta, przepisy) na małym modelu językowym. Działa na zwykłym laptopie z Windows,
bez karty graficznej, bez internetu i bez konta. Każde zdanie odpowiedzi ma odwołanie `[n]` do fragmentu dokumentu,
a gdy pasującego fragmentu nie ma, Sejf odpowiada „Nie znaleziono odpowiedzi w dostępnych dokumentach” zamiast zgadywać.

Dla kogo: kancelarie, działy kadr, biura rachunkowe, urzędy, placówki medyczne — wszędzie tam, gdzie dokumentów nie wolno
wkleić do ChatGPT (tajemnica zawodowa, RODO), a Google ich nie zna.

Zgłoszenie do **Bielik Awards 2026**, kategoria „Najlepsze użycie modelu SLM (<10B)”.
Strona projektu: https://lindasejf.denmarkeast.cloudapp.azure.com/projekt/ · demo online (dokumenty fikcyjnej firmy +
11 ustaw): https://lindasejf.denmarkeast.cloudapp.azure.com

## Instalacja (Windows 10/11, x64)

1. Pobierz `LindaSejf-Setup-<wersja>.exe` z zakładki **Releases** (ok. 50 MB). Instalator nie jest podpisany cyfrowo,
   więc SmartScreen może pokazać ostrzeżenie: „Więcej informacji” → „Uruchom mimo to”.
2. Zainstaluj (bez uprawnień administratora, do `%LOCALAPPDATA%\Programs\Linda Sejf`).
3. Uruchom **Linda Sejf** z menu Start. Za pierwszym razem pobiera modele z Hugging Face (ok. 8,2 GB, przypięte wersje,
   sprawdzane sumy SHA-256) i buduje indeks dokumentów (kilka minut). Potem w przeglądarce otwiera się aplikacja
   `http://127.0.0.1:8765/`. Zamknięcie okna konsoli zatrzymuje aplikację.

Program otwiera się we własnym oknie (WebView2 wbudowany w Windows 10/11; bez niego — w przeglądarce).
Po lewej **źródła** (dokumenty z folderu; można zaznaczyć, w których szukać, dodać plik przyciskiem „+ dodaj plik”
albo przeciągnąć go myszą, „odśwież” wczytuje nowe pliki), na środku rozmowa („kopiuj odpowiedź ze źródłami”,
„nowa rozmowa”), po prawej podgląd dokumentu z podświetlonym cytowanym fragmentem.
**Ustawienia**: folder dokumentów (okno wyboru folderu), tryb zwykły / ostrożny, karta graficzna (automatycznie / tylko procesor), wątki.
Szybkość (te same 3 pytania): karta graficzna Radeon RX 9070 XT ok. 4,5 s na odpowiedź (model ok. 1 s, reszta to wyszukiwanie na CPU); procesor desktopa 9–14 s; laptop Ryzen 7 5825U bez karty graficznej ok. 20–25 s.
**Dziennik audytu**: ostatnie pytania (z zamaskowanymi PESEL/NIP/REGON/IBAN) i sprawdzenie łańcucha SHA-256.
Na start w folderze dokumentów są trzy fikcyjne dokumenty firmy „Przykład sp. z o.o.” i 11 polskich ustaw.
Obsługiwane pliki: `.txt`, `.md`, `.pdf` (z warstwą tekstu), `.docx`. Wymagania: 16 GB RAM, ok. 9 GB na dysku.
Ustawienia zapisują się w `%LOCALAPPDATA%\LindaSejf\config.json` (także `gguf`, `min_rerank`, `passages` do ręcznej edycji).

## Uruchomienie ze źródeł (Windows / Linux)

```bash
pip install numpy onnxruntime tokenizers pypdf python-docx
python tools/download_models.py          # modele do ./models
# llama-server z https://github.com/ggml-org/llama.cpp/releases (build b12336) do ./bin/
python app.py
python -m pytest -q tests
```

## Jak to działa

```
pytanie ─► wyszukiwanie: e5-small (znaczenie) + BM25 (słowa), łączone RRF, 30 kandydatów
        ─► polski reranker (sdadas/polish-reranker-base-ranknet) ocenia kandydatów i ich krótkie fragmenty (ustęp/punkt)
        ─► BRAMKA: najlepsza ocena < 0,7  →  „Nie znaleziono odpowiedzi…” (kilka sekund, model nie jest uruchamiany)
        ─► Gemma-4-E4B Q6_K w llama.cpp odpowiada z odwołaniami [n] (albo sama odmawia)
        ─► weryfikator zdań (HerBERT, ONNX int8) oznacza zdania niepotwierdzone przez cytowany fragment
        ─► dziennik audytu z łańcuchem SHA-256, numery PESEL/NIP/REGON/IBAN maskowane w dzienniku
```

Reranker widzi ok. 256 pierwszych tokenów fragmentu, więc zdanie na końcu długiego fragmentu dostawało niską ocenę
i bramka odmawiała mimo dobrego źródła. Dlatego oceniamy też krótkie okna wewnątrz najlepszych fragmentów i bierzemy
lepszą ocenę (`passages`); do modelu nadal trafia cały fragment.

| plik | rola |
|---|---|
| `sejf/core.py` | bramka odmowy, prompt, podział na zdania, weryfikacja, dziennik audytu |
| `sejf/cite.py`, `sejf/labels.py` | odwołania `[n]`, etykiety „Kodeks pracy, art. 22²” |
| `sejf/retriever_simple.py` | wyszukiwarka (ONNX, SQLite FTS5), indeks z pamięcią podręczną per plik, dodawanie plików w locie |
| `sejf/webapi.py` | lista dokumentów, podgląd, zawężenie do wybranych źródeł |
| `sejf/retriever_localdocs.py` | adapter do komercyjnej wyszukiwarki Linda Probe (opcjonalny, nie jest częścią repozytorium) |
| `sejf/verifier_onnx.py`, `sejf/pii.py` | weryfikator zdań, maskowanie danych osobowych |
| `app.py`, `ui/index.src.html` → `ui/index.html` | lokalny serwer i interfejs (`python ui/build_ui.py`) |
| `tools/` | pobieranie modeli, eksport ONNX, walidacja wyszukiwarki, źródła do ewaluacji |
| `installer/` | instalator Inno Setup |

## Wyniki

124 pytania „z życia” z odpowiedzią w ustawach + 31 pułapek (zbiór napisany przez Gemini w rolach kadrowej, urzędnika
i księgowej), ślepa ocena dwóch sędziów-modeli (Gemini 4 Hydrogen, Bielik-11B; zakres = obaj). Procent wszystkich
124 pytań; odmowa nie jest błędem. Gemma-4-E4B Q6_K:

| konfiguracja | odpowiada | poprawne | błędne | odrzucone pułapki |
|---|---|---|---|---|
| **ta wyszukiwarka + bramka 0,7 (domyślnie)** | **81%** | **60–65%** | **6–9%** | 28/31 |
| ta wyszukiwarka + bramka 0,9 | 69% | 52–57% | 5–6% | 28/31 |
| ta wyszukiwarka + bramka 0,95 (ostrożnie) | 60% | 45–50% | 4–6% | 29/31 |
| ta wyszukiwarka bez bramki | 83% | 60–67% | 7–10% | 28/31 |
| wyszukiwarka Linda Probe + bramka 0,9 (pierwsza wersja zgłoszenia) | 52% | 40–44% | 2% | 30/31 |

Właściwy artykuł w top 5 źródeł: 88% pytań (Linda Probe: 71%). Przy n = 124 niepewność to ok. ±4 pkt proc.
Dlaczego 0,7, a nie 0,9: ocena rerankera mocno zależy od sformułowania pytania („Do której godziny muszę zgłosić, że jestem
chory?” 0,78, a „…zgłosić przełożonemu, że jestem chory?” 0,98 — w regulaminie jest „nieobecność”, nie „choroba”). Próg 0,9
odrzucał więc wiele zwykłych pytań; przy 0,7 bramka zatrzymuje pytania wyraźnie spoza dokumentów, a resztę odmów robi model.
Ostrożniejszy tryb: Ustawienia → „ostrożny” (próg 0,95).

Ograniczenia: sędziowie to modele, nie ludzie; ewaluacja na ustawach — dokumenty firmowe w demo są fikcyjne i służą
tylko do demonstracji; pytania wymagające wnioskowania („limit hotelu w Krakowie”, gdy dokument mówi o „pozostałych
miastach”) reranker ocenia nisko i Sejf wtedy odmawia.

## Wkład dla Bielika: tokenizer v3 w GGUF

Pliki GGUF Bielika v3 zapisują tokenizer BPE jako SentencePiece bez reguł scalania; llama.cpp dzieli wtedy polski tekst
inaczej niż przy treningu (0/41 zdań zgodnych). Poprawka metadanych (wagi bez zmian) daje 41/41 i podnosi poprawne odmowy
Bielika-4.5B z 60% do 87%. Skrypty: https://huggingface.co/Lindarixon/Linda-Sejf ·
zgłoszenie: https://huggingface.co/speakleash/Bielik-4.5B-v3.0-Instruct-GGUF/discussions/3

## Licencja

Kod: Apache-2.0 (`LICENSE`). Modele i biblioteki zewnętrzne: `THIRD_PARTY_NOTICES.md`.
To narzędzie wspiera pracę z dokumentami; nie jest poradą prawną.
