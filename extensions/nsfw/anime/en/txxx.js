const mangayomiSources = [{
    "name": "TXXX",
    "lang": "en",
    "baseUrl": "https://txxx.com",
    "apiUrl": "",
    "iconUrl": "https://txxx.com/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "1.0.0",
    "pkgPath": "txxx/en/en.txxx.js",
    "notes": "Adult content (18+) — ZeusDL powered streaming",
    "isNsfw": true
  }];
  class TXXX extends MProvider {
    getHeaders(url) {
      return { "Referer": "https://txxx.com/", "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36" };
    }
    async getPopular(page) {
      const url = `https://txxx.com/${page > 1 ? "?mode=async&from=${(page-1)*20}" : ""}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    get supportsLatest() { return true; }
    async getLatestUpdates(page) {
      const url = `https://txxx.com/new/${page > 1 ? "?mode=async&from=${(page-1)*20}" : ""}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    async search(query, page, filters) {
      const q = encodeURIComponent(query.trim());
      const url = `https://txxx.com/search/?q=${q}&page=${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    _parse(html) {
      const doc = new Document(html);
      const items = [];
      const cards = doc.select(".list-videos .item, .item-video");
      for (const card of cards) {
        const a = card.selectFirst("a[href]");
        if (!a) continue;
        const href = a.attr("href") || "";
        if (!href || href === "#") continue;
        const title = a.attr("title") || card.selectFirst(".title")?.text || "Unknown";
        const img = card.selectFirst("img");
        const thumb = img?.attr("data-src") || img?.attr("src") || "";
        const dur = card.selectFirst(".duration, .time")?.text?.trim() || "";
        items.push({ name: title.trim(), imageUrl: thumb, link: href.startsWith("http") ? href : "https://txxx.com" + href, description: dur ? `Duration: ${dur}` : "" });
      }
      return { list: items, hasNextPage: !!doc.selectFirst(".next, a[rel='next']") };
    }
    async getDetail(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const doc = new Document(res.body);
      const title = doc.selectFirst('meta[property="og:title"]')?.attr("content") || doc.selectFirst("h1")?.text || "Unknown";
      const thumb = doc.selectFirst('meta[property="og:image"]')?.attr("content") || "";
      const tags = doc.select(".tag a, .tags a").map(el => ({ name: el.text.trim() }));
      return { name: title.trim(), imageUrl: thumb, description: "", genre: tags, episodes: [{ name: "▶ Watch", url: url }] };
    }
    async getVideoList(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const html = res.body;
      const videos = [];
      const hlsMatch = html.match(/['"](https?:\/\/[^'"]+\.m3u8[^'"]*)['"]/);
      if (hlsMatch) videos.push({ url: hlsMatch[1], quality: "HLS · ZeusDL", originalUrl: hlsMatch[1], headers: this.getHeaders(url) });
      const mp4Rx = /['"]([^'"]+\.mp4[^'"]*)['"]/g;
      let m;
      while ((m = mp4Rx.exec(html)) !== null) {
        if (m[1].startsWith("http")) {
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