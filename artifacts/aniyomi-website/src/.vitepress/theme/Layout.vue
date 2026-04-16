<script setup lang='ts'>
import { useData } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import { nextTick, provide, ref, onMounted } from 'vue'
import WebViewPanel from './components/WebViewPanel.vue'

const { isDark } = useData()
const webViewRef = ref<InstanceType<typeof WebViewPanel> | null>(null)

function shouldEnableTransitions() {
  return 'startViewTransition' in document
    && window.matchMedia('(prefers-reduced-motion: no-preference)').matches
}

provide('toggle-appearance', async ({ clientX: x, clientY: y }: MouseEvent) => {
  if (!shouldEnableTransitions()) {
    isDark.value = !isDark.value
    return
  }

  const clipPath = [
    `circle(0px at ${x}px ${y}px)`,
    `circle(${Math.hypot(
      Math.max(x, innerWidth - x),
      Math.max(y, innerHeight - y),
    )}px at ${x}px ${y}px)`,
  ]

  // @ts-expect-error Missing types as its experimental
  await document.startViewTransition(async () => {
    isDark.value = !isDark.value
    await nextTick()
  }).ready

  document.documentElement.animate(
    { clipPath: isDark.value ? clipPath.reverse() : clipPath },
    {
      duration: 300,
      easing: 'ease-in',
      pseudoElement: `::view-transition-${isDark.value ? 'old' : 'new'}(root)`,
    },
  )
})

onMounted(() => {
  document.addEventListener('click', (e: MouseEvent) => {
    const anchor = (e.target as HTMLElement).closest('a[href]') as HTMLAnchorElement | null
    if (!anchor) return
    const href = anchor.href
    if (!href || href.startsWith('#') || href.startsWith('javascript:')) return
    if (
      (href.startsWith('http://') || href.startsWith('https://')) &&
      !href.includes(window.location.hostname)
    ) {
      e.preventDefault()
      webViewRef.value?.openPanel(href)
    }
  })
})
</script>

<template>
  <DefaultTheme.Layout />
  <WebViewPanel ref="webViewRef" />
</template>

<style lang='stylus'>
::view-transition-old(root),
::view-transition-new(root) {
  animation: none
  mix-blend-mode: normal
}

::view-transition-old(root),
.dark::view-transition-new(root) {
  z-index: 1
}

::view-transition-new(root),
.dark::view-transition-old(root) {
  z-index: 9999
}
</style>
