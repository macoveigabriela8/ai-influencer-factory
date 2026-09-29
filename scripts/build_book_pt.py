#!/usr/bin/env python3
"""Build O Silêncio Entre Pensamentos (PT-BR edition) -> book_pt.html -> PDF.

Reads the translated day files produced 2026-08-08:
  output/book/pt_days_0_9.json   ({"weeks":[...], "days":[...]})
  output/book/pt_days_10_19.json ({"days":[...]})
  output/book/pt_days_20_29.json ({"days":[...]})
Same 6x9in design and ink assets as the EN build (build_book.py).

    python3 scripts/build_book_pt.py     # writes output/book/book_pt.html + PDF
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "output", "book")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from build_book import HEAD, W  # same CSS + week image mapping  # noqa: E402

TITLE = "O Silêncio Entre Pensamentos"
AUTHOR = "MESTRE KAION"


def load_days():
    p1 = json.load(open(os.path.join(BOOK, "pt_days_0_9.json")))
    p2 = json.load(open(os.path.join(BOOK, "pt_days_10_19.json")))
    p3 = json.load(open(os.path.join(BOOK, "pt_days_20_29.json")))
    days = p1["days"] + p2["days"] + p3["days"]
    assert len(days) == 30, f"expected 30 days, got {len(days)}"
    weeks = p1["weeks"]
    return weeks, days


def day_page(i, d, days, weeks, folio):
    parts = []
    if i == 0 or days[i - 1]["week"] != d["week"]:
        wk = weeks[d["week"]]
        img = W[d["week"]][2]
        parts.append(f'<div class="page weekpage"><div class="wk">{wk["n"]}</div>'
                     f'<h1>{wk["t"]}</h1><img src="{img}"></div>')
    ps = "".join(f'<p class="{"first" if j == 0 else ""}">{p}</p>'
                 for j, p in enumerate(d["paras"]))
    steps = d.get("practice_steps") or d.get("steps")
    steps_html = "".join(f"<li>{s}</li>" for s in steps)
    parts.append(
        f'<div class="page"><div class="daynum">{i + 1}</div>'
        f'<h3 class="daytitle">{d["title"]}</h3>'
        f'<p class="epigraph">{d["epigraph"]}</p>{ps}'
        f'<div class="practice"><div class="label">{d["practice_label"]}</div>'
        f'<ol>{steps_html}</ol></div>'
        f'<div class="journal"><div class="label">Uma linha esta noite</div>'
        f'<p>{d["journal"]}</p>'
        f'<div class="rule-line"></div></div><div class="folio">{folio}</div></div>')
    return "".join(parts)


def build():
    weeks, days = load_days()
    html = [HEAD]
    html.append('<div class="page cover"><img src="cover_portrait_pt.png"><div class="block">'
                '<div class="sub">Um retorno de trinta dias à quietude</div>'
                '<h1>O Silêncio Entre<br>Pensamentos</h1>'
                f'<div class="rule"></div><div class="author">{AUTHOR}</div></div></div>')
    html.append(f'<div class="page titlepage"><h1>{TITLE}</h1>'
                '<div class="sub">Trinta dias de pequenas práticas<br>'
                'para uma mente que não para de falar</div>'
                '<img src="ink_enso.png"><div class="author">Mestre Kaion</div>'
                '<div class="folio">Este livro acompanha uma prática. '
                'Não substitui nenhum médico e nenhum remédio.</div></div>')
    html.append('<div class="page"><h2 class="week">Antes de Começar</h2>'
                '<img class="motif" src="ink_teacup.png">'
                '<p class="first">Você não encontrou este livro porque a sua vida está quebrada. '
                'Encontrou porque a sua mente é barulhenta, e você desconfia de que não precisa ser assim.</p>'
                '<p>Passei quarenta anos aprendendo uma coisa em silêncio: a paz não se encontra mudando o lugar onde você vive. '
                'Encontra-se mudando o modo como você encontra a própria mente. Essa frase é fácil de ler e lenta de aprender. '
                'Os trinta dias deste livro são o modo como eu a ensino.</p>'
                '<p>Cada dia pede dez minutos, às vezes menos. Um ensinamento curto. Uma prática pequena. Uma linha para escrever. '
                'É só isso. Não leia adiantado. Um dia lido em um minuto não faz nada; um dia vivido muda o dia seguinte.</p>'
                '<p>Algumas práticas vão parecer simples demais para importar. Faça mesmo assim. '
                'Um copo de água ao lado da cama é uma coisa pequena. Um único fósforo em um quarto escuro também é.</p>'
                '<p>Se você perder um dia, não falhou. Recomece de onde parou. '
                'O caminho não guarda rancor de quem anda devagar. Ele só pede que você continue andando.</p>'
                '<div class="folio">3</div></div>')
    folio = 5
    for i, d in enumerate(days):
        html.append(day_page(i, d, days, weeks, folio))
        folio += 1
    html.append('<div class="page titlepage"><h1>Vá com calma.</h1>'
                '<div class="sub">Se este livro lhe deu uma manhã mais quieta,<br>'
                'entregue-o a alguém cuja mente é barulhenta.</div>'
                '<img src="ink_enso.png"><div class="folio">© Mestre Kaion · O Silêncio Entre Pensamentos</div></div>')
    html.append("</body></html>")
    out = os.path.join(BOOK, "book_pt.html")
    open(out, "w").write("".join(html))
    words = sum(len(" ".join(d["paras"]).split()) for d in days)
    print(f"book_pt.html written · {len(days)} days · ~{words} words")
    # PDF via headless Chrome (same as EN)
    pdf = os.path.join(BOOK, "O_Silencio_Entre_Pensamentos.pdf")
    subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", out], check=True, timeout=300)
    print("pdf:", pdf)


if __name__ == "__main__":
    build()
