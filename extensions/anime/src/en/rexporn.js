const watchtowerSources = [{
    "name": "RexPorn",
    "langs": ["en"],
    "ids": { "en": 400500601 },
    "baseUrl": "https://www.rexporn.st",
    "apiUrl": "https://www.rexporn.st",
    "iconUrl": "https://www.rexporn.st/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "0.1.0",
    "pkgPath": "anime/src/en/rexporn.js"
}];

class DefaultExtension extends MProvider {
    constructor() {
        super();
        this.client = new Client();
    }

    getHeaders() {
        return {
            "Referer": "https://www.rexporn.st/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        };
    }

    _parseList(html) {
        const list = [];
        // RexPorn standard tube layout
        const re = /<(?:div|article)[^>]+class="[^"]*(?:video|item|thumb)[^"]*"[^>]*>[\s\S]*?<a[^>]+href="([^"]+)"[^>]*>[\s\S]*?<img[^>]+(?:src|data-src|data-original)="([^"]+)"[^>]*>[\s\S]*?<(?:h3|h2|span|strong)[^>]*>([^<]+)</g;
        let m;
        while ((m = re.exec(html)) !== null) {
            const url = m[1].startsWith("http") ? m[1] : `https://www.rexporn.st${m[1]}`;
            list.push({ url, imageUrl: m[2], name: m[3].trim() });
        }
        if (list.length === 0) {
            const re2 = /<a[^>]+href="(https?:\/\/(?:www\.)?rexporn\.st\/[^"]+/video/[^"]+)"[^>]*>[\s\S]*?<img[^>]+(?:src|data-src)="([^"]+)"[^>]*>[\s\S]*?title="([^"]+)"/g;
            while ((m = re2.exec(html)) !== null) {
                list.push({ url: m[1], imageUrl: m[2], name: m[3].trim() });
            }
        }
        return list;
    }

    _hasNext(html, page) {
        return html.includes(`?page=${page + 1}`) || html.includes(`page=${page + 1}`) || html.includes(`rel="next"`);
    }

    async getPopular(page) {
        const res = await this.client.get(
            `${this.source.baseUrl}/most-popular/year?page=${page}`,
            this.getHeaders()
        );
        return { list: this._parseList(res.body), hasNextPage: this._hasNext(res.body, page) };
    }

    async getLatestUpdates(page) {
        const res = await this.client.get(
            `${this.source.baseUrl}/newest/?page=${page}`,
            this.getHeaders()
        );
        return { list: this._parseList(res.body), hasNextPage: this._hasNext(res.body, page) };
    }

    async search(query, page, filterList) {
        const res = await this.client.get(
            `${this.source.baseUrl}/search/${encodeURIComponent(query.replace(/\s+/g, "+"))}?page=${page}`,
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

        const tagsRe = /<a[^>]+(?:tag|categor|genre|niche)[^>]*>([^<]+)<\/a>/gi;
        const genres = [];
        let t;
        while ((t = tagsRe.exec(html)) !== null) genres.push(t[1].trim());

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

        // Extract from inline JS — common xvideos/rexporn pattern
        const flashVarRe = /flashvars\s*=\s*\{([\s\S]*?)\}/g;
        let m;
        while ((m = flashVarRe.exec(html)) !== null) {
            const block = m[1];
            const urlRe = /(?:video_url|url_high|url_low|hd_url|sd_url|url)\s*:\s*["']([^"']+)["']/g;
            const labRe = /(?:video_url_text|quality|label)\s*:\s*["']([^"']+)["']/g;
            const urls = [], labels = [];
            let s;
            while ((s = urlRe.exec(block)) !== null) urls.push(s[1]);
            while ((s = labRe.exec(block)) !== null) labels.push(s[1]);
            urls.forEach((u, i) => {
                if (!videos.find(v => v.url === u))
                    videos.push({ url: u, quality: labels[i] || "Stream", originalUrl: u });
            });
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
