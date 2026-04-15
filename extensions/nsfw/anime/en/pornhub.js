const mangayomiSources = [{
    "name": "PornHub",
    "lang": "en",
    "baseUrl": "https://www.pornhub.com",
    "apiUrl": "",
    "iconUrl": "https://www.pornhub.com/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "1.0.0",
    "pkgPath": "pornhub/en/en.pornhub.js",
    "notes": "Adult content (18+) — ZeusDL powered streaming",
    "isNsfw": true
  }];
  class PornHub extends MProvider {
    getHeaders(url) {
      return { "Referer": "https://www.pornhub.com/", "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36", "Cookie": "accessAgeDisclaimerPH=1; platform=pc" };
    }
    async getPopular(page) {
      const url = `https://www.pornhub.com/video?o=mv&page=${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    get supportsLatest() { return true; }
    async getLatestUpdates(page) {
      const url = `https://www.pornhub.com/video?o=n&page=${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    async search(query, page, filters) {
      const q = encodeURIComponent(query.trim());
      const url = `https://www.pornhub.com/video/search?search=${q}&page=${page}`;
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      return this._parse(res.body);
    }
    _parse(html) {
      const doc = new Document(html);
      const items = [];
      const cards = doc.select("li.pcVideoListItem, .videoBox");
      for (const card of cards) {
        const a = card.selectFirst("a[href*='/view_video.php']") || card.selectFirst("a.videoPreviewBg");
        if (!a) continue;
        const href = a.attr("href") || "";
        if (!href) continue;
        const title = a.attr("title") || card.selectFirst(".title a")?.text || "Unknown";
        const img = card.selectFirst("img");
        const thumb = img?.attr("data-mediabook") || img?.attr("data-src") || img?.attr("src") || "";
        const dur = card.selectFirst(".videoDuration")?.text?.trim() || "";
        const link = href.startsWith("http") ? href : "https://www.pornhub.com" + href;
        items.push({ name: title.trim(), imageUrl: thumb, link, description: dur ? `Duration: ${dur}` : "" });
      }
      return { list: items, hasNextPage: !!doc.selectFirst(".pagination .next_multy") };
    }
    async getDetail(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const doc = new Document(res.body);
      const title = doc.selectFirst('meta[property="og:title"]')?.attr("content") || "Unknown";
      const thumb = doc.selectFirst('meta[property="og:image"]')?.attr("content") || "";
      const desc = doc.selectFirst(".infoWrapper .categoriesWrap")?.text || "";
      const tags = doc.select(".tagsWrapper a, .categoriesWrap a").map(el => ({ name: el.text.trim() }));
      return { name: title, imageUrl: thumb, description: desc, genre: tags, episodes: [{ name: "▶ Watch", url: url }] };
    }
    async getVideoList(url) {
      const res = await new Client().get(url, { headers: this.getHeaders(url) });
      const html = res.body;
      const videos = [];
      const qualityRx = /\{quality:\s*(\d+)p?,\s*videoUrl:\s*['"]([^'"]+)['"]/g;
      let m;
      while ((m = qualityRx.exec(html)) !== null) {
        videos.push({ url: m[2], quality: `${m[1]}p · ZeusDL`, originalUrl: m[2], headers: this.getHeaders(url) });
      }
      if (videos.length === 0) {
        const hlsMatch = html.match(/(?:hls|master)\s*:\s*['"]([^'"]+\.m3u8[^'"]*)['"]/);
        if (hlsMatch) videos.push({ url: hlsMatch[1], quality: "HLS · ZeusDL", originalUrl: hlsMatch[1], headers: this.getHeaders(url) });
      }
      if (videos.length === 0) {
        const jsonRx = /"videoUrl"\s*:\s*"([^"]+\.(?:mp4|m3u8)[^"]*)"/g;
        while ((m = jsonRx.exec(html)) !== null) {
          videos.push({ url: m[1].replace(/\\\/g, ""), quality: "Auto · ZeusDL", originalUrl: m[1], headers: this.getHeaders(url) });
          if (videos.length >= 3) break;
        }
      }
      return videos;
    }
    async getPageList(url) { return []; }
    getFilterList() { return []; }
    getSourcePreferences() { return []; }
  }