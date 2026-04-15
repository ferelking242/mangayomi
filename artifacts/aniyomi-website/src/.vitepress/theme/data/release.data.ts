import { defineLoader } from 'vitepress'
import { Octokit } from '@octokit/rest'
import type { GetResponseDataTypeFromEndpointMethod } from '@octokit/types'

const octokit = new Octokit()

type GitHubRelease = GetResponseDataTypeFromEndpointMethod<typeof octokit.repos.getLatestRelease>

export interface AppRelease {
  stable: GitHubRelease
  preview: GitHubRelease
}

declare const data: AppRelease
export { data }

function makeFallbackRelease(tagName: string): GitHubRelease {
  return {
    url: '',
    assets_url: '',
    upload_url: '',
    html_url: '',
    id: 0,
    author: {} as any,
    node_id: '',
    tag_name: tagName,
    target_commitish: 'main',
    name: tagName,
    draft: false,
    prerelease: false,
    created_at: new Date().toISOString(),
    published_at: new Date().toISOString(),
    assets: [],
    tarball_url: null,
    zipball_url: null,
    body: null,
    mentions_count: undefined,
  }
}

export default defineLoader({
  async load(): Promise<AppRelease> {
    let stable: GitHubRelease = makeFallbackRelease('v1.0.0')
    let preview: GitHubRelease = makeFallbackRelease('r1000')

    try {
      const { data: stableData } = await octokit.repos.getLatestRelease({
        owner: 'ferelking242',
        repo: 'watchtower',
      })
      stable = stableData
    }
    catch {
      // No stable release available yet — using fallback
    }

    try {
      const { data: previewData } = await octokit.repos.getLatestRelease({
        owner: 'ferelking242',
        repo: 'watchtower-preview',
      })
      preview = previewData
    }
    catch {
      // No preview release available yet — using fallback
    }

    return { stable, preview }
  },
})
