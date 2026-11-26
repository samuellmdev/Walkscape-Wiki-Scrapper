// Patch do mwoffliner 1.17.5 (lib/util/rewriteUrls.js) para a WalkScape Wiki.
//
// Na wiki, quase todo link passa por Special:MyLanguage/<página> (extensão Translate: leva à página no idioma de quem
// lê). O mwoffliner não tem páginas especiais no ZIM e remove esses links, deixando só o texto: Kallaheim tinha 164
// links na wiki e 62 no ZIM. Com o patch, o link vai para <página>/<idioma> numa subpágina de idioma (Kallaheim/de ->
// Jarvonia/de) quando ela existe no ZIM, e para <página> nos outros casos.
//
// Uso: node mwoffliner-mylanguage.mjs /tmp/mwoffliner/lib/util/rewriteUrls.js. Falha (sem mexer no arquivo) se o código
// do mwoffliner não for o esperado: troque a versão da imagem com cuidado.
import fs from 'node:fs'

const file = process.argv[2]
let src = fs.readFileSync(file, 'utf8')
const MARK = '/* walkscape: Special:MyLanguage */'
if (src.includes(MARK)) {
  console.log('patch MyLanguage: já aplicado')
  process.exit(0)
}

function swap(oldText, newText) {
  const n = src.split(oldText).length - 1
  if (n !== 1) {
    console.error(`patch MyLanguage: trecho esperado ${n} vezes (deveria ser 1):\n${oldText}`)
    process.exit(1)
  }
  src = src.replace(oldText, newText)
}

// 1. O título do link: sem o Special:MyLanguage/, e na subpágina de idioma a página do mesmo idioma
swap(
  `    const title = MediaWiki.extractPageTitleFromHref(href);
    if (title) {`,
  `    let title = MediaWiki.extractPageTitleFromHref(href);
    ${MARK}
    if (title && /^Special:MyLanguage\\//i.test(title)) {
        const base = title.replace(/^Special:MyLanguage\\//i, '');
        const lang = /\\/([a-z]{2,3}(?:-[a-z]{2,4})?)$/.exec(articleId);
        title = lang ? \`\${base}/\${lang[1]}\` : base;
        if (lang) {
            linkNode.setAttribute('data-ws-fallback', base);
        }
    }
    if (title) {`,
)

// 2. Antes de remover os links para páginas fora do ZIM: <página>/<idioma> que não existe volta para <página>
swap(
  `    const [, unmirroredTitles] = await checkIfArticlesMirrored(Object.keys(wikilinkMappings), RedisStore.articleDetailXId);`,
  `    ${MARK}
    {
        const [, missing] = await checkIfArticlesMirrored(Object.keys(wikilinkMappings), RedisStore.articleDetailXId);
        const redirected = missing.length ? await RedisStore.redirectsXId.existsMany(missing) : {};
        for (const t of missing) {
            if (redirected[t]) {
                continue;
            }
            const nodes = wikilinkMappings[t];
            const back = nodes.filter((n) => n.getAttribute('data-ws-fallback'));
            if (!back.length) {
                continue;
            }
            const keep = nodes.filter((n) => !n.getAttribute('data-ws-fallback'));
            if (keep.length) {
                wikilinkMappings[t] = keep;
            } else {
                delete wikilinkMappings[t];
            }
            for (const n of back) {
                const base = n.getAttribute('data-ws-fallback');
                const href = n.getAttribute('href') || '';
                const hash = href.lastIndexOf('#') === -1 ? '' : href.substr(href.lastIndexOf('#'));
                n.setAttribute('href', encodeArticleIdForZimHtmlUrl(base) + hash);
                (wikilinkMappings[base] = wikilinkMappings[base] || []).push(n);
            }
        }
        for (const nodes of Object.values(wikilinkMappings)) {
            for (const n of nodes) {
                n.removeAttribute('data-ws-fallback');
            }
        }
    }
    const [, unmirroredTitles] = await checkIfArticlesMirrored(Object.keys(wikilinkMappings), RedisStore.articleDetailXId);`,
)

fs.writeFileSync(file, src)
console.log('patch MyLanguage: aplicado')
