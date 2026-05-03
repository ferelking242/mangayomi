const watchtowerSources = [{
    "name": "HQPorner",
    "langs": ["en"],
    "ids": { "en": 600700801 },
    "baseUrl": "https://www.hqporner.com",
    "apiUrl": "https://www.hqporner.com",
    "iconUrl": "https://www.hqporner.com/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "0.1.0",
    "pkgPath": "anime/src/en/hqporner.js"
}];

class DefaultExtension extends MProvider {
    constructor() {
        super();
        this.client = new Client();
    }

    getHeaders() {
        return {
            "Referer": "https://www.hqporner.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        };
    }

    _parseList(html) {
        const list = [];
        // HQPorner uses .main-col-inner / article.col-6 cards
        const re = /<(?:div|article)[^>]+class="[^"]*(?:video|col-|item|thumb)[^"]*"[^>]*>[\s\S]*?<a[^>]+href="([^"]+)"[^>]*>[\s\S]*?<img[^>]+(?:src|data-src|data-lazy)="([^"]+)"[^>]*>[\s\S]*?<(?:h3|h2|span)[^>]+class="[^"]*(?:title|name)[^"]*"[^>]*>([^<]+)</g;
        let m;
        while ((m = re.exec(html)) !== null) {
            const url = m[1].startsWith("http") ? m[1] : `https://www.hqporner.com${m[1]}`;
            list.push({ url, imageUrl: m[2], name: m[3].trim() });
        }
        // Fallback: anchor with hdporn in href
        if (list.length === 0) {
            const re2 = /<a[^>]+href="(\/hdporn\/[^"]+)"[^>]*>[\s\S]*?<img[^>]+(?:src|data-src)="([^"]+)"[^>]*alt="([^"]+)"/g;
            while ((m = re2.exec(html)) !== null) {
                list.push({ url: `https://www.hqporner.com${m[1]}`, imageUrl: m[2], name: m[3].trim() });
            }
        }
        return list;
    }

    _hasNext(html, page) {
        return html.includes(`/page/${page + 1}`) || html.includes(`page=${page + 1}`) || html.includes(`rel="next"`);
    }

    async getPopular(page) {
        const res = await this.client.get(
            `${this.source.baseUrl}/hdporn/popular/all/page/${page}.html`,
            this.getHeaders()
        );
        return { list: this._parseList(res.body), hasNextPage: this._hasNext(res.body, page) };
    }

    async getLatestUpdates(page) {
        const res = await this.client.get(
            `${this.source.baseUrl}/hdporn/new/all/page/${page}.html`,
            this.getHeaders()
        );
        return { list: this._parseList(res.body), hasNextPage: this._hasNext(res.body, page) };
    }

    async search(query, page, filterList) {
        const res = await this.client.get(
            `${this.source.baseUrl}/search/${encodeURIComponent(query.replace(/\s+/g, "-"))}/page/${page}.html`,
            this.getHeaders()
        );
        return { list: this._parseList(res.body), hasNextPage: this._hasNext(res.body, page) };
    }

    async getDetail(url) {
        const fullUrl = url.startsWith("http") ? url : `${this.source.baseUrl}${url}`;
        const res = await this.client.get(fullUrl, this.getHeaders());
        const html = res.body;

        const nameM = html.match(/<h1[^>]*>([^<]+)<\/h1>/) || html.match(/<meta[^>]+og:title[^>]+content="([^"]+)"/);
        const name = nameM ? nameM[1].trim() : "";

        const imgM = html.match(/poster="([^"]+)"/) || html.match(/<meta[^>]+og:image[^>]+content="([^"]+)"/);
        const imageUrl = imgM ? imgM[1] : "";

        const descM = html.match(/<(?:div|p)[^>]+class="[^"]*(?:desc|description|info|about)[^"]*"[^>]*>([\s\S]*?)<\/(?:div|p)>/);
        const description = descM ? descM[1].replace(/<[^>]+>/g, "").trim() : "";

        const tagsRe = /<a[^>]+(?:tag|categor|genre|keyword)[^>]*>([^<]+)<\/a>/gi;
        const genres = [];
        let t;
        while ((t = tagsRe.exec(html)) !== null) {
            const g = t[1].trim();
            if (g.length > 1 && g.length < 60) genres.push(g);
        }

        return {
            name,
            description,
            imageUrl,
            genres: genres.slice(0, 10),
            status: 0,
            chapters: [{ name: "Watch", url: fullUrl, dateUpload: "" }]
        };
    }

    async getVideoList(url) {
        const res = await this.client.get(url, this.getHeaders());
        const html = res.body;
        const videos = [];

        // HQPorner serves HD MP4 directly — extract all resolution variants
        const mp4Re = /["'](https?:\/\/[^"']+\.mp4[^"']*)['"]/gi;
        let m;
        while ((m = mp4Re.exec(html)) !== null) {
            const qual = m[1].match(/(\d{3,4}p)/i)?.[1]
                || (m[1].includes("1080") ? "1080p" : m[1].includes("720") ? "720p" : m[1].includes("480") ? "480p" : "HD");
            if (!videos.find(v => v.url === m[1]))
                videos.push({ url: m[1], quality: qual, originalUrl: m[1] });
        }

        const m3u8Re = /["'](https?:\/\/[^"']+\.m3u8[^"']*)['"]/gi;
        while ((m = m3u8Re.exec(html)) !== null) {
            if (!videos.find(v => v.url === m[1]))
                videos.push({ url: m[1], quality: "HLS", originalUrl: m[1] });
        }

        // HQPorner JSON sources block
        const srcRe = /"sources"\s*:\s*\[([\s\S]*?)\]/g;
        while ((m = srcRe.exec(html)) !== null) {
            const block = m[1];
            const fRe = /["']file["']\s*:\s*["']([^"']+)["']/g;
            const lRe = /["']label["']\s*:\s*["']([^"']+)["']/g;
            const srcs = [], labs = [];
            let s;
            while ((s = fRe.exec(block)) !== null) srcs.push(s[1]);
            while ((s = lRe.exec(block)) !== null) labs.push(s[1]);
            srcs.forEach((src, i) => {
                if (!videos.find(v => v.url === src))
                    videos.push({ url: src, quality: labs[i] || `Source ${i + 1}`, originalUrl: src });
            });
        }

        // Sort by quality descending (1080p > 720p > 480p > others)
        videos.sort((a, b) => {
            const qa = parseInt(a.quality) || 0;
            const qb = parseInt(b.quality) || 0;
            return qb - qa;
        });

        return videos;
    }

    getFilterList() { return []; }
    getSourcePreferences() { return []; }
}
