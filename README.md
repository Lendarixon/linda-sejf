# Linda Sejf — cytuje przepis albo odmawia

Lokalny asystent do dokumentów (prawo, akta biurowe) na małym modelu językowym. Działa na zwykłym laptopie z Windows,
bez karty graficznej i bez chmury. Każde zdanie odpowiedzi ma odwołanie `[n]` do fragmentu dokumentu, a gdy żaden
fragment nie pasuje do pytania, Sejf odpowiada „Nie znaleziono odpowiedzi w dostępnych dokumentach” zamiast zgadywać.

Zgłoszenie do **Bielik Awards 2026**, kategoria „Najlepsze użycie modelu SLM (<10B)”.
Strona projektu, film i prezentacja: https://lindasejf.denmarkeast.cloudapp.azure.com/projekt/ ·
demo online: https://lindasejf.denmarkeast.cloudapp.azure.com

## Instalacja (Windows 10/11, x64)

1. Pobierz `LindaSejf-Setup-1.0.0.exe` z zakładki **Releases** (ok. 50 MB). Instalator nie jest podpisany cyfrowo,
   więc SmartScreen może pokazać ostrzeżenie: „Więcej informacji” → „Uruchom mimo to”.
2. Zainstaluj (bez uprawnień administratora, do `%LOCALAPPDATA%\Programs\Linda Sejf`).
3. Uruchom **Linda Sejf** z menu Start. Za pierwszym razem pobiera modele z Hugging Face (ok. 8,2 GB, przypięte wersje,
   sprawdzane sumy SHA-256) i buduje indeks dokumentów (kilka minut). Potem otwiera się przeglądarka z aplikacją
   pod adresem `http://127.0.0.1:8765/`. Zamknięcie okna konsoli zatrzymuje aplikację.

Wymagania: 16 GB RAM, ok. 9 GB na dysku. Na start w folderze dokumentów (`corpus`, skrót „Folder dokumentów Linda Sejf”)
jest 11 polskich ustaw. Dodaj własne pliki `.txt`, `.md`, `.pdf` (z warstwą tekstu) lub `.docx` i uruchom aplikację ponownie.
Ustawienia: `%LOCALAPPDATA%\LindaSejf\config.json` (folder dokumentów, model, próg bramki, wątki).

## Uruchomienie ze źródeł (Windows / Linux)

```bash
pip install numpy onnxruntime tokenizers pypdf python-docx
python tools/download_models.py          # modele do ./models
# llama-server z https://github.com/ggml-org/llama.cpp/releases (build b12336) do ./bin/
python app.py
python -m pytest -q tests                # 24 testy
```

## Jak to działa

```
pytanie ─► wyszukiwanie: e5-small (znaczenie) + BM25 (słowa), łączone RRF, 30 kandydatów
        ─► polski reranker (sdadas/polish-reranker-base-ranknet) ocenia kandydatów
        ─► BRAMKA: najlepsza ocena < 0,975  →  „Nie znaleziono odpowiedzi…” (ok. 6 s, model nie jest uruchamiany)
        ─► Gemma-4-E4B Q6_K w llama.cpp odpowiada z odwołaniami [n] (albo odmawia)
        ─► weryfikator zdań (HerBERT, ONNX int8) oznacza zdania niepotwierdzone przez cytowany fragment
        ─► dziennik audytu z łańcuchem SHA-256, numery PESEL/NIP/REGON/IBAN maskowane w dzienniku
```

| plik | rola |
|---|---|
| `sejf/core.py` | bramka odmowy, prompt, podział na zdania, weryfikacja, dziennik audytu |
| `sejf/cite.py`, `sejf/labels.py` | odwołania `[n]`, etykiety „Kodeks pracy, art. 22²” |
| `sejf/retriever_simple.py` | samodzielna wyszukiwarka (ONNX, SQLite FTS5) |
| `sejf/retriever_localdocs.py` | adapter do komercyjnej wyszukiwarki Linda Probe (opcjonalny, nie jest częścią repozytorium) |
| `sejf/verifier_onnx.py`, `sejf/pii.py` | weryfikator zdań, maskowanie danych osobowych |
| `app.py`, `ui/index.html` | lokalny serwer i interfejs |
| `tools/download_models.py`, `tools/export_onnx.py` | pobieranie modeli, eksport ONNX |
| `tools/validate_retriever.py` | porównanie tej wyszukiwarki z Linda Probe na tych samych pytaniach (zbiory pytań niepubliczne) |
| `installer/` | instalator Inno Setup |

