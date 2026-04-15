import type { DefaultTheme } from 'vitepress'

const nav: DefaultTheme.NavItem[] = [
  {
    text: 'Get v{app_version}',
    activeMatch: '^/*?(download|changelogs)/*?$',
    items: [
      {
        text: 'Download',
        link: '/download/',
      },
      {
        text: 'Changelogs',
        link: '/changelogs/',
      },
    ],
  },
  {
    text: 'Docs',
    activeMatch: '/docs/',
    items: [
      {
        text: 'Guides',
        items: [
          { text: 'Getting started', link: '/docs/guides/getting-started' },
          { text: 'Light Novel reader', link: '/docs/guides/light-novel-reader' },
          { text: 'Reader settings', link: '/docs/guides/reader-settings' },
          { text: 'Tracking', link: '/docs/guides/tracking' },
          { text: 'Backups', link: '/docs/guides/backups' },
          { text: 'Source migration', link: '/docs/guides/source-migration' },
        ],
      },
      {
        text: 'FAQ',
        items: [
          { text: 'General', link: '/docs/faq/general' },
          { text: 'Library', link: '/docs/faq/library' },
          { text: 'Reader', link: '/docs/faq/reader' },
          { text: 'Downloads', link: '/docs/faq/downloads' },
          { text: 'Storage', link: '/docs/faq/storage' },
        ],
      },
    ],
  },
  {
    text: 'News',
    link: '/news/',
    activeMatch: '/news/',
  },
  {
    text: 'Community',
    items: [
      {
        text: 'GitHub',
        link: 'https://github.com/ferelking242/watchtower',
      },
      {
        text: 'Discord',
        link: 'https://discord.gg/F32UjdJZrR',
      },
      {
        text: 'Forks',
        link: '/forks/',
      },
      {
        text: 'Contribute',
        link: '/docs/contribute',
      },
    ],
  },
]

export default nav
