"""Refaz o ZIM da WalkScape Wiki (gerado pelo mwoffliner) com o layout para celular:
``python3 patch_zim.py entrada.zim saida.zim``.

Copia tudo do ZIM de entrada (itens, redirecionamentos, metadados, a ilustração e a página principal) e só muda:
- as páginas HTML: ``transform.transform`` (o CSS novo e as tabelas largas num contêiner que rola);
- um item a mais, ``_res_/mobile.css``.
A busca (índice de títulos e de texto completo) é refeita pelo libzim.
"""
import os
import sys
import time

from libzim.reader import Archive
from libzim.writer import Creator, Hint, Item, StringProvider

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import transform  # noqa: E402

COMPRESSIBLE = ("text/", "application/javascript", "application/json", "image/svg+xml", "application/xml")
SKIP_METADATA = ("Counter",)          # o libzim escreve o dele


class Entry(Item):
    def __init__(self, path, title, mimetype, data, front):
        super().__init__()
        self.path, self.title, self.mimetype, self.data, self.front = path, title, mimetype, data, front

    def get_path(self):
        return self.path

    def get_title(self):
        return self.title

    def get_mimetype(self):
        return self.mimetype

    def get_contentprovider(self):
        return StringProvider(self.data)

    def get_hints(self):
        return {Hint.FRONT_ARTICLE: self.front, Hint.COMPRESS: self.mimetype.startswith(COMPRESSIBLE)}


def main(src, dst, css):
    t0 = time.time()
    zim = Archive(src)
    meta = {k: bytes(zim.get_metadata(k)) for k in zim.metadata_keys if k not in SKIP_METADATA}
    meta = {k: v for k, v in meta.items() if v}          # um metadado vazio (Flavour) seria um erro do zimcheck
    lang = meta.get("Language", b"eng").decode().split(",")[0] or "eng"
    main_entry = zim.main_entry
    main_path = main_entry.get_item().path if main_entry.is_redirect else main_entry.path
    pages = redirects = others = 0
    if os.path.exists(dst):
        os.remove(dst)
    with Creator(dst).config_indexing(True, lang) as out:
        out.set_mainpath(main_path)
        for key, value in meta.items():
            if key.startswith("Illustration_"):
                size = int(key.split("_")[1].split("x")[0])
                out.add_illustration(size, value)
            else:
                out.add_metadata(key, value, "text/plain;charset=UTF-8")
        out.add_item(Entry(transform.CSS_PATH, "", "text/css", open(css, "rb").read(), False))
        # só o conteúdo: os ids de 0 a entry_count - 1; depois vêm os metadados e os índices (sem o namespace no
        # caminho), que o Creator escreve de novo
        for i in range(zim.entry_count):
            entry = zim._get_entry_by_id(i)
            if entry.path == transform.CSS_PATH:
                continue
            if entry.is_redirect:
                target = entry.get_redirect_entry().path
                out.add_redirection(entry.path, entry.title, target, {Hint.FRONT_ARTICLE: True})
                redirects += 1
                continue
            item = entry.get_item()
            data = bytes(item.content)
            mime = item.mimetype
            front = False
            if mime.startswith("text/html"):
                html = data.decode("utf-8")
                front = transform.is_page(html) and not entry.path.startswith("_")
                data = transform.transform(html).encode("utf-8")
                pages += 1
            else:
                others += 1
            out.add_item(Entry(entry.path, entry.title, mime, data, front))
    print(f"{pages} páginas, {others} outros itens, {redirects} redirecionamentos em {time.time() - t0:.0f} s; "
          f"{os.path.getsize(src) / 1e6:.1f} MB -> {os.path.getsize(dst) / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else os.path.join(here, "mobile.css"))
