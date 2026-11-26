"""A transformação das páginas do ZIM da WalkScape Wiki para o celular (Kiwix):

- o CSS ``mobile.css`` (em ``_res_/``) entra depois do CSS da wiki, com o mesmo prefixo relativo dos outros
  (``./`` numa página da raiz, ``../`` numa subpágina como ``Fishing/de``);
- cada tabela ``wikitable`` (menos a caixa do item, ``wswb-infobox``) fica dentro de um ``div.ws-table-scroll``, que rola
  para o lado no celular em vez de cortar a tabela; tabelas dentro de tabelas ficam como estão.
"""
import re

CSS_PATH = "_res_/mobile.css"
_LINK = re.compile(r'<link rel="stylesheet" type="text/css" href="((?:\./|(?:\.\./)+))_mw_/site\.styles\.css">')
_TABLE = re.compile(r"<table\b[^>]*>|</table\s*>", re.I)
_CLASS = re.compile(r'\bclass="([^"]*)"', re.I)
MARK = 'data-ws-mobile="1"'


def _wrap_tables(html):
    out, pos, depth = [], 0, 0
    wrapped = []            # para cada nível aberto: se foi envolvido
    for m in _TABLE.finditer(html):
        tag = m.group(0)
        if tag[1] != "/":
            cls = _CLASS.search(tag)
            names = cls.group(1).split() if cls else []
            wrap = depth == 0 and "wikitable" in names and "wswb-infobox" not in names
            out.append(html[pos:m.start()])
            if wrap:
                out.append('<div class="ws-table-scroll">')
            out.append(tag)
            wrapped.append(wrap)
            depth += 1
        else:
            out.append(html[pos:m.end()])
            if depth:
                depth -= 1
                if wrapped.pop():
                    out.append("</div>")
            pos = m.end()
            continue
        pos = m.end()
    out.append(html[pos:])
    return "".join(out)


def is_page(html):
    """Uma página da wiki (tem o CSS da wiki), e não um recurso HTML do mwoffliner."""
    return bool(_LINK.search(html))


def transform(html):
    """O HTML de uma página, para o celular. Idempotente (a marca ``data-ws-mobile`` no <html>)."""
    if MARK in html[:600]:
        return html
    m = _LINK.search(html)
    if not m:                # não é uma página da wiki (o rodapé, um recurso): fica como está
        return html
    link = f'<link rel="stylesheet" type="text/css" href="{m.group(1)}{CSS_PATH}">'
    html = html[:m.end()] + link + html[m.end():]
    html = html.replace("<html ", f"<html {MARK} ", 1)
    return _wrap_tables(html)
