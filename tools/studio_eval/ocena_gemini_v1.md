# Ocena jakości wyników „studia” (model 4B) oraz trafności weryfikatora

Ocena wykonana na podstawie pliku `cases_for_judge.json` względem cytowanych fragmentów źródłowych `[n]` oraz wymogów z `p.md`.

---

## Ocena szczegółowa przypadków (0–15)

### Przypadek 0 — `summary` (`length: short`, `form: prose`, brak tematu)
- **Dokument:** `nauka/Notatki z wykładu — Podstawy ekonomii, popyt i podaż (materiał przykładowy).md`
- **Status:** `answered`

**Ocena wierszy:**
1. `Tekst dotyczy podstaw ekonomii, koncentrując się na popycie, podaży i równowadze rynkowej [1, 2].` *(weryfikator: `supported`)* — **POPRAWNY**. Tytuł wykładu w `[1]` brzmi dokładnie „Podstawy ekonomii — wykład 3: popyt, podaż i równowaga rynkowa”, a `[2]` rozwija temat popytu.
2. `Popyt to ilość dobra, jaką nabywcy chcą i mogą kupić, a prawo popytu mówi, że wzrost ceny powoduje spadek wielkości popytu [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (w krótkim streszczeniu pominięto doprecyzowanie *ceteris paribus* i „przy różnych poziomach ceny w określonym czasie”).
3. `Podaż to ilość dobra, jaką producenci chcą i mogą sprzedać, a prawo podaży mówi, że wzrost ceny powoduje wzrost wielkości podaży [3, 4].` *(weryfikator: `supported`)* — **POPRAWNY**. Cała treść znajduje się w `[4]` (cytat `[3]` jest zbędny — dotyczy wyłącznie popytu).
4. `Równowaga rynkowa występuje, gdy wielkość popytu jest równa wielkości podaży, a cena maksymalna poniżej tej równowagi prowadzi do niedoboru [5, 6].` *(weryfikator: `unsupported`)* — **POPRAWNY**. Definicja równowagi jest w `[5]`, a skutek ceny maksymalnej w `[6]`. **Fałszywy alarm weryfikatora.**

- **Opcje spełnione:** **TAK** (`short` = 3–4 zdania → są 4 zdania; `prose` → pełne zdania bez wypunktowań).
- **Użyteczność (student):** **3/5**. Streszczenie wierne, ale bardzo powierzchowne; obejmuje tylko definicje wstępne.
- **Ważne pominięcia:** Cały rozdział 5 (**elastyczność cenowa popytu**, na którą w dokumencie kładziono nacisk egzaminacyjny), rozdział 6 (**uwagi na egzamin i konsultacje**), funkcje ceny (`[1]`), czynniki przesuwające krzywe popytu i podaży (`[3, 4, 5]`), cena minimalna (`[6, 7]`).

---

### Przypadek 1 — `summary` (`length: long`, `form: points`, brak tematu)
- **Dokument:** `nauka/Notatki z wykładu — Podstawy ekonomii, popyt i podaż (materiał przykładowy).md`
- **Status:** `answered`

**Ocena wierszy:**
1. `Rynek to miejsce lub mechanizm, gdzie kupujący i sprzedający wymieniają dobra i usługi [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]`.
2. `Kupujący tworzą stronę popytową rynku, a sprzedający — stronę podażową [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]`.
3. `Na rynku doskonale konkurencyjnym działa wielu kupujących i sprzedających, a oferowane dobro jest jednorodne [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` (pominięto trzecią cechę: brak wpływu pojedynczego uczestnika na cenę).
4. `Cena pełni na rynku funkcje informacyjną (mówi o rzadkości dobra), motywacyjną (zachęca producentów do zwiększania produkcji, gdy cena rośnie) i alokacyjną (decyduje, kto otrzyma dobro) [1, 2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]`.
5. `Popyt to ilość dobra, jaką nabywcy chcą i mogą kupić przy różnych poziomach ceny w określonym czasie [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]`.
6. `Prawo popytu mówi, że wzrost ceny dobra powoduje spadek wielkości popytu, a spadek ceny — jej wzrost, co skutkuje ujemnym nachyleniem krzywej popytu [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]`.
7. `Zmiana ceny samego dobra powoduje ruch wzdłuż krzywej popytu, natomiast zmiana innych czynników przesuwa całą krzywą [2, 3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` i `[3]`.
8. `Do czynników przesuwających krzywą popytu należą m.in. dochody nabywców, ceny dóbr substytucyjnych i komplementarnych, gusty i preferencje, oczekiwania co do przyszłych cen oraz liczba nabywców na rynku [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` (słowo „m.in.” jest zbędne, bo w tekście wymieniono komplet 5 czynników).
9. `Dla większości dóbr wzrost dochodów zwiększa popyt (są to dobra normalne), a dobra, na które popyt spada przy wzroście dochodów, nazywane są dobrami niższego rzędu [3, 4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` i `[4]`.
10. `Podaż to ilość dobra, jaką producenci chcą i mogą sprzedać przy różnych poziomach ceny w określonym czasie [3].` *(weryfikator: `unsupported`)* — **ZLY_NUMER**. W `[3]` nie ma nic o podaży; definicja znajduje się we fragmencie **`[4]`**. (Weryfikator trafił).
11. `Prawo podaży mówi, że przy innych czynnikach niezmienionych wzrost ceny powoduje wzrost wielkości podaży, a krzywa podaży ma dodatnie nachylenie [4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[4]`.
12. `Równowaga rynkowa występuje przy cenie, gdzie wielkość popytu jest równa wielkości podaży, a ta cena nazywana jest ceną równowagi [5].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[5]`.
13. `Cena maksymalna ustalona przez państwo poniżej ceny równowagi prowadzi do niedoboru i kolejek, a cena minimalna ustalona powyżej ceny równowagi prowadzi do nadwyżki [6, 7].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[6]` i `[7]`.
14. `Elastyczność cenowa popytu pokazuje procentową zmianę wielkości popytu przy zmianie ceny o 1% [7].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[7]`.
15. `Jeżeli współczynnik elastyczności popytu jest większy od 1, popyt jest elastyczny, a przy popycie nieelastycznym podwyżka ceny zwiększa przychód sprzedawcy [7, 8].` *(weryfikator: `supported`)* — **POPRAWNY**. Pierwsza część jest w `[7]`, druga w `[8]`.

- **Opcje spełnione:** **NIE** (`long` wymaga 10–14 zdań/punktów, wygenerowano **15** wierszy; forma `points` zachowana).
- **Użyteczność (student):** **4/5**. Dobre i rzetelne pokrycie teorii, choć początek nadmiernie rozdrobniony (4 punkty na sekcję 1), a końcówka ściśnięta.
- **Ważne pominięcia:** Cała sekcja 6 (**wymagania na egzamin: wykłady 1–6, rysowanie krzywych, obowiązkowe zadanie rachunkowe z elastyczności oraz termin konsultacji** z `[8, 9]`), czynniki przesuwające krzywą podaży (`[4, 5]`), mechanizm nadwyżki/niedoboru (`[5, 6]`) oraz determinanty elastyczności cenowej (`[8]`).

---

### Przypadek 2 — `summary` (`length: standard`, `form: prose`, brak tematu)
- **Dokument:** `firma/Regulamin pracy — Przykład sp. z o.o. (dokument fikcyjny).txt`
- **Status:** `answered`

**Ocena wierszy:**
1. `Regulamin pracy Przykład sp. z o.o. określa organizację pracy oraz prawa i obowiązki pracodawcy i pracowników [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` (§ 1).
2. `Czas pracy wynosi 8 godzin na dobę i przeciętnie 40 godzin w pięciodniowym tygodniu pracy, rozliczany w okresie 3 miesięcy [1, 2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]` (§ 3 ust. 1).
3. `Praca w biurze odbywa się od poniedziałku do piątku, a pracownik rozpoczyna ją między 7:00 a 9:00 [1, 2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]` (§ 3 ust. 2).
4. `Dział obsługi klienta pracuje zmianowo (zmiana I: 7:00-15:00, zmiana II: 13:00-21:00), a grafik zmian ogłasza się najpóźniej 14 dni przed początkiem miesiąca [2, 3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` i `[3]` (§ 3 ust. 3).
5. `Pracownik może pracować zdalnie do 2 dni w tygodniu, pod warunkiem złożenia wniosku do czwartku poprzedniego tygodnia, z wyłączeniem okresu próbnego i ostatnich 3 dni roboczych miesiąca w dziale księgowości [2, 3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 4 ust. 1) i `[3]` (§ 4 ust. 1–2).
6. `Nieobecność należy zgłosić niezwłocznie, nie później niż do godziny 10:00 pierwszego dnia nieobecności [4, 5].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[4]` i `[5]` (§ 6 ust. 1).
7. `Spóźnienie powyżej 15 minut musi być odpracowane tego samego dnia lub w ciągu 7 dni za zgodą przełożonego [5].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[5]` (§ 7).
8. `Wynagrodzenie wypłaca się raz w miesiącu, najpóźniej 10. dnia następnego miesiąca, a regulamin wchodzi w życie po 2 tygodniach od podania go do wiadomości pracowników, tj. 1 marca 2026 r. [7, 8].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[7]` (§ 10 ust. 1, § 12) i `[8]` (§ 12).

- **Opcje spełnione:** **TAK** (`standard` = 5–8 zdań → jest 8 zdań; `prose` → zachowane).
- **Użyteczność (pracownik):** **4/5**. Konkretne, zwięzłe i bardzo rzetelne streszczenie najważniejszych zasad.
- **Ważne pominięcia:** Cały **Rozdział IV. Urlopy** (`[5, 6]`: terminy planu urlopów do 15 i 31 stycznia, 14 dni nieprzerwanego urlopu, urlop na żądanie do godz. 9:00, „dzień zdrowia” po 5 latach stażu), **przerwy w pracy** (`[3, 4]` § 5: 30 min wliczane + 5 min/godz. przy monitorze), informacja o automatycznym **e-ZLA** (`[4, 5]`), wypłata wynagrodzenia w poprzedzający dzień roboczy i pasek wypłaty (`[7]`) oraz zakres podmiotowy (umowa o pracę, `[1]`).

---

### Przypadek 3 — `quiz` (`length: standard`, brak tematu)
- **Dokument:** `nauka/Notatki z wykładu — Podstawy ekonomii, popyt i podaż (materiał przykładowy).md`
- **Status:** `answered`

**Ocena wierszy:**
1. `P: Jakie są trzy funkcje ceny na rynku? | O: informacyjną (mówi o rzadkości dobra), motywacyjną (zachęca producentów do zwiększania produkcji, gdy cena rośnie) i alokacyjną (decyduje, kto otrzyma dobro) [1, 2]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]` (błąd gramatyczny — odpowiedź w bierniku wklejona bezpośrednio z tekstu).
2. `P: Co jest potrzebne, aby pragnienie posiadania dobra stało się popytem? | O: zdolność do zapłaty [2]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]`.
3. `P: Jakie jest nachylenie krzywej popytu na wykresie? | O: ujemne: opada od lewej do prawej [2]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]`.
4. `P: Jakie czynniki przesuwają całą krzywą popytu? | O: dochody nabywców, ceny dóbr substytucyjnych i komplementarnych, gusty i preferencje, oczekiwania co do przyszłych cen, liczba nabywców na rynku [3]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]`.
5. `P: Co oznacza, że dobra substytucyjne zaspokajają tę samą potrzebę? | O: wzrost ceny masła zwiększa popyt na margarynę [3]` *(weryfikator: `supported`)* — **CZESCIOWO**. Sam przykład pochodzi z `[3]`, ale odpowiedź nie odpowiada ogólnie na pytanie „Co oznacza…”, tylko bezmyślnie przekleja drugi człon zdania z przykładem masła i margaryny.
6. `P: Jakie jest nachylenie krzywej podaży? | O: dodatnie: rośnie od lewej do prawej [4]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[4]`.
7. `P: Co powoduje przesunięcie krzywej podaży w prawo? | O: postęp technologiczny obniża koszty i przesuwa krzywą podaży w prawo [5]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[5]` (choć jako odpowiedź na otwarte pytanie pomija inne czynniki przesuwające krzywą z `[4, 5]`, jak spadek kosztów produkcji czy dotacje).
8. `P: Co dzieje się z ceną, gdy cena jest niższa od ceny równowagi? | O: powstaje niedobór (nadmiar popytu): kupujący konkurują o towar, więc cena ma tendencję do wzrostu [6]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[6]`.
9. `P: Kiedy popyt jest elastyczny? | O: jeżeli współczynnik elastyczności jest większy od 1: konsumenci silnie reagują na zmianę ceny [7]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[7]`.

- **Opcje spełnione:** **NIE** (`standard` dla `quiz` = 8 pytań, wygenerowano **9** pytań; format `P: … | O: …` zachowany).
- **Użyteczność (student):** **3/5**. Sprawdza podstawowe pojęcia, ale ma przekroczoną liczbę pytań, mechanicznie wycięte odpowiedzi i słabe pytanie 5.
- **Ważne pominięcia:** Brak pytań o dobra komplementarne/normalne/niższego rzędu (`[3, 4]`), cenę maksymalną i minimalną (`[6, 7]`), determinanty elastyczności oraz wpływ elastyczności na przychód sprzedawcy (`[8]`), a także o wymagania egzaminacyjne z sekcji 6 (`[8, 9]`).

---

### Przypadek 4 — `quiz` (`length: short`, brak tematu)
- **Dokument:** `firma/Zasady podróży służbowych — Przykład sp. z o.o. (dokument fikcyjny).txt`
- **Status:** `answered`

**Ocena wierszy:**
1. `P: Kto zatwierdza podróż służbową w przypadku wyjazdu zagranicznego? | O: Członek zarządu zatwierdza dodatkowo wyjazd zagraniczny [1].` *(weryfikator: `supported`)* — **CZESCIOWO**. W `[1]` (§ 1 ust. 1–2) wyjazd zatwierdza **bezpośredni przełożony**, a członek zarządu zatwierdza go **dodatkowo**. Odpowiedź pomija pierwszego decydenta, pozostawiając niepełną odpowiedź na pytanie „Kto zatwierdza…”.
2. `P: Jaki jest podstawowy środek transportu w podróżach krajowych do 300 km w jedną stronę? | O: Pociąg w klasie 2 [1, 2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]` (§ 2 ust. 1).
3. `P: Jaki jest limit kosztu noclegu w Warszawie? | O: 450 zł za dobę w Warszawie [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 3 ust. 1).
4. `P: W jakim terminie należy złożyć rozliczenie podróży? | O: W ciągu 14 dni od zakończenia podróży [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` (§ 5 ust. 1).
5. `P: Jakie są warunki, aby taksówkę można było rozliczyć? | O: Taksówkę rozlicza się wyłącznie na dojazd do i z dworca lub lotniska oraz po godzinie 22:00 [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 2 ust. 3).

- **Opcje spełnione:** **TAK** (`short` = 5 pytań → jest 5 pytań; format `P: … | O: …` zachowany).
- **Użyteczność (pracownik):** **4/5**. Praktyczne pytania sprawdzające codzienne zasady wyjazdów.
- **Ważne pominięcia:** Brak pytań o **diety i potrącenia za posiłki** (25%/50%/25%, `[3]`), **stawkę za samochód prywatny** (1,15 zł/km, zgoda przełożonego, `[1, 2]`), rezerwację noclegów przez dział administracji (`[2, 3]`), zwrot niewykorzystanej zaliczki i wymóg rachunków (`[3, 4]`) oraz termin 3 dni roboczych na zatwierdzenie wyjazdu (`[1]`).

---

### Przypadek 5 — `glossary` (brak opcji, brak tematu)
- **Dokument:** `nauka/Notatki z wykładu — Podstawy ekonomii, popyt i podaż (materiał przykładowy).md`
- **Status:** `answered`

**Ocena wierszy:**
1. `Rynek — miejsce albo mechanizm, w którym kupujący i sprzedający wymieniają dobra i usługi [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]`.
2. `Strona popytowa rynku — tworzona przez kupujących [1].` *(weryfikator: `unsupported`)* — **POPRAWNY**. W `[1]`: „Kupujący tworzą stronę popytową rynku”. **Fałszywy alarm weryfikatora.**
3. `Strona podażowa — tworzona przez sprzedających [1].` *(weryfikator: `unsupported`)* — **POPRAWNY**. W `[1]`: „a sprzedający — stronę podażową”. **Fałszywy alarm weryfikatora.**
4. `Cena — pełni na rynku funkcje informacyjną (mówi o rzadkości dobra), motywacyjną (zachęca producentów do zwiększania produkcji, gdy cena rośnie) i alokacyjną (decyduje, kto otrzyma dobro) [1, 2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]`.
5. `Popyt — ilość dobra, jaką nabywcy chcą i mogą kupić przy różnych poziomach ceny w określonym czasie [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]`.
6. `Prawo popytu — przy innych czynnikach niezmienionych wzrost ceny dobra powoduje spadek wielkości popytu, a spadek ceny — jej wzrost [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]`.
7. `Krzywa popytu — ma nachylenie ujemne: opada od lewej do prawej [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]`.
8. `Dobra substytucyjne — zaspokajają tę samą potrzebę, np. masło i margaryna [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]`.
9. `Dobra komplementarne — używa się razem, np. drukarka i tusz [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]`.
10. `Dobra normalne — dla większości dóbr wzrost dochodów zwiększa popyt [4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[4]`.
11. `Dobra niższego rzędu — dobra, na które popyt spada, gdy dochody rosną [4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[4]`.
12. `Podaż — ilość dobra, jaką producenci chcą i mogą sprzedać przy różnych poziomach ceny w określonym czasie [3].` *(weryfikator: `unsupported`)* — **ZLY_NUMER**. W `[3]` nie ma definicji podaży; znajduje się ona we fragmencie **`[4]`**. (Weryfikator trafił).
13. `Prawo podaży — przy innych czynnikach niezmienionych wzrost ceny powoduje wzrost wielkości podaży [4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[4]`.
14. `Równowaga rynkowa — występuje przy cenie, przy której wielkość popytu jest równa wielkości podaży [5].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[5]`.
15. `Elastyczność cenowa popytu — pokazuje, o ile procent zmieni się wielkość popytu, gdy cena zmieni się o 1% [7].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[7]`.

- **Opcje spełnione:** **TAK** (format `Termin — wyjaśnienie` zachowany).
- **Użyteczność (student):** **4/5**. Bardzo dobry, uporządkowany słowniczek pojęć z wykładu.
- **Ważne pominięcia:** Brak haseł dla pojęć: **rynek doskonale konkurencyjny** (`[1]`), **krzywa podaży** (`[4]`), **cena i ilość równowagi** (`[5]`), **nadwyżka (nadmiar podaży)** i **niedobór (nadmiar popytu)** (`[5, 6]`), **cena maksymalna** i **cena minimalna** (`[6, 7]`), **popyt elastyczny / nieelastyczny / elastyczność jednostkowa** (`[7, 8]`).

---

### Przypadek 6 — `glossary` (brak opcji, brak tematu)
- **Dokument:** `firma/Procedura ochrony danych osobowych — Przykład sp. z o.o. (dokument fikcyjny).txt`
- **Status:** `answered`

**Ocena wierszy:**
1. `Inspektorem ochrony danych (IOD) — w spółce jest Anna Nowak, kontakt: iod@przyklad.example, tel. wewnętrzny 214 [1]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` (§ 2 ust. 1; usterka gramatyczna hasła w narzędniku).
2. `Rejestr czynności przetwarzania — za rejestr odpowiada dział prawny; rejestr jest aktualizowany co najmniej raz na kwartał [2]` *(weryfikator: `unsupported`)* — **ZLY_NUMER**. W `[2]` brak tej informacji; znajduje się we fragmencie **`[1]`** (§ 2 ust. 2). (Weryfikator trafił).
3. `Dokumenty zawierające dane osobowe — drukuje się je wyłącznie na drukarkach z funkcją wydruku po zalogowaniu kartą [1, 2]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]` (§ 3 ust. 1).
4. `Wydruki niepotrzebne — niszczy się je w niszczarkach oznaczonych naklejką „P-4”; zabrania się wyrzucania ich do zwykłych koszy [2]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 3 ust. 2).
5. `Przesyłanie danych osobowych — nie wolno przesyłać ich przez prywatną pocztę ani prywatne komunikatory [2]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 3 ust. 3).
6. `Pliki z danymi klientów — wysyła się na zewnątrz wyłącznie w archiwum zaszyfrowanym hasłem, a hasło przekazuje się innym kanałem (SMS lub telefon) [2]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 3 ust. 3).
7. `Blokowanie komputera — zostawiony bez nadzoru komputer blokuje się skrótem Windows+L [2]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 3 ust. 4).
8. `Automatyczne blokowanie ekranu — ekran blokuje się automatycznie po 5 minutach bezczynności [2]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 3 ust. 4).
9. `Zgłaszanie naruszeń — pracownik zauważył możliwe naruszenie ochrony danych (np. zgubienie laptopa, wysłanie e-maila do złego adresata, nieuprawniony dostęp) i zgłasza je IOD niezwłocznie, nie później niż w ciągu 2 godzin od jego stwierdzenia, przez formularz w intranecie albo telefonicznie [2, 3]` *(weryfikator: `supported`)* — **POPRAWNY**. Treść pochodzi z `[2, 3]` (§ 4 ust. 1; niezręczność składniowa przez wycięcie słowa „który” zmieniająca warunek na opis zdarzenia).
10. `Ocena naruszenia — IOD ocenia naruszenie w ciągu 24 godzin i rekomenduje zarządowi, czy zgłosić je do Prezesa UODO [3]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` (§ 4 ust. 2).
11. `Zgłoszenie do Prezesa UODO — dokonuje się w terminie 72 godzin od stwierdzenia naruszenia [3]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` (§ 4 ust. 2).
12. `Wewnętrzny rejestr naruszeń — każde naruszenie, także niezgłoszone do UODO, wpisuje się do wewnętrznego rejestru naruszeń [3]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` (§ 4 ust. 3).
13. `Nagrania z monitoringu wejścia do biura — przechowuje się 30 dni, a następnie automatycznie nadpisuje [3, 4]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` i `[4]` (§ 5 ust. 1).
14. `Szkolenie z ochrony danych — każdy nowy pracownik przechodzi szkolenie w ciągu 7 dni od rozpoczęcia pracy; szkolenie przypominające odbywa się raz w roku [4, 5]` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[4]` i `[5]` (§ 6).

- **Opcje spełnione:** **TAK** (formalnie zachowano układ z myślnikiem, choć merytorycznie większość haseł to zasady postępowania pocięte na „pseudo-terminy” typu „Wydruki niepotrzebne”, a nie definicje słownikowe).
- **Użyteczność (pracownik):** **3/5**. Zawiera dużo przydatnych reguł, ale forma słowniczka jest nienaturalna i zawiera błędy gramatyczne.
- **Ważne pominięcia:** Pominięto dwa z trzech okresów retencji w § 5 (`[4]`): **dokumenty rekrutacyjne kandydatów niezatrudnionych** (3 mies. lub 12 mies. przy zgodzie) oraz **korespondencję reklamacyjną z klientami** (3 lata).

---

### Przypadek 7 — `simple` (`length: standard`, brak tematu)
- **Dokument:** `firma/Procedura ochrony danych osobowych — Przykład sp. z o.o. (dokument fikcyjny).txt`
- **Status:** `answered`

**Ocena wierszy:**
1. `Procedura ta określa zasady, jak należy przetwarzać dane osobowe klientów i pracowników oraz co robić w razie ich naruszenia [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` (§ 1).
2. `Inspektorem ochrony danych (osobą dbającą o ochronę danych) jest Anna Nowak [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` (§ 2 ust. 1; nawias jest dopuszczalnym uproszczeniem pojęcia IOD).
3. `Dokumenty z danymi osobowymi można drukować tylko na drukarkach, gdzie trzeba się najpierw zalogować kartą [1, 2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]` (§ 3 ust. 1).
4. `Wydruki, które nie są już potrzebne, trzeba niszczyć w specjalnych niszczarkach, a nie wyrzucać do zwykłych koszy [2].` *(weryfikator: `unsupported`)* — **POPRAWNY**. W `[2]` (§ 3 ust. 2) mowa o niszczarkach oznaczonych naklejką „P-4” i zakazie wyrzucania do zwykłych koszy. **Fałszywy alarm weryfikatora** (przez parafrazę „specjalnych”).
5. `Dane osobowe nie wolno wysyłać przez prywatne maile ani komunikatory [2].` *(weryfikator: `unsupported`)* — **POPRAWNY**. Zgodne merytorycznie z `[2]` (§ 3 ust. 3; błąd gramatyczny „Dane” zamiast „Danych”). **Fałszywy alarm weryfikatora.**
6. `Jeśli pracownik zauważy problem z danymi, musi zgłosić to IOD (Inspektorowi ochrony danych) nie później niż w ciągu 2 godzin [2, 3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` i `[3]` (§ 4 ust. 1).
7. `Nagrania z monitoringu wejścia do biura są przechowywane przez 30 dni, po czym są nadpisywane [3, 4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` i `[4]` (§ 5 ust. 1).

- **Opcje spełnione:** **TAK** (`standard` = 5–8 zdań → jest 7 zdań; język uproszczony).
- **Użyteczność (pracownik):** **3/5**. Przystępne wyjaśnienie, ale pomija wiele kluczowych zasad codziennego bezpieczeństwa i dane praktyczne (np. kontakt do IOD czy konkretne oznaczenie niszczarek P-4).
- **Ważne pominięcia:** **Szyfrowanie plików dla klientów i przekazywanie hasła innym kanałem** (`[2]`), **blokowanie komputera Windows+L i po 5 min bezczynności** (`[2]`), **oznaczenie niszczarki „P-4”** (`[2]`), **kontakt do IOD** (`[1]`), **termin 72h do Prezesa UODO i rejestr naruszeń** (`[3]`), **retencja dokumentów rekrutacyjnych i reklamacji** (`[4]`), **szkolenia (7 dni / raz w roku)** (`[4, 5]`).

---

### Przypadek 8 — `simple` (`length: short`, temat: `"urlop wypoczynkowy"`)
- **Dokument:** `Kodeks pracy (Dz.U. 2026 poz. 1245).txt`
- **Status:** `answered`

**Ocena wierszy:**
1. `Każdy pracownik ma prawo do corocznego, nieprzerwanego i płatnego urlopu wypoczynkowego [1].` *(weryfikator: `unsupported`)* — **POPRAWNY**. Zgodne z `[1]` (Art. 152 § 1). **Fałszywy alarm weryfikatora.**
2. `Pracownik nie może zrezygnować z tego prawa [1].` *(weryfikator: `unsupported`)* — **POPRAWNY**. W `[1]` (Art. 152 § 2): „Pracownik nie może zrzec się prawa do urlopu”. **Fałszywy alarm weryfikatora** (synonim „zrezygnować”).
3. `Wymiar urlopu zależy od stażu pracy: jest to 20 dni, jeśli pracownik pracuje krócej niż 10 lat, lub 26 dni, jeśli pracuje co najmniej 10 lat [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` (Art. 154 § 1).
4. `Osoba rozpoczynająca pracę po raz pierwszy nabywa prawo do urlopu stopniowo, z upływem każdego miesiąca pracy [1].` *(weryfikator: `unsupported`)* — **POPRAWNY**. Zgodne z `[1]` (Art. 153 § 1; uproszczenie bez ułamka 1/12 i wskazania roku kalendarzowego). **Fałszywy alarm weryfikatora.**

- **Opcje spełnione:** **TAK** (`short` = 3–4 zdania → są 4 zdania; język prosty; na temat „urlop wypoczynkowy”).
- **Użyteczność (pracownik):** **4/5**. Bardzo zrozumiałe wyjaśnienie najważniejszych zasad z Art. 152–154 KP.
- **Ważne pominięcia:** W dostarczonych fragmentach o urlopie wypoczynkowym pominięto **urlop na żądanie** (do 4 dni, `[4]` Art. 167²), **obowiązek wykorzystania urlopu w okresie wypowiedzenia** (`[4]` Art. 167¹), **zasadę 1/12 wymiaru** w pierwszym roku (`[1]` Art. 153 § 1) oraz szczególne zasady dla **młodocianych** (`[2]` Art. 205).

---

### Przypadek 9 — `claims` (brak opcji, brak tematu)
- **Dokument:** `nauka/Notatki z wykładu — Podstawy ekonomii, popyt i podaż (materiał przykładowy).md`
- **Status:** `answered`

**Ocena wierszy:**
1. `Rynek to miejsce albo mechanizm, w którym kupujący i sprzedający wymieniają dobra i usługi [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]`.
2. `Na rynku doskonale konkurencyjnym działa wielu kupujących i wielu sprzedających, oferowane dobro jest jednorodne, a żaden pojedynczy uczestnik nie ma wpływu na cenę [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]`.
3. `Cena pełni na rynku funkcję informacyjną (mówi o rzadkości dobra), motywacyjną (zachęca producentów do zwiększania produkcji, gdy cena rośnie) i alokacyjną (decyduje, kto otrzyma dobro) [1, 2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]`.
4. `Popyt to ilość dobra, jaką nabywcy chcą i mogą kupić przy różnych poziomach ceny w określonym czasie [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]`.
5. `Samo pragnienie posiadania dobra nie jest popytem — potrzebna jest także zdolność do zapłaty [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]`.
6. `Prawo popytu mówi, że przy innych czynnikach niezmienionych wzrost ceny dobra powoduje spadek wielkości popytu, a spadek ceny — jej wzrost [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]`.
7. `Zmiana ceny samego dobra powoduje ruch wzdłuż krzywej popytu, a zmiana innych czynników przesuwa całą krzywą [2, 3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` i `[3]`.
8. `Do czynników przesuwających krzywą popytu należą dochody nabywców, ceny dóbr substytucyjnych i komplementarnych, gusty i preferencje, oczekiwania co do przyszłych cen, liczba nabywców na rynku [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]`.
9. `Dobra substytucyjne zaspokajają tę samą potrzebę, np. masło i margaryna: wzrost ceny masła zwiększa popyt na margarynę [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]`.
10. `Podaż to ilość dobra, jaką producenci chcą i mogą sprzedać przy różnych poziomach ceny w określonym czasie [3].` *(weryfikator: `unsupported`)* — **ZLY_NUMER**. W `[3]` nie ma definicji podaży; znajduje się we fragmencie **`[4]`**. (Weryfikator trafił).
11. `Prawo podaży mówi, że przy innych czynnikach niezmienionych wzrost ceny powoduje wzrost wielkości podaży [4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[4]`.
12. `Cena maksymalna ustalona przez państwo poniżej ceny równowagi prowadzi do niedoboru i kolejek [6, 7].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[6]` i `[7]`.

- **Opcje spełnione:** **TAK** (w `opcje` brak dodatkowych parametrów, ale merytorycznie narzędzie `claims` nie zrealizowało podziału na **tezy / argumenty / ograniczenia** — zwróciło zwykłą płaską listę definicji i twierdzeń z pierwszej połowy wykładu).
- **Użyteczność (student):** **3/5**. Zestaw prawdziwych twierdzeń (poza 1 błędem numeracji), lecz nie daje struktury argumentacyjnej i urywa się w połowie dokumentu.
- **Ważne pominięcia:** Cały rozdział 5 (**elastyczność cenowa popytu** i wpływ na przychód, `[7, 8]`), **równowaga rynkowa, nadwyżka, niedobór i cena minimalna** (`[5, 6, 7]`), **czynniki przesuwające krzywą podaży** (`[4, 5]`), **dobra komplementarne/normalne/niższego rzędu** (`[3, 4]`), **uwagi egzaminacyjne** (`[8, 9]`) oraz wyraźne wskazanie ograniczeń (np. *ceteris paribus*).

---

### Przypadek 10 — `memo` (brak opcji, temat: `"elastyczność cenowa popytu"`)
- **Dokument:** `nauka/Notatki z wykładu — Podstawy ekonomii, popyt i podaż (materiał przykładowy).md`
- **Status:** `answered`

**Ocena wierszy:** *(Uwaga: w tym przypadku fragmenty zostały posortowane pod kątem wyszukiwania tematycznego — rozdział 5 znajduje się we fragmentach `[1]` i `[2]`).*
1. `Elastyczność cenowa popytu pokazuje, o ile procent zmieni się wielkość popytu, gdy cena zmieni się o 1% [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]`.
2. `Oblicza się ją jako stosunek procentowej zmiany wielkości popytu do procentowej zmiany ceny i podaje zwykle w wartości bezwzględnej [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]`.
3. `Jeżeli współczynnik elastyczności jest większy od 1, popyt jest elastyczny, co oznacza, że konsumenci silnie reagują na zmianę ceny [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]`.
4. `Jeżeli współczynnik elastyczności jest mniejszy od 1, popyt jest nieelastyczny, a reakcja jest słaba [1, 2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]`.
5. `Jeżeli współczynnik elastyczności jest równy 1, popyt ma elastyczność jednostkową [1, 2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]`.
6. `Przy popycie nieelastycznym podwyżka ceny zwiększa przychód sprzedawcy, a przy popycie elastycznym — zmniejsza go [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]`.

- **Opcje spełnione:** **TAK** (notatka ściśle na zadany temat).
- **Użyteczność (student):** **4/5**. Bardzo klarowna, trafna i bezbłędna notatka na temat.
- **Ważne pominięcia:** Pominięto dwie bardzo ważne dla studenta informacje obecne w `[2]` i `[3]`: **czynniki determinujące elastyczność** (dobra pierwszej potrzeby / brak substytutów / mały udział w dochodzie np. sól vs dobra luksusowe i mające wiele substytutów) oraz **wskazówkę egzaminacyjną** („Zadanie rachunkowe z elastyczności cenowej popytu pojawia się na każdym egzaminie”).

---

### Przypadek 11 — `memo` (brak opcji, temat: `"przepis na pierogi"`)
- **Dokument:** `nauka/Notatki z wykładu — Podstawy ekonomii, popyt i podaż (materiał przykładowy).md`
- **Status:** `refused`
- **Wiersze:** brak (`[]`, 0 wierszy).
- **Opcje spełnione:** **TAK**. Zgodnie z wymogiem temat spoza dokumentu został prawidłowo odrzucony (`status: refused`), bez halucynacji.
- **Użyteczność (student):** **5/5** (prawidłowa odmowa odpowiedzi poza zakresem źródeł).
- **Ważne pominięcia:** Nie dotyczy.

---

### Przypadek 12 — `summary` (`length: short`, `form: prose`, brak tematu)
- **Dokument:** `Ustawa o dostępie do informacji publicznej (Dz.U. 2022 poz. 902).txt`
- **Status:** `answered`

**Ocena wierszy:**
1. `Część 1: Teksty dotyczą Ustawy o dostępie do informacji publicznej [1].` *(weryfikator: `unsupported`)* — **POPRAWNY**. Tytuł ustawy znajduje się w `[1]`, choć prefiks „Część 1: Teksty dotyczą…” to rażący artefakt podziału map-reduce. **Fałszywy alarm weryfikatora** (wynikający z meta-sformułowania).
2. `Każdemu przysługuje prawo dostępu do informacji publicznej, które obejmuje uzyskanie informacji publicznej, wgląd do dokumentów urzędowych oraz dostęp do posiedzeń kolegialnych organów władzy publicznej [2, 3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` i `[3]` (Art. 2 ust. 1, Art. 3 ust. 1).
3. `Obowiązane do udostępniania informacji publicznej są m.in. władze publiczne, organy samorządów, podmioty wykonujące zadania publiczne, organizacje związkowe i pracodawcy reprezentatywni, a udostępnianie informacji odbywa się m.in. poprzez Biuletyn Informacji Publicznej [3, 4, 5, 21].` *(weryfikator: `supported`)* — **CZESCIOWO**. W `[4, 5]` mowa o **organizacjach związkowych i [organizacjach] pracodawców, reprezentatywnych**, natomiast wynik zmienia to na „pracodawcy reprezentatywni” (wypacza krąg podmiotów zobowiązanych z Art. 4 ust. 2) oraz uogólnia organy samorządów gospodarczych/zawodowych i jednostki samorządu terytorialnego.
4. `Część 2: Fragmenty dotyczą przepisów Ustawy o dostępie do informacji publicznej, regulujących m.in. obowiązki podmiotów udostępniających informacje oraz procedury związane z udostępnianiem informacji [24, 25, 26, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43].` *(weryfikator: `supported`)* — **CZESCIOWO**. Zacytowane fragmenty `[24–43]` rzeczywiście dotyczą obowiązków i procedur udostępniania, lecz **w żadnym z tych 16 fragmentów nie pojawia się nazwa „Ustawa o dostępie do informacji publicznej”** (jest ona wyłącznie w `[1]`), a samo zdanie to puste meta-streszczenie wyciekłe z etapu łączenia partii.
5. `Podmioty udostępniające informacje publiczne w Biuletynie Informacji Publicznej muszą oznaczać informacje danymi określającymi podmiot, osobę wytwórcę/odpowiedzialną oraz czas wytworzenia i udostępnienia [24].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[24]` (Art. 8 ust. 6 pkt 1–4).
6. `Udostępnianie informacji na wniosek następuje bez zbędnej zwłoki, nie później niż w terminie 14 dni, a w przypadku niemożności udostępnienia w tym terminie, podmiot musi powiadomić o przyczynach opóźnienia i terminie, nie dłuższym niż 2 miesiące [32, 33].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[32]` i `[33]` (Art. 13 ust. 1–2).

- **Opcje spełnione:** **NIE** (`short` = 3–4 zdania → wygenerowano **6** zdań; ponadto wynik zawiera sztuczne etykiety `Część 1:` / `Część 2:` nienależące do spójnej prozy).
- **Użyteczność (student / pracownik):** **2/5**. Dwa zdania to puste meta-komentarze („Teksty dotyczą…”, „Fragmenty dotyczą…”), jedno zniekształca podmioty ustawowe, a całość pomija większość kluczowych mechanizmów ustawy.
- **Ważne pominięcia:** **Ograniczenia prawa do informacji** (`[6–10]` Art. 5: informacje niejawne, tajemnice, prywatność, tajemnica przedsiębiorcy), **katalog informacji publicznych** (`[10–17]` Art. 6), **bezpłatność dostępu i opłaty** (`[20, 35–37]` Art. 7 ust. 2 i Art. 15), **odmowa w drodze decyzji, odwołania i skarga do sądu** (`[37–39, 41–42]` Art. 16–17, 21) oraz **odpowiedzialność karna za nieudostępnienie** (`[42–43]` Art. 23).

---

### Przypadek 13 — `facts` (brak opcji, brak tematu)
- **Dokument:** `nauka/Notatki z wykładu — Podstawy ekonomii, popyt i podaż (materiał przykładowy).md`
- **Status:** `answered`

**Ocena wierszy:**
1. `Egzamin obejmuje wykłady 1–6 [6, 9].` *(weryfikator: `supported`)* — **POPRAWNY**. Informacja znajduje się w `[9]` (oraz `[8]`); `[6]` jest błędnie doczepione (pomyłka numeru rozdziału `## 6` z numerem fragmentu).
2. `Konsultacje odbywają się we wtorki o 12:00 w sali 214 [6, 9].` *(weryfikator: `supported`)* — **POPRAWNY**. Jak wyżej: pełne pokrycie w `[9]`, a `[6]` dopisano omyłkowo z numeru rozdziału `## 6`.
3. `Przykład z wykładu: przy cenie 4 zł za kilogram jabłek nabywcy chcą kupić 100 ton, a sadownicy chcą sprzedać 100 ton [6].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[6]`.
4. `Przy cenie 6 zł popyt spada do 70 ton, a podaż rośnie do 130 ton [6].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[6]`.
5. `Cena maksymalna ustalona przez państwo poniżej ceny równowagi prowadzi do niedoboru i kolejek [6, 7].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[6]` i `[7]`.
6. `Cena minimalna ustalona powyżej ceny równowagi prowadzi do nadwyżki [6, 7].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[6]` i `[7]`.
7. `Popyt jest zwykle mniej elastyczny na dobra pierwszej potrzeby, dobra bez bliskich substytutów i dobra, na które wydajemy niewielką część dochodu (np. sól) [8].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[8]`.
8. `Popyt jest bardziej elastyczny na dobra luksusowe i na dobra z wieloma substytutami [8].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[8]`.
9. `Jeżeli współczynnik elastyczności jest większy od 1, popyt jest elastyczny [7].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[7]`.
10. `Jeżeli współczynnik elastyczności jest mniejszy od 1, popyt jest nieelastyczny [7, 8].` *(weryfikator: `unsupported`)* — **POPRAWNY**. Zdanie wprost występuje w `[7]` i `[8]`. **Fałszywy alarm weryfikatora.**
11. `Jeżeli współczynnik elastyczności jest równy 1, popyt ma elastyczność jednostkową [7, 8].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[7]` i `[8]`.
12. `W przypadku nadwyżki (nadmiaru podaży), cena ma tendencję do spadku [6].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[6]`.
13. `W przypadku niedoboru (nadmiaru popytu), cena ma tendencję do wzrostu [6].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[6]`.
14. `Wzrost ceny dobra powoduje spadek wielkości popytu, a spadek ceny — jej wzrost [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]`.
15. `Przy innych czynnikach niezmienionych wzrost ceny powoduje wzrost wielkości podaży [4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[4]`.
16. `Postęp technologiczny obniża koszty i przesuwa krzywą podaży w prawo [5].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[5]`.
17. `Wzrost podatku akcyzowego przesuwa krzywą podaży w lewo [5].` *(weryfikator: `unsupported`)* — **POPRAWNY**. W `[5]`: „Postęp technologiczny obniża koszty i przesuwa krzywą podaży w prawo, a wzrost podatku akcyzowego — w lewo”. **Fałszywy alarm weryfikatora.**
18. `Dobra substytucyjne zaspokajają tę samą potrzebę, np. masło i margaryna [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]`.
19. `Dobra komplementarne używa się razem, np. drukarka i tusz [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]`.
20. `Dla większości dóbr wzrost dochodów zwiększa popyt — są to dobra normalne [3, 4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` i `[4]`.

- **Opcje spełnione:** **TAK** (brak dodatkowych opcji w JSON; fakty wyciągnięte, choć wiersze 12–20 to już ogólne prawa i definicje, a nie twarde parametry/terminy/obowiązki).
- **Użyteczność (student):** **3/5**. Dobra ekstrakcja danych liczbowych i organizacyjnych w pierwszej części, ale druga połowa rozwadnia listę ogólnikami z notatek; widać też mylące doklejanie `[6]` do uwag egzaminacyjnych.
- **Ważne pominięcia:** **Nadwyżka 60 ton** przy cenie 6 zł (`[6]`), **konkretne wymagania egzaminacyjne** (`[8, 9]`: rysowanie krzywych, wyznaczanie równowagi, przesunięcia po zmianie dochodów/kosztów oraz **zadanie rachunkowe z elastyczności cenowej popytu na każdym egzaminie**), a także **1% zmiana ceny** i **wartość bezwzględna** ze wzoru elastyczności (`[7]`).

---

### Przypadek 14 — `facts` (brak opcji, brak tematu)
- **Dokument:** `firma/Zasady podróży służbowych — Przykład sp. z o.o. (dokument fikcyjny).txt`
- **Status:** `answered`

**Ocena wierszy:**
1. `Podróż służbową zatwierdza bezpośredni przełożony we wniosku w systemie kadrowym najpóźniej 3 dni robocze przed wyjazdem [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` (§ 1 ust. 1).
2. `Wyjazd zagraniczny zatwierdza dodatkowo członek zarządu [1].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` (§ 1 ust. 2).
3. `W podróżach krajowych do 300 km w jedną stronę podstawowym środkiem transportu jest pociąg w klasie 2 [1, 2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]` (§ 2 ust. 1).
4. `W podróżach krajowych powyżej 300 km podstawowym środkiem transportu jest pociąg w klasie 1 albo samolot w klasie ekonomicznej [1, 2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]` (§ 2 ust. 1).
5. `Samochód prywatny można wykorzystać tylko za zgodą przełożonego [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 2 ust. 2).
6. `Zwrot kosztów za samochód prywatny wynosi 1,15 zł za kilometr dla samochodu o pojemności silnika powyżej 900 cm³ [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 2 ust. 2).
7. `Taksówkę rozlicza się wyłącznie na dojazd do i z dworca lub lotniska oraz po godzinie 22:00 [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 2 ust. 3).
8. `Limit kosztu noclegu w kraju wynosi 450 zł za dobę w Warszawie [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 3 ust. 1).
9. `Limit kosztu noclegu w kraju wynosi 350 zł za dobę w pozostałych miastach [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 3 ust. 1).
10. `Rezerwacji dokonuje dział administracji [2, 3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` i `[3]` (§ 3 ust. 2).
11. `Samodzielna rezerwacja wymaga zgody przełożonego [2, 3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` i `[3]` (§ 3 ust. 2).
12. `Pracownikowi przysługuje dieta w wysokości określonej w przepisach o podróżach służbowych pracowników sfery budżetowej [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` (§ 4).
13. `Dietę zmniejsza się o 25% za śniadanie, jeżeli spółka zapewnia posiłek [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` (§ 4).
14. `Dietę zmniejsza się o 50% za obiad, jeżeli spółka zapewnia posiłek [3].` *(weryfikator: `unsupported`)* — **POPRAWNY**. Zgodne z `[3]` (§ 4: „dietę zmniejsza się o 25% za śniadanie, 50% za obiad i 25% za kolację”). **Fałszywy alarm weryfikatora.**
15. `Dietę zmniejsza się o 25% za kolację, jeżeli spółka zapewnia posiłek [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` (§ 4).
16. `Rozliczenie podróży składa się w systemie kadrowym w ciągu 14 dni od zakończenia podróży, ze zdjęciami lub skanami wszystkich rachunków [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` (§ 5 ust. 1).
17. `Zaliczkę niewykorzystaną zwraca się w tym samym terminie przelewem na rachunek spółki [3, 4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` i `[4]` (§ 5 ust. 2; odwołanie „w tym samym terminie” wymaga odczytania wiersza 16).
18. `Koszty nieudokumentowane rachunkiem nie podlegają zwrotowi, z wyjątkiem diet i ryczałtów [3, 4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` i `[4]` (§ 5 ust. 3).

- **Opcje spełnione:** **TAK** (kompletna lista terminów, kwot, limitów i obowiązków).
- **Użyteczność (pracownik):** **5/5**. Wzorcowa ściągawka z dokumentu — pokrywa wszystkie zasady, stawki i terminy (drobna uwaga: w wierszu 17 lepiej jawnie podać „w ciągu 14 dni” zamiast „w tym samym terminie”).
- **Ważne pominięcia:** Brak istotnych pominięć.

---

### Przypadek 15 — `facts` (brak opcji, brak tematu)
- **Dokument:** `firma/Procedura ochrony danych osobowych — Przykład sp. z o.o. (dokument fikcyjny).txt`
- **Status:** `answered`

**Ocena wierszy:**
1. `Pracownik, który zauważył możliwe naruszenie ochrony danych, zgłasza je IOD niezwłocznie, nie później niż w ciągu 2 godzin od jego stwierdzenia [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` (§ 4 ust. 1).
2. `IOD ocenia naruszenie w ciągu 24 godzin i rekomenduje zarządowi, czy zgłosić je do Prezesa UODO [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` (§ 4 ust. 2).
3. `Zgłoszenia do Prezesa UODO dokonuje się w terminie 72 godzin od stwierdzenia naruszenia [3].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` (§ 4 ust. 2).
4. `Nagrania z monitoringu wejścia do biura przechowuje się 30 dni, a następnie automatycznie nadpisuje [3, 4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[3]` i `[4]` (§ 5 ust. 1).
5. `Dokumenty rekrutacyjne kandydatów niezatrudnionych usuwa się po 3 miesiącach od zakończenia rekrutacji, chyba że kandydat zgodził się na udział w przyszłych rekrutacjach — wtedy po 12 miesiącach [4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[4]` (§ 5 ust. 2).
6. `Korespondencję z klientami w sprawie reklamacji przechowuje się 3 lata od zakończenia sprawy [4].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[4]` (§ 5 ust. 3).
7. `Każdy nowy pracownik przechodzi szkolenie z ochrony danych w ciągu 7 dni od rozpoczęcia pracy [4, 5].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[4]` i `[5]` (§ 6).
8. `Szkolenie przypominające odbywa się raz w roku [4, 5].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[4]` i `[5]` (§ 6).
9. `Rejestr czynności przetwarzania jest aktualizowany co najmniej raz na kwartał [2].` *(weryfikator: `unsupported`)* — **ZLY_NUMER**. W `[2]` nie ma informacji o rejestrze czynności przetwarzania; znajduje się ona we fragmencie **`[1]`** (§ 2 ust. 2). (Weryfikator trafił).
10. `Dokumenty zawierające dane osobowe drukuje się wyłącznie na drukarkach z funkcją wydruku po zalogowaniu kartą [1, 2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[1]` i `[2]` (§ 3 ust. 1).
11. `Wydruki niepotrzebne niszczy się w niszczarkach oznaczonych naklejką „P-4”; zabrania się wyrzucania ich do zwykłych koszy [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 3 ust. 2).
12. `Danych osobowych nie wolno przesyłać przez prywatną pocztę ani prywatne komunikatory [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 3 ust. 3).
13. `Pliki z danymi klientów wysyła się na zewnątrz wyłącznie w archiwum zaszyfrowanym hasłem, a hasło przekazuje się innym kanałem (SMS lub telefon) [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 3 ust. 3).
14. `Komputer zostawiony bez nadzoru blokuje się skrótem Windows+L [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 3 ust. 4).
15. `Ekran blokuje się automatycznie po 5 minutach bezczynności [2].` *(weryfikator: `supported`)* — **POPRAWNY**. Zgodne z `[2]` (§ 3 ust. 4).
16. `Inspektorem ochrony danych (IOD) w spółce jest Anna Nowak [2].` *(weryfikator: `unsupported`)* — **ZLY_NUMER**. Informacja o tym, kto jest IOD, znajduje się wyłącznie we fragmencie **`[1]`** (§ 2 ust. 1), a nie w `[2]`. (Weryfikator trafił).

- **Opcje spełnione:** **TAK** (bardzo dokładne wydobycie terminów i obowiązków).
- **Użyteczność (pracownik):** **4/5**. Praktyczny wykaz reguł i terminów, obniżony dwoma błędami cytowania (`[2]` zamiast `[1]`) i brakiem danych kontaktowych IOD.
- **Ważne pominięcia:** **Dane kontaktowe IOD** (`iod@przyklad.example`, tel. wewnętrzny 214 — `[1]` § 2 ust. 1), **odpowiedzialność działu prawnego** za rejestr czynności przetwarzania (`[1]` § 2 ust. 2), **kanał zgłaszania naruszeń do IOD** (formularz w intranecie lub telefonicznie — `[2, 3]` § 4 ust. 1) oraz **obowiązek wpisu każdego naruszenia do wewnętrznego rejestru naruszeń** (`[3]` § 4 ust. 3).

---

## 1. Tabela zbiorcza

| Przypadek | Narzędzie | Wiersze | POPRAWNY | CZESCIOWO | BLEDNY | ZLY_NUMER | Opcje spełnione | Użyteczność |
|---:|---|---:|---:|---:|---:|---:|:---:|---:|
| 0 | summary (`short`, `prose`) | 4 | 4 | 0 | 0 | 0 | tak | 3/5 |
| 1 | summary (`long`, `points`) | 15 | 14 | 0 | 0 | 1 | nie | 4/5 |
| 2 | summary (`standard`, `prose`) | 8 | 8 | 0 | 0 | 0 | tak | 4/5 |
| 3 | quiz (`standard`) | 9 | 8 | 1 | 0 | 0 | nie | 3/5 |
| 4 | quiz (`short`) | 5 | 4 | 1 | 0 | 0 | tak | 4/5 |
| 5 | glossary | 15 | 14 | 0 | 0 | 1 | tak | 4/5 |
| 6 | glossary | 14 | 13 | 0 | 0 | 1 | tak | 3/5 |
| 7 | simple (`standard`) | 7 | 7 | 0 | 0 | 0 | tak | 3/5 |
| 8 | simple (`short`) | 4 | 4 | 0 | 0 | 0 | tak | 4/5 |
| 9 | claims | 12 | 11 | 0 | 0 | 1 | tak* | 3/5 |
| 10 | memo | 6 | 6 | 0 | 0 | 0 | tak | 4/5 |
| 11 | memo (`refused`) | 0 | 0 | 0 | 0 | 0 | tak | 5/5 |
| 12 | summary (`short`, `prose`) | 6 | 4 | 2 | 0 | 0 | nie | 2/5 |
| 13 | facts | 20 | 20 | 0 | 0 | 0 | tak | 3/5 |
| 14 | facts | 18 | 18 | 0 | 0 | 0 | tak | 5/5 |
| 15 | facts | 16 | 14 | 0 | 0 | 2 | tak | 4/5 |

*\* W przypadku 9 brak parametrów w `opcje`, lecz sam cel narzędzia `claims` (rozróżnienie tez, argumentów i ograniczeń) nie został zrealizowany.*

---

## 2. Sumy dla wszystkich wierszy

- **Łączna liczba wierszy:** **159**
- **POPRAWNY:** **149** (93,71%)
- **CZESCIOWO:** **4** (2,52%)
- **BLEDNY:** **0** (0,00%)
- **ZLY_NUMER:** **6** (3,77%)
- **Opcje spełnione:** **13 / 16** przypadków (`tak`), **3 / 16** (`nie` — przekroczone limity w przypadkach 1, 3 i 12).
- **Średnia użyteczność:** **3,63 / 5** (58 pkt w 16 przypadkach).

---

## 3. Trafność automatycznego weryfikatora

W całym zbiorze weryfikator wystawił **18** oznaczeń `unsupported` oraz **141** oznaczeń `supported`.

1. **Wykrywalność błędów (`BLEDNY` / `ZLY_NUMER` oznaczonych jako `unsupported`):** **6 / 6 (100%)**.
   - Wszystkie 6 wierszy z błędnym numerem fragmentu (`ZLY_NUMER`) zostało poprawnie oflagowanych jako `unsupported`: przypadek 1 (wiersz 10), przypadek 5 (wiersz 12), przypadek 6 (wiersz 2), przypadek 9 (wiersz 10) oraz przypadek 15 (wiersze 9 i 16).
   - *(Uwaga poboczna: wszystkie 4 wiersze ocenione jako `CZESCIOWO` — przyp. 3 w. 5, przyp. 4 w. 1, przyp. 12 w. 3 i 4 — weryfikator przepuścił jako `supported`.)*

2. **Fałszywe alarmy (wiersze `POPRAWNY` oznaczone fałszywie jako `unsupported`):** **12 / 149 (8,05% poprawnych wierszy; aż 12 z 18 = 66,7% wszystkich alertów `unsupported`)**:
   - Przypadek 0, w. 4 (`[5, 6]`) — łączenie dwóch faktów z różnych fragmentów;
   - Przypadek 5, w. 2 i w. 3 (`[1]`) — zmiana szyku/formy przy definicjach strony popytowej i podażowej;
   - Przypadek 7, w. 4 i w. 5 (`[2]`) — uproszczenie leksykalne („specjalnych niszczarkach”, „prywatne maile”) w narzędziu `simple`;
   - Przypadek 8, w. 1, w. 2 i w. 4 (`[1]`) — synonimy i uproszczenia („Każdy pracownik”, „zrezygnować” zamiast „zrzec się”, „stopniowo” zamiast „1/12”) w narzędziu `simple`;
   - Przypadek 12, w. 1 (`[1]`) — meta-prefiks „Część 1: Teksty dotyczą…”;
   - Przypadek 13, w. 10 (`[7, 8]`) i w. 17 (`[5]`) — rozbicie punktu/zdania złożonego („a wzrost podatku akcyzowego — w lewo”);
   - Przypadek 14, w. 14 (`[3]`) — wydzielenie jednego elementu z wyliczenia (50% za obiad).

Weryfikator świetnie wyłapuje przesunięcia numerów chunków (`ZLY_NUMER`), ale jest nadwrażliwy na parafrazy i synonimy — szczególnie w narzędziu `simple` (w przypadku 8 odrzucił 3 z 4 poprawnych zdań).

---

## 4. Trzy najważniejsze problemy jakości i konkretne poprawki polecenia

### 1. Błędne przypisywanie numerów fragmentów na granicach chunków i mylenie z numeracją rozdziałów (`ZLY_NUMER` i zbędne cytaty)
- **Problem:** Model 4B systematycznie cytuje sąsiedni fragment (np. `[3]` zamiast `[4]` dla definicji podaży w przypadkach 1, 5 i 9; `[2]` zamiast `[1]` dla IOD i rejestru czynności przetwarzania w przypadkach 6 i 15), dopisuje zbędny numer sąsiedniego chunku (`[3, 4]` w przyp. 0 w. 3), a nawet myli numer sekcji dokumentu (`## 6. Na egzamin`) z numerem fragmentu (`[6, 9]` w przyp. 13 w. 1–2).
- **Konkretna poprawka polecenia:**
  > „Każdy fragment jest wyraźnie oznaczony na początku i końcu jako `[FRAGMENT n]` … `[/FRAGMENT n]`. Przy każdym wierszu podaj wyłącznie numery tych fragmentów `[n]`, w których treści **bezpośrednio** występuje każde stwierdzenie z tego wiersza. Nie zgaduj numeru na podstawie kolejności ani numerów rozdziałów w tekście (np. `§ 6` lub `## 6` to nie jest fragment `[6]`). Jeśli nie masz pewności, w którym z dwóch sąsiednich fragmentów leży zdanie, sprawdź dokładnie między znacznikami `[FRAGMENT n]` i `[/FRAGMENT n]`.”

### 2. Przekraczanie limitów długości, wyciek artefaktów map-reduce oraz ignorowanie specyfiki narzędzia (`claims`, `glossary`, `quiz`)
- **Problem:** W 3 z 6 przypadków z jawnym limitem długości model przekroczył limit (15 zamiast 10–14 w przyp. 1; 9 zamiast 8 w przyp. 3; 6 zamiast 3–4 w przyp. 12). W długim dokumencie (przyp. 12) do wyniku wyciekły śmieciowe nagłówki agregacji („Część 1: Teksty dotyczą…”, „Część 2: Fragmenty dotyczą…”) oraz bezwartościowy ciąg 16 cytatów `[24..43]` bez nazwy ustawy w tych fragmentach. Ponadto `claims` (przyp. 9) wygenerowało zwykłą listę zdań bez tez/argumentów/ograniczeń, `glossary` (przyp. 6) tworzyło pseudohasła z reguł, a `quiz` (przyp. 3 i 4) ucinał zdania źródłowe bez pełnej odpowiedzi na pytanie.
- **Konkretna poprawka polecenia:**
  - **Limit i brak meta-komentarzy (szczególnie w etapie reduce dla `summary`):**
    > „Zwróć DOKŁADNIE od {min} do {max} wierszy i przerwij po osiągnięciu limitu — nigdy nie przekraczaj {max}. Pisz wyłącznie o treści dokumentu: zakazane są meta-komentarze typu *'Część 1/2'*, *'Tekst dotyczy…'*, *'Fragmenty opisują…'*. Łącząc podsumowania części, usuń ich etykiety i zostaw przy każdym zdaniu tylko 1–3 konkretne numery `[n]`, które je potwierdzają.”
  - **Szablony narzędzi:**
    - Dla `claims`: > „Każdy wiersz sformułuj według schematu: `Teza: … | Argument/mechanizm: … | Ograniczenie/warunek: … [n]`.”
    - Dla `glossary`: > „Jako hasło przed myślnikiem podawaj wyłącznie nazwę pojęcia, skrót lub instytucję (1–4 słowa w mianowniku), a po myślniku jej definicję lub rolę — nie twórz haseł z całych czynności ani zakazów.”
    - Dla `quiz`: > „Odpowiedź po `|` musi wprost, kompletnie i poprawnie gramatycznie odpowiadać na zadane pytanie (nie wklejaj urwanych cytatów ani samych przykładów bez wyjaśnienia).”

### 3. „Efekt początku dokumentu” i pomijanie kluczowych sekcji praktycznych/końcowych
- **Problem:** Model zużywa limit wierszy na szczegółowe streszczanie pierwszych paragrafów i systematycznie gubi kluczowe sekcje ze środka lub końca dokumentu: w wykładzie z ekonomii pomija elastyczność cenową popytu oraz uwagi na egzamin i konsultacje (przyp. 0, 1, 3, 9), w regulaminie pracy cały dział urlopów i przerw (przyp. 2), w procedurze RODO blokowanie ekranu, hasłowanie plików, UODO i okresy retencji (przyp. 7), a w ustawie ograniczenia dostępu z art. 5, odwołania i sankcje karne (przyp. 12). Nawet w `memo` (przyp. 10) na temat elastyczności pominął determinanty elastyczności oraz informację, że zadanie z niej jest na każdym egzaminie.
- **Konkretna poprawka polecenia:**
  > „Rozłóż budżet wierszy równomiernie na **wszystkie** sekcje i rozdziały obecne we fragmentach (maksymalnie 1–2 wiersze na jedną sekcję w trybie `summary`/`quiz`/`claims`). Obowiązkowo uwzględnij: wyjątki, ograniczenia, sankcje, terminy i kwoty oraz wszelkie uwagi praktyczne lub egzaminacyjne z końcowych fragmentów. W narzędziu `memo` zbierz z dokumentu nie tylko definicję tematu, ale też wszystkie powiązane z nim przykłady, determinanty, wyjątki i uwagi praktyczne/egzaminacyjne.”
