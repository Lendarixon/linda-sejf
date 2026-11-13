"""Wykrywanie i maskowanie polskich danych osobowych z walidacją sum kontrolnych.

Maskujemy tylko to, co przechodzi walidację (PESEL, NIP, REGON, IBAN, dowód),
żeby nie niszczyć numerów artykułów, kwot i dat. E-mail i telefon - wzorcem.
"""
import re

_PESEL = re.compile(r"(?<!\d)(\d{11})(?!\d)")
_NIP = re.compile(r"(?<![\d-])(\d{3}-?\d{3}-?\d{2}-?\d{2}|\d{3}-?\d{2}-?\d{2}-?\d{3})(?![\d-])")
_REGON = re.compile(r"(?<!\d)(\d{9}|\d{14})(?!\d)")
_IBAN = re.compile(r"\b(?:PL)?\s?(\d{2}(?:\s?\d{4}){6})\b")
_DOWOD = re.compile(r"\b([A-Z]{3}\s?\d{6})\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"(?<!\d)(?:\+48\s?)?(?:\d{3}[\s-]?\d{3}[\s-]?\d{3})(?!\d)")


def _digits(s):
    return [int(c) for c in s if c.isdigit()]


def pesel_ok(s):
    d = _digits(s)
    if len(d) != 11:
        return False
    w = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    c = (10 - sum(a * b for a, b in zip(d, w)) % 10) % 10
    month = d[2] * 10 + d[3]
    return c == d[10] and (month % 20) in range(1, 13)


def nip_ok(s):
    d = _digits(s)
    if len(d) != 10:
        return False
    w = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    c = sum(a * b for a, b in zip(d, w)) % 11
    return c != 10 and c == d[9]


def regon_ok(s):
    d = _digits(s)
    if len(d) == 9:
        w = [8, 9, 2, 3, 4, 5, 6, 7]
    elif len(d) == 14:
        w = [2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8]
    else:
        return False
    c = sum(a * b for a, b in zip(d, w)) % 11 % 10
    return c == d[-1]


def iban_ok(s):
    d = "".join(c for c in s if c.isdigit())
    if len(d) != 26:
        return False
    # PL = 25 21
    num = d[2:] + "2521" + d[:2]
    return int(num) % 97 == 1


def dowod_ok(s):
    s = s.replace(" ", "")
    if len(s) != 9:
        return False
    val = [ord(c) - 55 for c in s[:3]] + [int(c) for c in s[3:]]
    w = [7, 3, 1, 0, 7, 3, 1, 7, 3]
    return sum(a * b for a, b in zip(val, w)) % 10 == val[3]


def find(text):
    """Zwraca listę (start, end, typ)."""
    spans = []
    for m in _IBAN.finditer(text):
        if iban_ok(m.group(1)):
            spans.append((m.start(), m.end(), "IBAN"))
    for m in _PESEL.finditer(text):
        if pesel_ok(m.group(1)):
            spans.append((m.start(1), m.end(1), "PESEL"))
    for m in _NIP.finditer(text):
        if nip_ok(m.group(1)):
            spans.append((m.start(1), m.end(1), "NIP"))
    for m in _REGON.finditer(text):
        if regon_ok(m.group(1)):
            spans.append((m.start(1), m.end(1), "REGON"))
    for m in _DOWOD.finditer(text):
        if dowod_ok(m.group(1)):
            spans.append((m.start(1), m.end(1), "DOWOD"))
    for m in _EMAIL.finditer(text):
        spans.append((m.start(), m.end(), "EMAIL"))
    for m in _PHONE.finditer(text):
        spans.append((m.start(), m.end(), "TELEFON"))
    # bez nakładania: dłuższe i wcześniejsze wygrywają
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    out, last = [], -1
    for s in spans:
        if s[0] >= last:
            out.append(s)
            last = s[1]
    return out


def mask(text):
    """Zwraca (tekst_zamaskowany, {typ: liczba})."""
    counts = {}
    res, pos = [], 0
    for a, b, t in find(text):
        res.append(text[pos:a])
        res.append(f"[{t}]")
        counts[t] = counts.get(t, 0) + 1
        pos = b
    res.append(text[pos:])
    return "".join(res), counts
