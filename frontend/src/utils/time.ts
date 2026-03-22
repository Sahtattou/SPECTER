export function formatUtc(value: string | null | undefined): string {
  if (!value) {
    return '—'
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return parsed.toISOString().replace('T', ' ').replace('Z', ' UTC')
}

export function statusLabel(detected: number | null): 'CAUGHT' | 'MISSED' | 'PENDING' {
  if (detected === 1) {
    return 'CAUGHT'
  }
  if (detected === 0) {
    return 'MISSED'
  }
  return 'PENDING'
}
