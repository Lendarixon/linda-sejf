WYKONAJ OD RAZU, bez planu. Bez wyszukiwania w internecie. Wynik zapisz do out.md w tym katalogu (po polsku).

Plik cases_for_judge.json: 16 wyników „studia” lokalnego asystenta dokumentów (model 4B). Każdy przypadek: narzędzie, opcje, temat, fragmenty źródłowe (numer → tekst) i wiersze wyniku z odwołaniami [n] oraz oceną automatycznego weryfikatora (supported/unsupported).
Narzędzia: summary (streszczenie; opcje length short=3–4 zdania, standard=5–8, long=10–14; form prose/points), quiz (pytania „P: … | O: …”; short=5, standard=8 pytań), glossary (słowniczek), simple (wyjaśnij prościej), claims (tezy/argumenty/ograniczenia), facts (terminy, kwoty, obowiązki), memo (notatka na temat). Przypadek z tematem „przepis na pierogi” powinien zostać odrzucony.

Dla KAŻDEGO wiersza oceń względem CYTOWANYCH fragmentów: POPRAWNY / CZESCIOWO / BLEDNY / ZLY_NUMER (treść prawdziwa, ale w innym fragmencie niż zacytowany). Dla każdego przypadku: czy opcje zostały spełnione (liczba zdań/pytań, forma), czy wynik jest użyteczny dla odbiorcy (student / pracownik) 1–5, ważne pominięcia.
Na końcu:
1. Tabela zbiorcza: przypadek, narzędzie, wiersze, POPRAWNY, CZESCIOWO, BLEDNY, ZLY_NUMER, opcje spełnione (tak/nie), użyteczność.
2. Sumy dla wszystkich wierszy.
3. Trafność weryfikatora: ile wierszy BLEDNY/ZLY_NUMER oznaczył jako unsupported, ile POPRAWNYCH oznaczył fałszywie.
4. 3 najważniejsze problemy jakości i konkretna poprawka polecenia dla każdego.
Bądź surowy i konkretny; nie zgaduj — oceniaj tylko względem fragmentów.
