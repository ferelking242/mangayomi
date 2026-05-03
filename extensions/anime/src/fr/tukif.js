const watchtowerSources = [{
    "name": "Tukif",
    "langs": ["fr"],
    "ids": { "fr": 100200301 },
    "baseUrl": "https://www.tukif.com",
    "apiUrl": "https://www.tukif.com",
    "iconUrl": "https://www.tukif.com/favicon.ico",
    "typeSource": "single",
    "itemType": 1,
    "version": "0.1.0",
    "pkgPath": "anime/src/fr/tukif.js"
}];

class DefaultExtension extends MProvider {
    constructor() {
        super();
        this.client = new Client();
    }

    getHeaders() {
        return {
            "Referer": "https://www.tukif.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        };
    }

    _parseList(html) {
        const list = [];
        // Tukif video cards: <div class="video-thumb">
        const re = /<div[^>]+class="[^"]*video-thumb[^"]*"[^>]*>[\s\S]*?<a[^>]+href="([^"]+)"[^>]*>[\s\S]*?<img[^>]+(?:src|data-src)="([^"]+)"[^>]*>[\s\S]*?<span[^>]+class="[^"]*title[^"]*"[^>]*>([^<]+)<\/span>/g;
        let m;
        while ((m = re.exec(html)) !== null) {
            const url = m[1].startsWith("http") ? m[1] : `https://www.tukif.com${m[1]}`;
            list.push({ url, imageUrl: m[2], name: m[3].trim() });
        }
        // Fallback: article-based cards
        if (list.length === 0) {
            const re2 = /<a[^>]+href="(https?:\/\/www\.tukif\.com\/video\/[^"]+)"[^>]*>[\s\S]*?<img[^>]+(?:src|data-src)="([^"]+)"[^>]*>[\s\S]*?<\/a>[\s\S]*?<(?:span|h3|p)[^>]*class="[^"]*(?:title|name)[^"]*"[^>]*>([^<]{3,})<\//g;
            while ((m = re2.exec(html)) !== null) {
                list.push({ url: m[1], imageUrl: m[2], name: m[3].trim() });
            }
        }
        return list;
    }

    _hasNext(html, page) {
        return html.includes(`page=${page + 1}`) || html.includes(`?page=${page + 1}`) || html.includes(`rel="next"`);
    }

    async getPopular(page) {
        const res = await this.client.get(
            `${this.source.baseUrl}/pornos-populaire.html?page=${page}`,
            this.getHeaders()
        );
        return { list: this._parseList(res.body), hasNextPage: this._hasNext(res.body, page) };
    }

    async getLatestUpdates(page) {
        const res = await this.client.get(
            `${this.source.baseUrl}/pornos-recents.html?page=${page}`,
            this.getHeaders()
        );
        return { list: this._parseList(res.body), hasNextPage: this._hasNext(res.body, page) };
    }

    async search(query, page, filterList) {
        const res = await this.client.get(
            `${this.source.baseUrl}/recherche/?q=${encodeURIComponent(query)}&page=${page}`,
            this.getHeaders()
        );
        return { list: this._parseList(res.body), hasNextPage: this._hasNext(res.body, page) };
    }

    async getDetail(url) {
        const fullUrl = url.startsWith("http") ? url : `${this.source.baseUrl}${url}`;
        const res = await this.client.get(fullUrl, this.getHeaders());
        const html = res.body;

        const nameM = html.match(/<h1[^>]*>([^<]+)<\/h1>/);
        const name = nameM ? nameM[1].trim() : "";

        const descM = html.match(/<(?:div|p)[^>]+class="[^"]*(?:description|desc)[^"]*"[^>]*>([\s\S]*?)<\/(?:div|p)>/);
        const description = descM ? descM[1].replace(/<[^>]+>/g, "").trim() : "";

        const imgM = html.match(/<(?:meta[^>]+og:image[^>]+content|video[^>]+poster)="([^"]+)"/);
        const imageUrl = imgM ? imgM[1] : "";

        return {
            name,
            description,
            imageUrl,
            genres: [],
            status: 0,
            chapters: [{
                name: "Regarder",
                url: fullUrl,
                dateUpload: ""
            }]
        };
    }

    async getVideoList(url) {
        const res = await this.client.get(url, this.getHeaders());
        const html = res.body;
        const videos = [];

        // Direct MP4
        const mp4Re = /(?:file|src|source)['":\s]+["'](https?:\/\/[^"']+\.mp4[^"']*)['"]/gi;
        let m;
        while ((m = mp4Re.exec(html)) !== null) {
            const label = m[0].match(/(\d{3,4}p)/i)?.[1] || "Tukif";
            videos.push({ url: m[1], quality: label, originalUrl: m[1] });
        }

        // M3U8 / HLS
        const m3u8Re = /["'](https?:\/\/[^"']+\.m3u8[^"']*)['"]/gi;
        while ((m = m3u8Re.exec(html)) !== null) {
            videos.push({ url: m[1], quality: "HLS", originalUrl: m[1] });
        }

        // JSON playlist (sources array)
        const sourcesRe = /"sources"\s*:\s*\[([\s\S]*?)\]/g;
        while ((m = sourcesRe.exec(html)) !== null) {
            const block = m[1];
            const srcRe = /"(?:file|src)"\s*:\s*"([^"]+)"/g;
            const labelRe = /"label"\s*:\s*"([^"]+)"/g;
            const srcs = [], labels = [];
            let sm;
            while ((sm = srcRe.exec(block)) !== null) srcs.push(sm[1]);
            while ((sm = labelRe.exec(block)) !== null) labels.push(sm[1]);
            srcs.forEach((s, i) => {
                if (!videos.find(v => v.url === s))
                    videos.push({ url: s, quality: labels[i] || `Source ${i + 1}`, originalUrl: s });
            });
        }

        return videos;
    }

    getFilterList() { return []; }
    getSourcePreferences() { return []; }
}
