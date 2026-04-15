const mangayomiSources = [{
    "name": "XVideos",
    "lang": "en",
    "baseUrl": "https://www.xvideos.com",
    "apiUrl": "",
    "iconUrl": "https://www.xvideos.com/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "1.0.0",
    "pkgPath": "xvideos/en/en.xvideos.js",
    "notes": "Adult content (18+) — ZeusDL powered streaming",
    "isNsfw": true
  }];
  class XVideos extends MProvider {
    getHeaders(url) {
      return { "Referer": "https://www.xvideos.com/", "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36" };
    }
    async getPopular(page) {
      const url = `https://www.xvideos.com/?p=${page - 1}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    get supportsLatest() { return true; }
    async getLatestUpdates(page) {
      const url = `https://www.xvideos.com/new/${page - 1}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    async search(query, page, filters) {
      const q = encodeURIComponent(query.trim());
      const url = `https://www.xvideos.com/?k=${q}&p=${page - 1}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    _parse(html) {
      const doc = new Document(html);
      const items = [];
      const cards = doc.select(".thumb-block, .mozaique .thumb-block, #main .thumb-block");
      for (const card of cards) {
        const a = card.selectFirst("a");
        if (!a) continue;
        const href = a.attr("href") || "";
        if (!href || !href.includes("/video")) continue;
        const title = a.attr("title") || card.selectFirst(".title")?.text || "Unknown";
        const img = card.selectFirst("img");
        const thumb = img?.attr("data-src") || img?.attr("src") || "";
        const dur = card.selectFirst(".duration")?.text?.trim() || "";
        items.push({ name: title.trim(), imageUrl: thumb, link: href.startsWith("http") ? href : "https://www.xvideos.com" + href, description: dur ? `Duration: ${dur}` : "" });
      }
      return { list: items, hasNextPage: !!doc.selectFirst(".pagination .next-page, a[rel='next']") };
    }
    async getDetail(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const doc = new Document(res.body);
      const title = doc.selectFirst('meta[property="og:title"]')?.attr("content") || "Unknown";
      const thumb = doc.selectFirst('meta[property="og:image"]')?.attr("content") || "";
      const tags = doc.select(".video-tags-list a, .tags a").map(el => ({ name: el.text.trim() }));
      return { name: title, imageUrl: thumb, description: "", genre: tags, episodes: [{ name: "▶ Watch", url: url }] };
    }
    async getVideoList(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const html = res.body;
      const videos = [];
      const hlsMatch = html.match(/setVideoHLS\(['"]([^'"]+)['"]\)/);
      if (hlsMatch) videos.push({ url: hlsMatch[1], quality: "HLS · ZeusDL", originalUrl: hlsMatch[1], headers: this.getHeaders(url) });
      const hiMatch = html.match(/setVideoUrlHigh\(['"]([^'"]+)['"]\)/);
      if (hiMatch) videos.push({ url: hiMatch[1], quality: "HD · ZeusDL", originalUrl: hiMatch[1], headers: this.getHeaders(url) });
      const loMatch = html.match(/setVideoUrlLow\(['"]([^'"]+)['"]\)/);
      if (loMatch) videos.push({ url: loMatch[1], quality: "SD · ZeusDL", originalUrl: loMatch[1], headers: this.getHeaders(url) });
      return videos;
    }
    async getPageList(url) { return []; }
    getFilterList() { return []; }
    getSourcePreferences() { return []; }
  }