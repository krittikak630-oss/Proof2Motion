// Talks to the FastAPI backend. Same-origin by default; set VITE_API_URL only if hosted separately.
const API = import.meta.env.VITE_API_URL || ''

export const LIMITS = { files: 5, bytes: 5 * 1024 * 1024, types: ['.txt', '.md', '.pdf'] }

export function validateFiles(files) {
  if (files.length > LIMITS.files) return `Choose at most ${LIMITS.files} files.`
  for (const f of files) {
    const ext = f.name.slice(f.name.lastIndexOf('.')).toLowerCase()
    if (!LIMITS.types.includes(ext)) return `"${f.name}" is not a TXT, MD or PDF file.`
    if (f.size > LIMITS.bytes) return `"${f.name}" is larger than 5 MB.`
    if (f.size === 0) return `"${f.name}" is empty.`
  }
  return ''
}

export async function fetchSample() {
  const res = await fetch(`${API}/api/sample`)
  if (!res.ok) throw new Error('Could not load the sample file. Is the backend running?')
  const json = await res.json()
  return new File([json.text], json.filename, { type: 'text/plain' })
}

function parseBlock(block) {
  let event = 'message'
  let data = ''
  for (const line of block.split('\n')) {
    if (line.startsWith('event: ')) event = line.slice(7)
    else if (line.startsWith('data: ')) data += line.slice(6)
  }
  return { event, data: data ? JSON.parse(data) : {} }
}

// Streams analysis events (stage / progress / result / error) from the backend as they happen.
export async function streamAnalyze(files, onEvent) {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  let res
  try {
    res = await fetch(`${API}/api/analyze/stream`, { method: 'POST', body: form })
  } catch {
    throw new Error('Cannot reach the server. Start the backend and try again.')
  }
  if (!res.ok) {
    const json = await res.json().catch(() => ({}))
    throw new Error(json.detail || `Server error ${res.status}`)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let end
    while ((end = buffer.indexOf('\n\n')) !== -1) {
      const block = buffer.slice(0, end)
      buffer = buffer.slice(end + 2)
      if (block.trim()) {
        const { event, data } = parseBlock(block)
        onEvent(event, data)
      }
    }
  }
}
