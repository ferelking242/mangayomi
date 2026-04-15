const mangayomiSources = [{
    "name": "XNXX",
    "lang": "en",
    "baseUrl": "https://www.xnxx.com",
    "apiUrl": "",
    "iconUrl": "https://www.xnxx.com/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "1.0.3",
    "pkgPath": "xnxx/en/en.xnxx.js",
    "notes": "Adult content (18+) — ZeusDL powered streaming",
    "isNsfw": true
  }];

  class XNXX extends MProvider {
    getHeaders(url) {
      return {
        "Referer": "https://www.xnxx.com/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
      };
    }
    async getPopular(page) {
      const url = `https://www.xnxx.com/search/videos/${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parseVideoList(res.body, "https://www.xnxx.com");
    }
    get supportsLatest() { return true; }
    async getLatestUpdates(page) {
      const url = `https://www.xnxx.com/search/videos/${page}?sort=upload-date`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parseVideoList(res.body, "https://www.xnxx.com");
    }
    async search(query, page, filters) {
      const q = encodeURIComponent(query.trim().replace(/\s+/g, "+"));
      const url = `https://www.xnxx.com/search/${q}/${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parseVideoList(res.body, "https://www.xnxx.com");
    }
    _parseVideoList(html, base) {
      const doc = new Document(html);
      const items = [];
      const cards = doc.select(".mozaique .thumb-block");
      for (const card of cards) {
        const anchor = card.selectFirst("a");
        if (!anchor) continue;
        const href = anchor.attr("href") || "";
        if (!href || href === "#") continue;
        const titleEl = card.selectFirst(".title a") || card.selectFirst("a[title]");
        const title = (titleEl && (titleEl.attr("title") || titleEl.text)) || anchor.attr("title") || "Unknown";
        const imgEl = card.selectFirst("img");
        const thumb = (imgEl && (imgEl.attr("data-src") || imgEl.attr("data-original") || imgEl.attr("src"))) || "";
        const durationEl = card.selectFirst(".duration");
        const duration = durationEl ? durationEl.text.trim() : "";
        items.push({
          name: title.trim(),
          imageUrl: thumb,
          link: href.startsWith("http") ? href : base + href,
          description: duration ? `Duration: ${duration}` : ""
        });
      }
      const hasNext = !!doc.selectFirst(".pagination .next, a[rel='next']");
      return { list: items, hasNextPage: hasNext };
    }
    async getDetail(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const doc = new Document(res.body);
      const title = doc.selectFirst("h2.page-title, h1.content-title")?.text || doc.selectFirst('meta[property="og:title"]')?.attr("content") || "Unknown";
      const description = doc.selectFirst(".video-description, .metadata")?.text || "";
      const thumb = doc.selectFirst('meta[property="og:image"]')?.attr("content") || "";
      const tagsEls = doc.select(".video-tags a, .tags a");
      const tags = tagsEls.map(el => ({ name: el.text.trim() }));
      return { name: title.trim(), imageUrl: thumb, description: description.trim(), genre: tags, episodes: [{ name: "▶ Watch", url: url }] };
    }
    async getVideoList(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const html = res.body;
      const videos = [];
      const hlsMatch = html.match(/html5player\.setVideoHLS\(['"]([^'"]+)['"]\)/);
      if (hlsMatch) videos.push({ url: hlsMatch[1], quality: "HLS · ZeusDL", originalUrl: hlsMatch[1], headers: this.getHeaders(url) });
      const hiMatch = html.match(/html5player\.setVideoUrlHigh\(['"]([^'"]+)['"]\)/);
      if (hiMatch) videos.push({ url: hiMatch[1], quality: "HD · ZeusDL", originalUrl: hiMatch[1], headers: this.getHeaders(url) });
      const loMatch = html.match(/html5player\.setVideoUrlLow\(['"]([^'"]+)['"]\)/);
      if (loMatch) videos.push({ url: loMatch[1], quality: "SD · ZeusDL", originalUrl: loMatch[1], headers: this.getHeaders(url) });
      return videos;
    }
    async getPageList(url) { return []; }
    getFilterList() { return []; }
    getSourcePreferences() { return []; }
  }