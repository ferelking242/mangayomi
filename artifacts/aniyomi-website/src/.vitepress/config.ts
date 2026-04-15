import process from 'node:process'
import { URL, fileURLToPath } from 'node:url'
import { defineConfig, loadEnv } from 'vitepress'
import ElementPlus from 'unplugin-element-plus/vite'

import markdownConfig from './config/markdownConfig'

// For use with loading Markdown plugins
import themeConfig from './config/themeConfig'

// Theme related config
import headConfig from './config/headConfig'

import generateMeta from './config/hooks/generateMeta'

// Enhanced meta generation
import generateFeed from './config/hooks/generateFeed'

// Allows generation of RSS feed
import generateOgImages from './config/hooks/generateOgImages'

const title = 'Watchtower'
const description = 'Watch anime, read manga and light novels from hundreds of sources — all in one powerful Android app.'

const env = loadEnv('', process.cwd())
const hostname: string = env.VITE_HOSTNAME || 'http://localhost:4173'

export default defineConfig({
  base: '/aniyomi-website/',
  outDir: '../dist',
  lastUpdated: true,
  cleanUrls: true,
  title,
  description,
  sitemap: {
    hostname,
  },
  head: headConfig,
  markdown: markdownConfig,
  themeConfig,
  transformHead: async context => generateMeta(context, hostname),
  buildEnd: async (context) => {
    generateFeed(context, hostname)
    generateOgImages(context)
  },
  vite: {
    resolve: {
      alias: [
        {
          // Used to show the release version on navbar.
          find: /^.*\/VPNavBarMenu\.vue$/,
          replacement: fileURLToPath(
            new URL('./theme/components/CustomNavBarMenu.vue', import.meta.url),
          ),
        },
        {
          find: /^.*VPNavScreenMenu\.vue$/,
          replacement: fileURLToPath(
            new URL('./theme/components/CustomNavScreenMenu.vue', import.meta.url),
          ),
        },
        {
          find: /^.*VPSwitchAppearance\.vue$/,
          replacement: fileURLToPath(
            new URL('./theme/components/CustomSwitchAppearance.vue', import.meta.url),
          ),
        },
      ],
    },
    plugins: [ElementPlus({})],
    ssr: {
      noExternal: ['element-plus'],
    },
    server: {
      allowedHosts: true,
    },
  },
})
