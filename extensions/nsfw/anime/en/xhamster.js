const mangayomiSources = [{
    "name": "xHamster",
    "lang": "en",
    "baseUrl": "https://xhamster.com",
    "apiUrl": "",
    "iconUrl": "https://xhamster.com/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "1.0.0",
    "pkgPath": "xhamster/en/en.xhamster.js",
    "notes": "Adult content (18+) — ZeusDL powered streaming",
    "isNsfw": true
  }];
  class XHamster extends MProvider {
    getHeaders(url) {
      return { "Referer": "https://xhamster.com/", "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36" };
    }
    async getPopular(page) {
      const url = `https://xhamster.com/videos/best?page=${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    get supportsLatest() { return true; }
    async getLatestUpdates(page) {
      const url = `https://xhamster.com/videos/newest?page=${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    async search(query, page, filters) {
      const q = encodeURIComponent(query.trim());
      const url = `https://xhamster.com/search/${q}?page=${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    _parse(html) {
      const doc = new Document(html);
      const items = [];
      const cards = doc.select(".entities article, .video-thumb-wrap, [data-video-url]");
      for (const card of cards) {
        const a = card.selectFirst("a[href*='/videos/']") || card.selectFirst("a.video-thumb-img");
        if (!a) continue;
        const href = a.attr("href") || "";
        if (!href) continue;
        const title = a.attr("title") || card.selectFirst(".video-thumb-title-label")?.text || "Unknown";
        const img = card.selectFirst("img");
        const thumb = img?.attr("data-src") || img?.attr("src") || "";
        const dur = card.selectFirst(".thumb-image-container__duration, .video-thumb-info__duration")?.text?.trim() || "";
        items.push({ name: title.trim(), imageUrl: thumb, link: href.startsWith("http") ? href : "https://xhamster.com" + href, description: dur ? `Duration: ${dur}` : "" });
      }
      return { list: items, hasNextPage: !!doc.selectFirst(".pager-block__item-next, a.pager-next") };
    }
    async getDetail(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const doc = new Document(res.body);
      const title = doc.selectFirst('meta[property="og:title"]')?.attr("content") || "Unknown";
      const thumb = doc.selectFirst('meta[property="og:image"]')?.attr("content") || "";
      const tags = doc.select(".categories a, .tags-list a").map(el => ({ name: el.text.trim() }));
      return { name: title, imageUrl: thumb, description: "", genre: tags, episodes: [{ name: "▶ Watch", url: url }] };
    }
    async getVideoList(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const html = res.body;
      const videos = [];
      const jsonMatch = html.match(/xHamster\.initEmbedPlayer\(({.+?})\)/s) || html.match(/"sources"\s*:\s*(\[.+?\])/s);
      if (jsonMatch) {
        try {
          const sources = JSON.parse(jsonMatch[1]);
          const arr = Array.isArray(sources) ? sources : (sources.sources || []);
          for (const s of arr) {
            if (s.url) videos.push({ url: s.url, quality: (s.quality || s.name || "Auto") + " · ZeusDL", originalUrl: s.url, headers: this.getHeaders(url) });
          }
        } catch (_) {}
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