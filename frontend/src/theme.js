import { ref, watch } from 'vue'
import { acceptsAppearance, channels, configurationTokens, TOKEN_MAP } from './appearance'

const STORAGE_KEY = 'gatherplay-theme'
const NEXT = { auto: 'light', light: 'dark', dark: 'auto' }
const root = document.documentElement
export const embedded = window.parent !== window && new URLSearchParams(window.location.search).get('embed') === 'cms'
export const resolvedTheme = ref('light')
export const brand = ref({ short_name: 'GatherPlay', logo_light: '/assets/quizzly/images/gatherplay-logo.svg' })
export const theme = ref(localStorage.getItem(STORAGE_KEY) === 'system' ? 'auto' : localStorage.getItem(STORAGE_KEY) || localStorage.getItem('quizzly-theme') || 'auto')
let configuration = null
let inherited = false
const media = matchMedia('(prefers-color-scheme: dark)')
if (embedded) root.dataset.embedded = 'cms'

function apply(tokens, mode, branding) {
  resolvedTheme.value = mode
  root.dataset.theme = mode
  root.style.colorScheme = mode
  for (const [source,target] of Object.entries(TOKEN_MAP)) {
    const color = channels(tokens?.[source])
    if (color) root.style.setProperty(target, color)
  }
  root.dataset.sharedBranding = 'true'
  if (branding?.short_name && typeof branding.short_name === 'string') brand.value = { ...branding, logo_light: branding.logo_light || '/assets/church_management_system/images/cms-member-icon.svg' }
}
function applyLocal() {
  if (inherited) return
  const mode = theme.value === 'auto' ? (media.matches ? 'dark' : 'light') : theme.value
  resolvedTheme.value = mode
  root.dataset.theme = mode
  root.style.colorScheme = mode
  if (configuration) apply(configurationTokens(configuration, mode), mode, configuration.branding)
}
export function cycleTheme() { if (!embedded) theme.value = NEXT[theme.value] || 'auto' }
watch(theme, value => {
  if (!embedded) localStorage.setItem(STORAGE_KEY, value === 'auto' ? 'system' : value)
  applyLocal()
}, { immediate: true })
media.addEventListener('change', applyLocal)
window.addEventListener('storage', event => {
  if (!embedded && event.key === STORAGE_KEY) theme.value = event.newValue === 'system' ? 'auto' : event.newValue || 'auto'
})
if (embedded) {
  window.addEventListener('message', event => {
    if (!acceptsAppearance(event, window.parent, location.origin)) return
    inherited = true
    theme.value = event.data.mode
    apply(event.data.tokens, event.data.mode, event.data.branding)
    // Game copy currently remains English; do not mislabel it for screen readers.
    root.lang = 'en'
  })
  window.parent.postMessage({ type: 'quizzly:ready', version: 1 }, location.origin)
}
// The embedded compatibility provider is a fallback until the parent sends appearance.
if (embedded) fetch('/api/method/quizzly.branding.get_application_branding')
  .then(response => response.ok ? response.json() : null)
  .then(payload => {
    const config = payload?.message?.configuration
    if (config?.theme?.brand && config?.theme?.surface && config?.theme?.semantic) {
      configuration = config; applyLocal()
    }
  }).catch(() => { /* The independent Quizzly palette remains available. */ })
