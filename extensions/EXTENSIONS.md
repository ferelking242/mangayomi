# Watchtower Extensions

## Structure

```
extensions/
├── anime/               # Anime streaming extensions (JS)
│   ├── en/             # English
│   ├── fr/             # French
│   ├── de/             # German
│   ├── es/             # Spanish
│   └── ...             # Other languages
├── manga/               # Manga reading extensions (JS)
│   ├── en/
│   ├── fr/
│   ├── ja/, zh/, ko/   # Asian languages
│   └── ...             # 50+ language folders
├── novel/               # Novel/light novel extensions (JS)
│   ├── en/
│   └── ar/
├── nsfw/                # Adult content extensions (18+)
│   ├── anime/           # Adult video sites (ZeusDL)
│   │   └── en/         # XNXX, XVideos, PornHub, SpankBang, xHamster...
│   └── manga/           # Adult manga/hentai sites
│       └── en/, ja/, ...
└── index/               # Raw source index files (per-repo)
    ├── kodjo_manga.json
    ├── m2k3a_anime.json
    ├── swakshan_anime.json
    └── ...

## Master Index Files (root of extensions/)
- anime_index.json    — 73 anime extensions
- manga_index.json    — 368 manga extensions
- novel_index.json    — 11 novel extensions
- nsfw_index.json     — 287 adult extensions
- index.min.json      — Watchtower custom extensions (GitHub hosted)
```

## Sources (from wotaku.wiki)

| Source | Anime | Manga | Novel | NSFW |
|--------|-------|-------|-------|------|
| Kodjo | ❌ | ✅ 363 | ✅ 5 | ❌ |
| m2k3a | ✅ 62 | ✅ 327 | ✅ 8 | ❌ |
| Swakshan | ✅ 12 | ✅ 5 | ✅ 3 | ❌ |
| Schnitzel5 | ✅ 62 | ✅ 327 | ✅ 8 | ❌ |
| Gato404 | ✅ 2 | ✅ 272 | ❌ | ✅ |
| **Watchtower** | — | — | — | ✅ 12 |

## NSFW Anime Extensions (Watchtower, in nsfw/anime/en/)
XNXX · XVideos · PornHub · SpankBang · xHamster · Eporner · RedTube · YouPorn · Tube8 · TXXX · Beeg · TNAFlix

## Extension Format
- **Dart extensions** (no sourceCodeUrl / .dart path) → metadata only in index files
- **JS extensions** (.js sourceCodeUrl) → actual source code saved locally
- **ZeusDL / MProvider** → format for custom JS extensions (Watchtower NSFW)
