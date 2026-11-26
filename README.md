# WalkScape Wiki offline (Kiwix)

Daily ZIM dumps of the [WalkScape Wiki](https://wiki.walkscape.app), for reading offline in
[Kiwix](https://kiwix.org) (Android, iOS, desktop). Download the latest `.zim` from
[Releases](../../releases) and open it in Kiwix.

## How it is built

Everything runs on GitHub Actions, once a day at 03:00 UTC: [`.github/workflows/zim.yml`](.github/workflows/zim.yml)
downloads the wiki with [mwoffliner](https://github.com/openzim/mwoffliner) 1.17.5, applies the mobile layout below and
publishes the release `vYYYY-MM-DD`. It can also be run by hand from the Actions tab. If a release is published by other
means, [`.github/workflows/mobile.yml`](.github/workflows/mobile.yml) applies the layout to it.

## Mobile layout

[`mobile/patch_zim.py`](mobile/patch_zim.py) rewrites the ZIM made by mwoffliner:

- a white page with margins and readable text, instead of dark text on the grey Timeless background;
- the language links as one row of buttons that scrolls sideways, with the "Other Languages" menu hidden (it needs the
  wiki's JavaScript);
- wide tables scroll sideways inside the page instead of being cut off, with a shadow on the side that has more columns;
- item boxes, cards and floating images aligned to the screen width on phones.

The page content, search and images are unchanged.

**Links between pages.** The wiki routes almost every link through `Special:MyLanguage/<page>`, which mwoffliner
cannot keep, so it used to drop those links and leave plain text (the main page cards, item and location references).
[`scripts/mwoffliner-mylanguage.mjs`](scripts/mwoffliner-mylanguage.mjs) patches mwoffliner so they link to the page
in the same language when it exists (`Jarvonia/de` from a German page), or to the English page otherwise. To apply it to an existing file by hand:

```sh
pip install "libzim>=3.4,<4"
python mobile/patch_zim.py walkscape_offline.zim walkscape_offline_mobile.zim
```
