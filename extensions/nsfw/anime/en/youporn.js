const mangayomiSources = [{
    "name": "YouPorn",
    "lang": "en",
    "baseUrl": "https://www.youporn.com",
    "apiUrl": "",
    "iconUrl": "https://www.youporn.com/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "1.0.0",
    "pkgPath": "youporn/en/en.youporn.js",
    "notes": "Adult content (18+) — ZeusDL powered streaming",
    "isNsfw": true
  }];
  class YouPorn extends MProvider {
    getHeaders(url) {
      return { "Referer": "https://www.youporn.com/", "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36", "Cookie": "age_verified=1" };
    }
    async getPopular(page) {
      const url = `https://www.youporn.com/porn-videos/?o=mv&page=${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    get supportsLatest() { return true; }
    async getLatestUpdates(page) {
      const url = `https://www.youporn.com/porn-videos/?o=n&page=${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    async search(query, page, filters) {
      const q = encodeURIComponent(query.trim());
      const url = `https://www.youporn.com/search/video/?query=${q}&page=${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    _parse(html) {
      const doc = new Document(html);
      const items = [];
      const cards = doc.select(".video-box, .pcVideoListItem, article");
      for (const card of cards) {
        const a = card.selectFirst("a[href*='/watch/']") || card.selectFirst("a");
        if (!a) continue;
        const href = a.attr("href") || "";
        if (!href || !href.includes("watch")) continue;
        const title = a.attr("title") || card.selectFirst(".title")?.text || "Unknown";
        const img = card.selectFirst("img");
        const thumb = img?.attr("data-src") || img?.attr("src") || "";
        const dur = card.selectFirst(".duration, .videoDuration")?.text?.trim() || "";
        items.push({ name: title.trim(), imageUrl: thumb, link: href.startsWith("http") ? href : "https://www.youporn.com" + href, description: dur ? `Duration: ${dur}` : "" });
      }
      return { list: items, hasNextPage: !!doc.selectFirst(".next, a[rel='next']") };
    }
    async getDetail(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const doc = new Document(res.body);
      const title = doc.selectFirst('meta[property="og:title"]')?.attr("content") || "Unknown";
      const thumb = doc.selectFirst('meta[property="og:image"]')?.attr("content") || "";
      const tags = doc.select(".video-tags a, .tag").map(el => ({ name: el.text.trim() }));
      return { name: title, imageUrl: thumb, description: "", genre: tags, episodes: [{ name: "▶ Watch", url: url }] };
    }
    async getVideoList(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const html = res.body;
      const videos = [];
      const qualityRx = /"quality"\s*:\s*"(\d+)"[^}]+"videoUrl"\s*:\s*"([^"]+)"/g;
      let m;
      while ((m = qualityRx.exec(html)) !== null) {
        videos.push({ url: m[2].replace(/\\/g, ""), quality: `${m[1]}p · ZeusDL`, originalUrl: m[2].replace(/\\/g, ""), headers: this.getHeaders(url) });
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