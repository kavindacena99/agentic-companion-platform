const PERSONA_MAP = {
  girlfriend: '#FF6B81',
  boyfriend: '#2E86DE',
  best_friend: '#FF9F43',
  friend: '#FF9F43',
}

export function getPersonaColor(agentType, agentKey) {
  const raw = (agentType || agentKey || '').toLowerCase().replace(/[\s-]+/g, '_')
  if (raw.includes('girlfriend') || raw.includes('girl')) return '#FF6B81'
  if (raw.includes('boyfriend') || raw.includes('boy')) return '#2E86DE'
  if (raw.includes('friend')) return '#FF9F43'
  return PERSONA_MAP[raw] || '#6366f1'
}

export function getPersonaTextColor(agentType, agentKey) {
  const color = getPersonaColor(agentType, agentKey)
  return color === '#FF9F43' ? '#92400e' : '#fff'
}
