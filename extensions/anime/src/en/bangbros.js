const watchtowerSources = [{
    "name": "BangBros",
    "langs": ["en"],
    "ids": { "en": 500600701 },
    "baseUrl": "https://site-ma.bangbros.com",
    "apiUrl": "https://site-ma.bangbros.com",
    "iconUrl": "https://bangbros.com/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "0.1.0",
    "pkgPath": "anime/src/en/bangbros.js"
}];

class DefaultExtension extends MProvider {
    constructor() {
        super();
        this.client = new Client();
    }

    getHeaders() {
        return {
            "Referer": "https://site-ma.bangbros.com/",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        };
    }

    _parseList(html) {
        const list = [];
        // BangBros mobile site card pattern
        const re = /<(?:div|article)[^>]+class="[^"]*(?:scene|video|item|thumb)[^"]*"[^>]*>[\s\S]*?<a[^>]+href="([^"]+)"[^>]*>[\s\S]*?<img[^>]+(?:src|data-src|data-original|data-lazy)="([^"]+)"[^>]*>[\s\S]*?<(?:h3|h2|span|div|p)[^>]+class="[^"]*(?:title|name)[^"]*"[^>]*>([^<]+)</g;
        let m;
        while ((m = re.exec(html)) !== null) {
            const url = m[1].startsWith("http") ? m[1] : `https://site-ma.bangbros.com${m[1]}`;
            list.push({ url, imageUrl: m[2], name: m[3].trim() });
        }
        if (list.length === 0) {
            const re2 = /<a[^>]+href="(\/(?:video|scene)\/[^"]+)"[^>]*>[\s\S]*?<img[^>]+(?:src|data-src)="([^"]+)"[\s\S]*?<\/a>[\s\S]*?<(?:h3|h2)[^>]*>([^<]+)</g;
            while ((m = re2.exec(html)) !== null) {
                list.push({ url: `https://site-ma.bangbros.com${m[1]}`, imageUrl: m[2], name: m[3].trim() });
            }
        }
        return list;
    }

    _hasNext(html, page) {
        return html.includes(`page=${page + 1}`) || html.includes(`?page=${page + 1}`) || html.includes(`rel="next"`) || html.includes(`/page/${page + 1}`);
    }

    async getPopular(page) {
        const res = await this.client.get(
            `${this.source.baseUrl}/most-popular?page=${page}`,
            this.getHeaders()
        );
        return { list: this._parseList(res.body), hasNextPage: this._hasNext(res.body, page) };
    }

    async getLatestUpdates(page) {
        const res = await this.client.get(
            `${this.source.baseUrl}/videos?page=${page}`,
            this.getHeaders()
        );
        return { list: this._parseList(res.body), hasNextPage: this._hasNext(res.body, page) };
    }

    async search(query, page, filterList) {
        const res = await this.client.get(
            `${this.source.baseUrl}/search?q=${encodeURIComponent(query)}&page=${page}`,
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

        const descM = html.match(/<(?:div|p)[^>]+class="[^"]*(?:desc|description|synopsis|summary)[^"]*"[^>]*>([\s\S]*?)<\/(?:div|p)>/);
        const description = descM ? descM[1].replace(/<[^>]+>/g, "").trim() : "";

        const tagsRe = /<a[^>]+(?:tag|categor|niche|channel)[^>]*>([^<]+)<\/a>/gi;
        const genres = [];
        let t;
        while ((t = tagsRe.exec(html)) !== null) {
            const g = t[1].trim();
            if (g.length > 1 && g.length < 50) genres.push(g);
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

        // BangBros often has JSON data in <script> tags
        const jsonRe = /<script[^>]+type="application\/json"[^>]*>([\s\S]*?)<\/script>/gi;
        let m;
        while ((m = jsonRe.exec(html)) !== null) {
            try {
                const data = JSON.parse(m[1]);
                const checkObj = (obj) => {
                    if (!obj || typeof obj !== "object") return;
                    if (obj.url && (obj.url.includes(".mp4") || obj.url.includes(".m3u8"))) {
                        videos.push({ url: obj.url, quality: obj.quality || obj.label || "Stream", originalUrl: obj.url });
                    }
                    Object.values(obj).forEach(v => { if (typeof v === "object") checkObj(v); });
                };
                checkObj(data);
            } catch (e) {}
        }

        const mp4Re = /["'](https?:\/\/[^"']+\.mp4[^"']*)['"]/gi;
        while ((m = mp4Re.exec(html)) !== null) {
            if (!videos.find(v => v.url === m[1]))
                videos.push({ url: m[1], quality: m[1].match(/(\d{3,4}p)/i)?.[1] || "MP4", originalUrl: m[1] });
        }

        const m3u8Re = /["'](https?:\/\/[^"']+\.m3u8[^"']*)['"]/gi;
        while ((m = m3u8Re.exec(html)) !== null) {
            if (!videos.find(v => v.url === m[1]))
                videos.push({ url: m[1], quality: "HLS", originalUrl: m[1] });
        }

        return videos;
    }

    getFilterList() { return []; }
    getSourcePreferences() { return []; }
}