## Wyniki (z pomiarów w zgłoszeniu)

124 pytania „z życia” z odpowiedzią w ustawach + 31 pułapek, ślepa ocena dwóch sędziów-modeli (Gemini 4 Hydrogen, Bielik-11B):

| konfiguracja | odpowiada | błędne | odrzucone pułapki |
|---|---|---|---|
| Gemma-4-E4B bez bramki | — | 6–9% | 94% |
| **Gemma-4-E4B z bramką 0,9 (Linda Probe)** | 52% | **2%** | 97% (30/31) |
| Bielik-4.5B (naprawiony tokenizer) bez / z bramką | — / 62% | 27–32% / 15% | 55% / 84% |

Ograniczenia: sędziowie to modele, nie ludzie; bramka obniża zasięg (Sejf odpowiada na ok. połowę pytań); ewaluacja
tylko na tekstach ustaw. Pomiary w zgłoszeniu wykonano z wyszukiwarką Linda Probe; wyszukiwarka open source w tym
repozytorium została z nią porównana na tych samych 155 pytaniach — wynik w sekcji poniżej.

## Wyszukiwarka open source a Linda Probe (sprawdzone)

Wyszukiwarka w tym repozytorium (e5-small + BM25 + ten sam reranker) ma inny rozkład ocen niż Linda Probe, więc próg bramki
skalibrowaliśmy tą samą regułą co w zgłoszeniu: pierwszy próg, przy którym na zbiorze (a) (289 pytań Bielika-11B) nie przechodzi
żadna pułapka → **0,975** (domyślny w `app.py`). Sprawdzenie na niezależnym zbiorze (b), 124 pytania + 31 pułapek
(`tools/validate_retriever.py`; zbiory pytań nie są publiczne):

| | Linda Probe, próg 0,9 | open source, próg 0,975 |
|---|---|---|
| właściwy artykuł w top 5 (wszystkie pytania) | 71% | 88% |
| pytania przepuszczone przez bramkę do modelu | 63% | 44% |
| właściwy artykuł wśród przepuszczonych | 88,5% | 94,5% |
| pułapki zatrzymane już przez bramkę | 26/31 | 31/31 |

Wersja open source jest więc ostrożniejsza (rzadziej odpowiada, nie przepuszcza pułapek). Odsetka błędnych odpowiedzi z modelem
dla tej wyszukiwarki nie mierzyliśmy osobno — liczby 2% / 15% w tabeli wyżej dotyczą konfiguracji z Linda Probe.
Próg można zmienić w `config.json` (`min_rerank`).

## Wkład dla Bielika: tokenizer v3 w GGUF

Pliki GGUF Bielika v3 zapisują tokenizer BPE jako SentencePiece bez reguł scalania; llama.cpp dzieli wtedy polski tekst
inaczej niż przy treningu (0/41 zdań zgodnych). Poprawka metadanych (wagi bez zmian) daje 41/41 i podnosi poprawne odmowy
Bielika-4.5B z 60% do 87%. Skrypty: https://huggingface.co/Lindarixon/Linda-Sejf ·
zgłoszenie: https://huggingface.co/speakleash/Bielik-4.5B-v3.0-Instruct-GGUF/discussions/3

## Licencja

Kod: Apache-2.0 (`LICENSE`). Modele i biblioteki zewnętrzne: `THIRD_PARTY_NOTICES.md`.
To narzędzie wspiera pracę z dokumentami; nie jest poradą prawną.
