const watchtowerSources = [{
    "name": "Wow.xxx",
    "langs": ["en"],
    "ids": { "en": 200300401 },
    "baseUrl": "https://www.wow.xxx",
    "apiUrl": "https://www.wow.xxx",
    "iconUrl": "https://www.wow.xxx/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "0.1.0",
    "pkgPath": "anime/src/en/wowxxx.js"
}];

class DefaultExtension extends MProvider {
    constructor() {
        super();
        this.client = new Client();
    }

    getHeaders() {
        return {
            "Referer": "https://www.wow.xxx/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        };
    }

    _parseList(html) {
        const list = [];
        // wow.xxx uses .thumb-video / .video-item cards
        const re = /<(?:div|article)[^>]+class="[^"]*(?:thumb|video-item|item)[^"]*"[^>]*>[\s\S]*?<a[^>]+href="([^"]+)"[^>]*>[\s\S]*?<img[^>]+(?:src|data-src|data-original)="([^"]+)"[^>]*>[\s\S]*?(?:<(?:span|h3|div)[^>]+class="[^"]*(?:title|name)[^"]*"[^>]*>([^<]+)<|title="([^"]+)")/g;
        let m;
        while ((m = re.exec(html)) !== null) {
            const url = m[1].startsWith("http") ? m[1] : `https://www.wow.xxx${m[1]}`;
            const name = (m[3] || m[4] || "").trim();
            if (name) list.push({ url, imageUrl: m[2], name });
        }
        // Fallback: og:url + og:image + og:title from meta for single page
        if (list.length === 0) {
            const urlM = html.match(/<meta[^>]+property="og:url"[^>]+content="([^"]+)"/);
            const imgM = html.match(/<meta[^>]+property="og:image"[^>]+content="([^"]+)"/);
            const ttlM = html.match(/<meta[^>]+property="og:title"[^>]+content="([^"]+)"/);
            if (urlM && ttlM) list.push({ url: urlM[1], imageUrl: imgM?.[1] || "", name: ttlM[1].trim() });
        }
        return list;
    }

    _hasNext(html, page) {
        return html.includes(`?p=${page + 1}`) || html.includes(`page=${page + 1}`) || html.includes(`rel="next"`);
    }

    async getPopular(page) {
        const res = await this.client.get(
            `${this.source.baseUrl}/videos/popular/?p=${page}`,
            this.getHeaders()
        );
        return { list: this._parseList(res.body), hasNextPage: this._hasNext(res.body, page) };
    }

    async getLatestUpdates(page) {
        const res = await this.client.get(
            `${this.source.baseUrl}/videos/?p=${page}`,
            this.getHeaders()
        );
        return { list: this._parseList(res.body), hasNextPage: this._hasNext(res.body, page) };
    }

    async search(query, page, filterList) {
        const res = await this.client.get(
            `${this.source.baseUrl}/videos/?s=${encodeURIComponent(query)}&p=${page}`,
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

        const descM = html.match(/<(?:div|p)[^>]+class="[^"]*(?:desc|description|about)[^"]*"[^>]*>([\s\S]*?)<\/(?:div|p)>/);
        const description = descM ? descM[1].replace(/<[^>]+>/g, "").trim() : "";

        const imgM = html.match(/<meta[^>]+og:image[^>]+content="([^"]+)"/) || html.match(/poster="([^"]+)"/);
        const imageUrl = imgM ? imgM[1] : "";

        const tagsRe = /<a[^>]+(?:tag|categor|genre)[^>]*>([^<]+)<\/a>/gi;
        const genres = [];
        let tm;
        while ((tm = tagsRe.exec(html)) !== null) genres.push(tm[1].trim());

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

        const mp4Re = /["'](https?:\/\/[^"']+\.mp4[^"']*)['"]/gi;
        let m;
        while ((m = mp4Re.exec(html)) !== null) {
            const qual = m[1].match(/(\d{3,4}p)/i)?.[1] || "MP4";
            if (!videos.find(v => v.url === m[1]))
                videos.push({ url: m[1], quality: qual, originalUrl: m[1] });
        }

        const m3u8Re = /["'](https?:\/\/[^"']+\.m3u8[^"']*)['"]/gi;
        while ((m = m3u8Re.exec(html)) !== null) {
            if (!videos.find(v => v.url === m[1]))
                videos.push({ url: m[1], quality: "HLS", originalUrl: m[1] });
        }

        // jwplayer / videojs sources
        const jwRe = /sources\s*:\s*\[([\s\S]*?)\]/g;
        while ((m = jwRe.exec(html)) !== null) {
            const block = m[1];
            const srcRe = /["']file["']\s*:\s*["']([^"']+)["']/g;
            const labRe = /["']label["']\s*:\s*["']([^"']+)["']/g;
            const srcs = [], labs = [];
            let s;
            while ((s = srcRe.exec(block)) !== null) srcs.push(s[1]);
            while ((s = labRe.exec(block)) !== null) labs.push(s[1]);
            srcs.forEach((src, i) => {
                if (!videos.find(v => v.url === src))
                    videos.push({ url: src, quality: labs[i] || `Quality ${i + 1}`, originalUrl: src });
            });
        }

        return videos;
    }

    getFilterList() { return []; }
    getSourcePreferences() { return []; }
}
