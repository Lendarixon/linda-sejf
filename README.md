# Linda Sejf — cytuje źródło albo odmawia

**Jak NotebookLM, ale dokumenty nie opuszczają komputera.** Lokalny asystent do własnych dokumentów — notatek
z wykładów, skryptów, artykułów, regulaminów, procedur, umów i przepisów — na małym modelu językowym (Gemma-4-E4B, 4 mld
parametrów). Działa na zwykłym laptopie z Windows, bez internetu i bez konta; z kartą graficzną szybciej. Pytania, streszczenia,
fiszki, słowniczek, wyjaśnienie prostym językiem — każde zdanie ma odwołanie `[n]` do fragmentu dokumentu i jest sprawdzane
weryfikatorem zdań. Gdy pasującego fragmentu nie ma, Sejf odpowiada „Nie znaleziono odpowiedzi w dostępnych dokumentach”
zamiast zgadywać.

Dla kogo: dla każdego, kto pracuje z własnymi tekstami, których nie chce albo nie może wysłać do chmury — studenci i uczniowie
(notatki, skrypty), nauczyciele i badacze, organizacje pozarządowe, a także kancelarie, kadry, biura rachunkowe, urzędy
i placówki medyczne (tajemnica zawodowa, RODO).

Zgłoszenie do **Bielik Awards 2026**, kategoria „Najlepsze użycie modelu SLM (<10B)”.
Strona projektu: https://lindasejf.denmarkeast.cloudapp.azure.com/projekt/ · demo online (notatki z wykładu, dokumenty fikcyjnej firmy +
11 ustaw): https://lindasejf.denmarkeast.cloudapp.azure.com

## Instalacja (Windows 10/11, x64)

1. Pobierz `LindaSejf-Setup-<wersja>.exe` z zakładki **Releases** (ok. 50 MB). Instalator nie jest podpisany cyfrowo,
   więc SmartScreen może pokazać ostrzeżenie: „Więcej informacji” → „Uruchom mimo to”.
2. Zainstaluj (bez uprawnień administratora, do `%LOCALAPPDATA%\Programs\Linda Sejf`).
3. Uruchom **Linda Sejf** z menu Start. Za pierwszym razem pobiera modele z Hugging Face (ok. 8,2 GB, przypięte wersje,
   sprawdzane sumy SHA-256) i buduje indeks dokumentów (kilka minut). Potem otwiera się okno programu; zamknięcie okna zatrzymuje aplikację.

Program otwiera się we własnym oknie (WebView2 wbudowany w Windows 10/11; bez niego — w przeglądarce).
Po lewej **źródła** (dokumenty z folderu; można zaznaczyć, w których szukać, dodać plik przyciskiem „+ dodaj plik”
albo przeciągnąć go myszą, „odśwież” wczytuje nowe pliki), na środku rozmowa („kopiuj odpowiedź ze źródłami”,
„nowa rozmowa”), po prawej podgląd dokumentu z podświetlonym cytowanym fragmentem.
**Ustawienia**: folder dokumentów (okno wyboru folderu), tryb zwykły / ostrożny, karta graficzna (automatycznie / tylko procesor), wątki.
Szybkość (te same 3 pytania): karta graficzna Radeon RX 9070 XT ok. 4,5 s na odpowiedź (model ok. 1 s, reszta to wyszukiwanie na CPU); procesor desktopa 9–14 s; laptop Ryzen 7 5825U bez karty graficznej ok. 20–25 s.
**Studio** (jak w NotebookLM, na zaznaczonych dokumentach; przy każdym narzędziu można wpisać temat):
- **streszczenie** — krótko (3–4 zdania), standardowo (5–8) albo szczegółowo (10–14); akapit albo punkty;
- **pytania sprawdzające** — fiszki do nauki: pytanie, odpowiedź po kliknięciu; zapis do CSV (import w Anki albo Quizlet);
- **słowniczek pojęć** — pojęcia z wyjaśnieniem tylko z tekstu;
- **wyjaśnij prościej** — ta sama treść bez żargonu, liczby i wyjątki zostają;
- **terminy, kwoty i obowiązki** — każda pozycja jako pełne zdanie z odwołaniem;
- **tezy i argumenty** — tezy, argumenty i ograniczenia tekstu, bez oceny od modelu;
- **notatka na temat** — tylko ustalenia z dokumentów, bez własnych zaleceń modelu;
- **notatnik** — zapisane odpowiedzi i wyniki, kopiowanie ze źródłami, eksport do `.md` w `%LOCALAPPDATA%\LindaSejf\notatki`.

Krótkie dokumenty idą do modelu w całości (do 24 fragmentów); dłuższe (do ok. 140 fragmentów, np. skrypt albo krótka ustawa)
— w częściach, a wynik każdej części ma odwołania do jej fragmentów; z bardzo długich Sejf bierze 8 fragmentów pasujących
do tematu. Każde zdanie wyniku przechodzi przez ten sam weryfikator co odpowiedzi; niepotwierdzone są oznaczone.
Na karcie graficznej 3–8 s na wynik; dokument w 2 częściach ok. 20 s.

Jakość (16 zadań: notatki z wykładu, dokumenty firmy, Kodeks pracy, ustawa w częściach; skrypty, wyniki i ocena w `tools/studio_eval`):
Gemini 4 Hydrogen ocenił 159 wierszy wersji wstępnej: 149 poprawnych, 4 częściowo, 0 błędnych, 6 z prawdziwą treścią,
ale złym numerem fragmentu — weryfikator oznaczył wszystkie 6. Dlatego w 1.4.0 Sejf sam szuka fragmentu, który potwierdza
takie zdanie, i poprawia numer (oznaczone w wyniku): na tych samych zadaniach 14 poprawionych numerów, ręcznie sprawdzone
14/14 trafnie; weryfikator potwierdza 139 ze 149 wierszy (93%). Najsłabsze jest „wyjaśnij prościej”: przeredagowane zdania
weryfikator częściej uznaje za niepotwierdzone, choć według oceny są poprawne — interfejs o tym uprzedza.

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
| `sejf/tools.py` | studio: streszczenie, fiszki, słowniczek, prosty język, terminy, tezy, notatka (z weryfikacją zdań) |
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
