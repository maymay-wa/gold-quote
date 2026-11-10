#!/usr/bin/env python3
"""Copy the app's translations into the website, so both speak the same words.

    python3 tools/web_strings.py

Reads ios/GoldQuote/<lang>.lproj/Localizable.strings (keys are the English text) and rewrites the STRINGS table
between "@strings-start" and "@strings-end" in index.html. WEB_ONLY holds the few strings only the website has.
Run it again after changing the app's .strings files.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["he", "ar", "ru", "es", "fr"]

WEB_ONLY = {
    "Choose or drop an STL file": {
        "he": "בחירת קובץ STL או גרירה לכאן",
        "ar": "اختر ملف STL أو أفلته هنا",
        "ru": "Выбрать или перетащить файл STL",
        "es": "Elegir o soltar un archivo STL",
        "fr": "Choisir ou déposer un fichier STL",
    },
    "Download photo": {
        "he": "הורדת התמונה",
        "ar": "تنزيل الصورة",
        "ru": "Скачать фото",
        "es": "Descargar foto",
        "fr": "Télécharger la photo",
    },
    "This browser can't show the 3D viewer.": {
        "he": "הדפדפן הזה לא יכול להציג את התצוגה התלת־ממדית.",
        "ar": "لا يمكن لهذا المتصفح عرض العارض ثلاثي الأبعاد.",
        "ru": "Этот браузер не может показать 3D-просмотр.",
        "es": "Este navegador no puede mostrar el visor 3D.",
        "fr": "Ce navigateur ne peut pas afficher la vue 3D.",
    },
    "3D model. Drag to turn it any way, pinch to zoom, twist to roll, double-tap to reset.": {
        "he": "דגם תלת־ממדי. גרירה מסובבת אותו לכל כיוון, צביטה מגדילה, סיבוב בשתי אצבעות מטה אותו, והקשה כפולה מאפסת.",
        "ar": "نموذج ثلاثي الأبعاد. اسحب لتدويره في أي اتجاه، وقرّب إصبعيك أو باعدهما للتكبير، ولفّهما للإمالة، واضغط مرتين لإعادة الضبط.",
        "ru": "3D-модель. Перетаскивайте, чтобы повернуть в любую сторону, сводите и разводите пальцы для масштаба, вращайте двумя пальцами, коснитесь дважды для сброса.",
        "es": "Modelo 3D. Arrastra para girarlo en cualquier dirección, pellizca para hacer zoom, gira dos dedos para rotarlo y toca dos veces para restablecer.",
        "fr": "Modèle 3D. Faites glisser pour le tourner dans tous les sens, pincez pour zoomer, tournez à deux doigts pour le pivoter, touchez deux fois pour réinitialiser.",
    },
    "3D viewer": {"he": "תצוגה תלת־ממדית", "ar": "العارض ثلاثي الأبعاد", "ru": "3D-просмотр", "es": "Visor 3D", "fr": "Vue 3D"},
    "STL file": {"he": "קובץ STL", "ar": "ملف STL", "ru": "Файл STL", "es": "Archivo STL", "fr": "Fichier STL"},
    "Price": {"he": "מחיר", "ar": "السعر", "ru": "Цена", "es": "Precio", "fr": "Prix"},
}

LINE = re.compile(r'^"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)";\s*$')


def unescape(s):
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), s)


def read_strings(path):
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = LINE.match(line)
        if m:
            out[unescape(m.group(1))] = unescape(m.group(2))
    return out


def main():
    table = {}
    for lang in LANGS:
        t = read_strings(ROOT / "ios" / "GoldQuote" / f"{lang}.lproj" / "Localizable.strings")
        for key, by_lang in WEB_ONLY.items():
            t[key] = by_lang[lang]
        table[lang] = dict(sorted(t.items()))
    body = "const STRINGS = {\n" + "".join(
        f"  {lang}: {json.dumps(table[lang], ensure_ascii=False, separators=(',', ':'))},\n" for lang in LANGS
    ) + "};"
    page = ROOT / "index.html"
    html = page.read_text(encoding="utf-8")
    new, n = re.subn(r"(// @strings-start\n)(?:.*?\n)?(// @strings-end)", lambda m: m.group(1) + body + "\n" + m.group(2), html, flags=re.S)
    if n != 1:
        raise SystemExit("index.html needs one // @strings-start ... // @strings-end region")
    page.write_text(new, encoding="utf-8")
    print(", ".join(f"{lang} {len(table[lang])}" for lang in LANGS) + " strings written to index.html")


if __name__ == "__main__":
    main()
