// Only known color tokens cross the first-party embedding boundary.
export const TOKEN_MAP = {
  '--cms-page': '--night', '--cms-surface': '--dusk', '--cms-text': '--paper',
  '--cms-border': '--haze', '--cms-brand-primary': '--accent',
  '--cms-brand-accent': '--ok', '--cms-danger': '--alert',
}
export function channels(value) {
  if (typeof value !== 'string' || !/^#[\da-f]{6}$/i.test(value)) return null
  return [1, 3, 5].map(start => parseInt(value.slice(start, start + 2), 16)).join(' ')
}
export function acceptsAppearance(event, parent, origin) {
  return event.source === parent && event.origin === origin && event.data?.type === 'cms:appearance'
    && event.data.version === 1 && ['light','dark'].includes(event.data.mode)
}
export function configurationTokens(config, mode) {
  const { brand, surface, semantic } = config.theme
  const dark = mode === 'dark'
  const result = { '--cms-page': dark ? '#121417' : surface.page, '--cms-surface': dark ? '#1A1D21' : surface.surface,
    '--cms-text': dark ? '#E5E7EB' : surface.text, '--cms-border': dark ? '#2D3035' : surface.border,
    '--cms-brand-primary': dark ? brand.primary_light : brand.primary, '--cms-brand-accent': brand.accent,
    '--cms-danger': semantic.danger }
  for (const [key,value] of Object.entries(config.theme.advanced_overrides || {})) {
    if (key in TOKEN_MAP && channels(value)) result[key] = value
  }
  return result
}
