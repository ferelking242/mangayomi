# Watchtower

## Overview

Flutter media app forked from Mangayomi, rebranded as **Watchtower**. Supports anime watching, manga reading, and **light novel reading**. Includes a ZeusDL-powered adult content extension system.

## Website (artifacts/aniyomi-website)

VitePress documentation website for Watchtower. Deployed at `/aniyomi-website/`.

### Website Key Files
- `src/index.md` — home page with features (Anime & Manga, Light Novels, Tracking, etc.)
- `src/.vitepress/config.ts` — main VitePress config, base URL `/aniyomi-website/`
- `src/.vitepress/config/navigation/navbar.ts` — top navigation (Get, Docs dropdown, News, Community dropdown)
- `src/.vitepress/config/navigation/sidebar.ts` — sidebar navigation including LN reader guide
- `src/.vitepress/theme/data/release.data.ts` — GitHub release loader (ferelking242/watchtower), has fallback for missing releases
- `src/.vitepress/theme/data/changelogs.data.ts` — GitHub changelogs loader (ferelking242/watchtower)
- `src/docs/guides/light-novel-reader.md` — complete LN reader guide (added)
- `src/docs/faq/general.md` — general FAQ (LN support confirmed, content types listed)

## Stack

- **App**: Flutter (Dart) — `mangayomi/`
- **Extensions**: JavaScript (ZeusDL / MProvider format)
- **Extensions repo**: `ferelking242/watchtower-extensions` on GitHub
- **Default repos seeded on first launch**: Keiyoushi (manga), Aniyomi (anime), Watchtower Extensions (NSFW anime), LNReader (novel)

## Key Files

- `mangayomi/lib/main.dart` — app entry point, title "Watchtower"
- `mangayomi/android/app/src/main/AndroidManifest.xml` — app label
- `mangayomi/lib/modules/main_view/main_screen.dart` — dock order
- `mangayomi/lib/modules/more/settings/reader/providers/reader_state_provider.dart` — dock items enum
- `mangayomi/lib/modules/more/more_screen.dart` — branding
- `mangayomi/lib/modules/more/about/about_screen.dart` — about screen branding
- `mangayomi/lib/providers/storage_provider.dart` — default repos seeded on first run
- `extensions/index.min.json` — local mirror of GitHub extension index

## Dock Order

Watch → Manga → Novel → History → Updates → Browse → More

## Extensions on GitHub

12 adult video extensions at `ferelking242/watchtower-extensions`:
- XNXX, XVideos, PornHub, SpankBang, xHamster, Eporner, RedTube, YouPorn, Tube8, TXXX, Beeg, TNAFlix
- All use ZeusDL `MProvider` class, `sourceCodeLanguage: 1` (JavaScript), `itemType: 1` (anime/video)
- Index URL: `https://raw.githubusercontent.com/ferelking242/watchtower-extensions/main/index.min.json`
