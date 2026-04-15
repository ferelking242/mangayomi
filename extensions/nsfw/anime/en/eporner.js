const mangayomiSources = [{
    "name": "Eporner",
    "lang": "en",
    "baseUrl": "https://www.eporner.com",
    "apiUrl": "",
    "iconUrl": "https://www.eporner.com/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "1.0.0",
    "pkgPath": "eporner/en/en.eporner.js",
    "notes": "Adult content (18+) — ZeusDL powered streaming",
    "isNsfw": true
  }];
  class Eporner extends MProvider {
    getHeaders(url) {
      return { "Referer": "https://www.eporner.com/", "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36" };
    }
    async getPopular(page) {
      const url = `https://www.eporner.com/${page > 1 ? page + "/" : ""}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    get supportsLatest() { return true; }
    async getLatestUpdates(page) {
      const url = `https://www.eporner.com/new/${page > 1 ? page + "/" : ""}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    async search(query, page, filters) {
      const q = encodeURIComponent(query.trim());
      const url = `https://www.eporner.com/search/${q}/${page > 1 ? page + "/" : ""}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    _parse(html) {
      const doc = new Document(html);
      const items = [];
      const cards = doc.select("#categries article, .mb, .mbs");
      for (const card of cards) {
        const a = card.selectFirst("a[href*='/video']");
        if (!a) continue;
        const href = a.attr("href") || "";
        if (!href) continue;
        const title = a.attr("title") || card.selectFirst("strong")?.text || "Unknown";
        const img = card.selectFirst("img");
        const thumb = img?.attr("data-src") || img?.attr("src") || "";
        const dur = card.selectFirst(".duration, .time")?.text?.trim() || "";
        items.push({ name: title.trim(), imageUrl: thumb, link: href.startsWith("http") ? href : "https://www.eporner.com" + href, description: dur ? `Duration: ${dur}` : "" });
      }
      return { list: items, hasNextPage: !!doc.selectFirst(".next, a[rel='next']") };
    }
    async getDetail(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const doc = new Document(res.body);
      const title = doc.selectFirst("h1")?.text || doc.selectFirst('meta[property="og:title"]')?.attr("content") || "Unknown";
      const thumb = doc.selectFirst('meta[property="og:image"]')?.attr("content") || "";
      const tags = doc.select(".vtagsc a, .tags a").map(el => ({ name: el.text.trim() }));
      return { name: title.trim(), imageUrl: thumb, description: "", genre: tags, episodes: [{ name: "▶ Watch", url: url }] };
    }
    async getVideoList(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const html = res.body;
      const videos = [];
      const hlsMatch = html.match(/['"]([^'"]+\.m3u8[^'"]*)['"]/);
      if (hlsMatch) videos.push({ url: hlsMatch[1], quality: "HLS · ZeusDL", originalUrl: hlsMatch[1], headers: this.getHeaders(url) });
      const mp4Rx = /['"]([^'"]+\.mp4[^'"]*)['"]/g;
      let m;
      while ((m = mp4Rx.exec(html)) !== null) {
        if (!m[1].includes("ad") && !m[1].includes("banner")) {
          videos.push({ url: m[1], quality: "MP4 · ZeusDL", originalUrl: m[1], headers: this.getHeaders(url) });
          if (videos.length >= 4) break;
        }
      }
      return videos;
    }
    async getPageList(url) { return []; }
    getFilterList() { return []; }
    getSourcePreferences() { return []; }
  }