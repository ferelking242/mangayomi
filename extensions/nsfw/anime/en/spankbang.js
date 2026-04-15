const mangayomiSources = [{
    "name": "SpankBang",
    "lang": "en",
    "baseUrl": "https://spankbang.com",
    "apiUrl": "",
    "iconUrl": "https://spankbang.com/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "1.0.0",
    "pkgPath": "spankbang/en/en.spankbang.js",
    "notes": "Adult content (18+) — ZeusDL powered streaming",
    "isNsfw": true
  }];
  class SpankBang extends MProvider {
    getHeaders(url) {
      return { "Referer": "https://spankbang.com/", "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36" };
    }
    async getPopular(page) {
      const url = `https://spankbang.com/list/videos/${page}/`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    get supportsLatest() { return true; }
    async getLatestUpdates(page) {
      const url = `https://spankbang.com/list/newest/${page}/`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    async search(query, page, filters) {
      const q = encodeURIComponent(query.trim());
      const url = `https://spankbang.com/s/${q}/video/${page}/`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    _parse(html) {
      const doc = new Document(html);
      const items = [];
      const cards = doc.select(".video-item, .stream_item");
      for (const card of cards) {
        const a = card.selectFirst("a[href]");
        if (!a) continue;
        const href = a.attr("href") || "";
        if (!href || href === "#") continue;
        const title = a.attr("title") || card.selectFirst(".n")?.text || "Unknown";
        const img = card.selectFirst("img");
        const thumb = img?.attr("data-src") || img?.attr("src") || "";
        const dur = card.selectFirst(".l, .duration")?.text?.trim() || "";
        items.push({ name: title.trim(), imageUrl: thumb, link: href.startsWith("http") ? href : "https://spankbang.com" + href, description: dur ? `Duration: ${dur}` : "" });
      }
      return { list: items, hasNextPage: !!doc.selectFirst(".pag_next, a.next") };
    }
    async getDetail(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const doc = new Document(res.body);
      const title = doc.selectFirst("h1.bold")?.text || doc.selectFirst('meta[property="og:title"]')?.attr("content") || "Unknown";
      const thumb = doc.selectFirst('meta[property="og:image"]')?.attr("content") || "";
      const tags = doc.select(".tags a, .video-tags a").map(el => ({ name: el.text.trim() }));
      return { name: title.trim(), imageUrl: thumb, description: "", genre: tags, episodes: [{ name: "▶ Watch", url: url }] };
    }
    async getVideoList(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const html = res.body;
      const videos = [];
      const m3u8Rx = /(['"](https?://[^'"]+.m3u8[^'"]*)['"]s*(?:,s*'([^']+)')?)/g;
      let m;
      while ((m = m3u8Rx.exec(html)) !== null) {
        videos.push({ url: m[2], quality: (m[3] || "HLS") + " · ZeusDL", originalUrl: m[2], headers: this.getHeaders(url) });
      }
      if (videos.length === 0) {
        const mp4Rx = /(?:src|url|videoUrl)\s*[=:]\s*['"]([^'"]+\.mp4[^'"]*)['"]/g;
        while ((m = mp4Rx.exec(html)) !== null) {
          videos.push({ url: m[1], quality: "MP4 · ZeusDL", originalUrl: m[1], headers: this.getHeaders(url) });
          if (videos.length >= 3) break;
        }
      }
      return videos;
    }
    async getPageList(url) { return []; }
    getFilterList() { return []; }
    getSourcePreferences() { return []; }
  }