const mangayomiSources = [{
    "name": "Beeg",
    "lang": "en",
    "baseUrl": "https://beeg.com",
    "apiUrl": "",
    "iconUrl": "https://beeg.com/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "1.0.0",
    "pkgPath": "beeg/en/en.beeg.js",
    "notes": "Adult content (18+) — ZeusDL powered streaming",
    "isNsfw": true
  }];
  class Beeg extends MProvider {
    getHeaders(url) {
      return { "Referer": "https://beeg.com/", "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36" };
    }
    async getPopular(page) {
      const url = `https://beeg.com/${page > 1 ? "?page=" + page : ""}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    get supportsLatest() { return true; }
    async getLatestUpdates(page) {
      const url = `https://beeg.com/new/?page=${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    async search(query, page, filters) {
      const q = encodeURIComponent(query.trim());
      const url = `https://beeg.com/?query=${q}&page=${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    _parse(html) {
      const doc = new Document(html);
      const items = [];
      const cards = doc.select(".videoThumb, .video-thumb, article[data-video-id]");
      for (const card of cards) {
        const a = card.selectFirst("a[href]");
        if (!a) continue;
        const href = a.attr("href") || "";
        if (!href) continue;
        const title = a.attr("title") || card.selectFirst(".title, .video-title")?.text || "Unknown";
        const img = card.selectFirst("img");
        const thumb = img?.attr("data-src") || img?.attr("src") || "";
        const dur = card.selectFirst(".duration, .time")?.text?.trim() || "";
        items.push({ name: title.trim(), imageUrl: thumb, link: href.startsWith("http") ? href : "https://beeg.com" + href, description: dur ? `Duration: ${dur}` : "" });
      }
      return { list: items, hasNextPage: !!doc.selectFirst(".next, a[rel='next']") };
    }
    async getDetail(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const doc = new Document(res.body);
      const title = doc.selectFirst('meta[property="og:title"]')?.attr("content") || "Unknown";
      const thumb = doc.selectFirst('meta[property="og:image"]')?.attr("content") || "";
      const tags = doc.select(".tags a, .tag").map(el => ({ name: el.text.trim() }));
      return { name: title, imageUrl: thumb, description: "", genre: tags, episodes: [{ name: "▶ Watch", url: url }] };
    }
    async getVideoList(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const html = res.body;
      const videos = [];
      const qualityRx = /"(\d{3,4}p|hd|sd)"\s*:\s*"([^"]+\.mp4[^"]*)"/gi;
      let m;
      while ((m = qualityRx.exec(html)) !== null) {
        videos.push({ url: m[2].replace(/\\/g, ""), quality: `${m[1].toUpperCase()} · ZeusDL`, originalUrl: m[2].replace(/\\/g, ""), headers: this.getHeaders(url) });
      }
      if (videos.length === 0) {
        const hlsMatch = html.match(/['"](https?:\/\/[^'"]+\.m3u8[^'"]*)['"]/);
        if (hlsMatch) videos.push({ url: hlsMatch[1], quality: "HLS · ZeusDL", originalUrl: hlsMatch[1], headers: this.getHeaders(url) });
      }
      return videos;
    }
    async getPageList(url) { return []; }
    getFilterList() { return []; }
    getSourcePreferences() { return []; }
  }