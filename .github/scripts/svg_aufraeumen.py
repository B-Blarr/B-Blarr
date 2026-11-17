"""Entfernt aus den SVGs von github-profile-3d-contrib die Netzgrafik
(Commit, Issue, PullReq, Review, Repo) sowie Sterne und Forks und
faerbt einzelne Sprachen im Ring und in der Legende um.

Aufruf: python svg_aufraeumen.py datei1.svg datei2.svg ...

Das Skript bricht mit Exit-Code 1 ab, wenn es die erwarteten Teile nicht
findet. Dann hat sich der Aufbau der SVG geaendert (etwa nach einem Update
des Tools) und der Workflow schlaegt sichtbar fehl, statt still ein Bild
mit Netzgrafik zu veroeffentlichen.
"""

import os
import sys
import xml.etree.ElementTree as ET

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)

G = f"{{{NS}}}g"
TEXT = f"{{{NS}}}text"
TITLE = f"{{{NS}}}title"
RECT = f"{{{NS}}}rect"
PATH = f"{{{NS}}}path"

# Eigene Sprachfarben je Bild, damit Python sich klar von TypeScript abhebt
LANGUAGE_COLORS = {
    "3d-contrib-dark.svg": {"Python": "#2DD1B6"},
    "3d-contrib-light.svg": {"Python": "#42A090"},
}


def ist_netzgrafik(gruppe):
    # Die Netzgrafik ist die einzige Gruppe mit Achsen-Untergruppen.
    return any(kind.get("class") == "axis" for kind in gruppe.findall(G))


def ist_fusszeile(gruppe):
    # Die Fusszeile enthaelt Texte mit <title>, das sind genau
    # die Zahlen fuer Sterne und Forks.
    return any(text.find(TITLE) is not None for text in gruppe.findall(TEXT))


def recolor_language(root, language, color):
    """Setzt die Farbe einer Sprache im Ring und im Kaestchen der Legende.

    Gibt False zurueck, wenn die Sprache nur an einer der beiden Stellen
    gefunden wird. Fehlt sie an beiden, ist sie gerade nicht unter den
    fuenf groessten Sprachen und es gibt nichts zu tun.
    """
    slices = [
        path for path in root.iter(PATH)
        if path.find(TITLE) is not None
        and path.find(TITLE).text.rsplit(" ", 1)[0] == language
    ]
    markers = []
    for group in root.iter(G):
        labels = [child for child in group if child.tag == TEXT]
        rects = [child for child in group if child.tag == RECT]
        if not labels or len(labels) != len(rects):
            continue
        for label, rect in zip(labels, rects):
            if (label.text or "").strip() == language:
                markers.append(rect)

    if len(slices) != len(markers) or len(slices) > 1:
        print(f"{language}: Aufbau unerwartet (Ring {len(slices)}, Legende {len(markers)})")
        return False
    for pie_slice in slices:
        pie_slice.set("style", f"fill: {color};")
    for marker in markers:
        marker.set("fill", color)
    return True


def aufraeumen(pfad):
    baum = ET.parse(pfad)
    wurzel = baum.getroot()

    netz = [g for g in wurzel.iter(G) if ist_netzgrafik(g)]
    fuss = [g for g in wurzel.findall(G) if ist_fusszeile(g)]
    if len(netz) != 1 or len(fuss) != 1:
        print(f"{pfad}: Aufbau unerwartet (Netzgrafik {len(netz)}, Fusszeile {len(fuss)})")
        return False

    # Netzgrafik komplett entfernen
    eltern = {kind: el for el in wurzel.iter() for kind in el}
    eltern[netz[0]].remove(netz[0])

    # In der Fusszeile: die zwei Symbole (Stern und Gabel) sind Untergruppen,
    # die zwei Zahlen sind Texte mit <title>. Contributions und Datum bleiben.
    for kind in list(fuss[0]):
        if kind.tag == G or (kind.tag == TEXT and kind.find(TITLE) is not None):
            fuss[0].remove(kind)

    colors = LANGUAGE_COLORS.get(os.path.basename(pfad), {})
    if not all(recolor_language(wurzel, lang, col) for lang, col in colors.items()):
        print(f"{pfad}: Umfaerben fehlgeschlagen")
        return False

    baum.write(pfad, encoding="unicode")
    print(f"{pfad}: aufgeraeumt")
    return True


if __name__ == "__main__":
    ergebnisse = [aufraeumen(p) for p in sys.argv[1:]]
    if not ergebnisse or not all(ergebnisse):
        sys.exit(1)
