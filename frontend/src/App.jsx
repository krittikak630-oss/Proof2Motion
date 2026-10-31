import { useEffect, useRef, useState } from 'react'
import { DEMO, DEMO_VERIFICATION } from './demo.js'
import { fetchSample, streamAnalyze, validateFiles } from './api.js'

const STATUS = {
  supported: 'Supported by your files',
  partial: 'Only partly supported',
  unsupported: 'Not supported by the evidence',
}

function clampSeconds(value) {
  return Math.min(Math.max(Number(value) || 5, 3), 8)
}

function Storyboard({ scenes }) {
  const [index, setIndex] = useState(0)
  const [playing, setPlaying] = useState(false)

  useEffect(() => {
    if (!playing) return undefined
    const timer = setTimeout(() => {
      if (index >= scenes.length - 1) setPlaying(false)
      else setIndex(index + 1)
    }, clampSeconds(scenes[index]?.duration_sec) * 1000)
    return () => clearTimeout(timer)
  }, [playing, index, scenes])

  const scene = scenes[index]
  if (!scene) return null
  const stop = (next) => { setPlaying(false); setIndex(next) }

  return (
    <section className="block" aria-label="Storyboard">
      <h2>Storyboard</h2>
      <div className="player">
        <div className="frame" key={index}>
          <p className="frame-text">{scene.on_screen_text || scene.title}</p>
          <p className="frame-visual">{scene.visual}</p>
        </div>
        <div className="narration" aria-live="polite">
          <h3>{scene.title}</h3>
          <p>{scene.narration}</p>
        </div>
        <div className="bar">
          <span
            key={`${index}-${playing}`}
            className={playing ? 'bar-fill running' : 'bar-fill'}
            style={{ animationDuration: `${clampSeconds(scene.duration_sec)}s` }}
          />
        </div>
        <div className="controls">
          <button onClick={() => { if (!playing && index >= scenes.length - 1) setIndex(0); setPlaying(!playing) }}>
            {playing ? 'Pause' : 'Play storyboard'}
          </button>
          <button className="ghost" onClick={() => stop(Math.max(0, index - 1))}>Previous</button>
          <button className="ghost" onClick={() => stop(Math.min(scenes.length - 1, index + 1))}>Next</button>
        </div>
      </div>
      <ol className="strip">
        {scenes.map((s, i) => (
          <li key={i}>
            <button className={i === index ? 'cell active' : 'cell'} onClick={() => stop(i)} aria-current={i === index}>
              <span className="cell-num">Scene {i + 1}</span>
              <span className="cell-title">{s.title}</span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  )
}

function Results({ data }) {
  const { analysis, model, files, verification } = data

  function download() {
    const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'proof2motion-analysis.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="results">
      <header className="case">
        <h2>{analysis.title}</h2>
        <p className="meta">Read {files.join(', ')} with {model}</p>
        <p>{analysis.summary}</p>
        {verification?.total > 0 && (
          <p className={verification.verified === verification.total ? 'trust ok' : 'trust warn'}>
            {verification.verified} of {verification.total} quotes found word for word in your files
          </p>
        )}
      </header>

      <section className="block">
        <h2>Claims and proof</h2>
        {analysis.claims.map((c, i) => (
          <article className={`claim ${c.status}`} key={i}>
            <p className="claim-text">{c.claim}</p>
            <p className="badge">{STATUS[c.status]}</p>
            {c.note && <p className="note">{c.note}</p>}
            {c.support.map((s, j) => (
              <blockquote key={j}>
                <mark>{s.quote}</mark>
                <cite>
                  {s.file}{s.page ? `, page ${s.page}` : ''}
                  <span className={s.verified ? 'check ok' : 'check bad'}>
                    {s.verified ? 'Quote found in file' : 'Quote not found in your files'}
                  </span>
                </cite>
              </blockquote>
            ))}
          </article>
        ))}
      </section>

      {analysis.gaps.length > 0 && (
        <section className="block">
          <h2>What is missing</h2>
          <ul className="gaps">{analysis.gaps.map((g, i) => <li key={i}>{g}</li>)}</ul>
        </section>
      )}

      <Storyboard scenes={analysis.storyboard} />
      <button className="ghost" onClick={download}>Download analysis as JSON</button>
    </div>
  )
}

function Progress({ stage, chars }) {
  const order = ['uploading', 'analyzing', 'retrying', 'verifying']
  const at = order.indexOf(stage)
  const done = (n) => at > n
  return (
    <div className="progress" role="status" aria-live="polite">
      <div className="reel"><i /><i /><i /><i /><i /></div>
      <ul>
        <li className={done(0) ? 'done' : 'now'}>{done(0) ? 'Files received' : 'Uploading your files'}</li>
        <li className={done(1) ? 'done' : at === 1 || at === 2 ? 'now' : ''}>
          Gemma 4 is analysing{chars > 0 ? ` (${chars.toLocaleString()} characters written)` : ''}
          {stage === 'retrying' ? ' - retrying once' : ''}
        </li>
        <li className={at === 3 ? 'now' : ''}>Checking every quote against your files</li>
      </ul>
    </div>
  )
}

export default function App() {
  const [files, setFiles] = useState([])
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [stage, setStage] = useState('idle')
  const [chars, setChars] = useState(0)
  const [drag, setDrag] = useState(false)
  const busy = stage !== 'idle'
  const resultRef = useRef(null)

  useEffect(() => {
    if (data) resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [data])

  function addFiles(list) {
    const chosen = [...list]
    setError(validateFiles(chosen))
    setFiles(chosen)
  }

  async function analyze() {
    setStage('uploading'); setError(''); setData(null); setChars(0)
    try {
      await streamAnalyze(files, (event, payload) => {
        if (event === 'stage') setStage(payload.stage)
        else if (event === 'progress') setChars(payload.chars)
        else if (event === 'result') setData(payload)
        else if (event === 'error') throw new Error(payload.detail)
      })
    } catch (e) {
      setError(e.message)
    }
    setStage('idle')
  }

  async function useSample() {
    try { addFiles([await fetchSample()]) } catch (e) { setError(e.message) }
  }

  function showDemo() {
    setError('')
    setData({ analysis: DEMO, model: 'built-in demo data', files: ['sample_evidence.txt'], verification: DEMO_VERIFICATION })
  }

  return (
    <main>
      <header className="hero">
        <p className="brand">Proof2Motion</p>
        <h1>Evidence in. A film plan out.</h1>
        <p className="lede">
          Upload documents. Proof2Motion shows which claims they actually prove, what is missing, and turns the
          story into a five-scene storyboard you can play. Every quote is checked against your files.
        </p>
        <ol className="steps">
          <li><b>1</b> Add your files</li>
          <li><b>2</b> Check claims against quotes</li>
          <li><b>3</b> Play the storyboard</li>
        </ol>
      </header>

      <section
        className={drag ? 'drop over' : 'drop'}
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); addFiles(e.dataTransfer.files) }}
      >
        <p>Drag TXT, MD or PDF files here (up to 5 files, 5 MB each), or</p>
        <label className="pick">
          Choose files
          <input type="file" multiple accept=".txt,.md,.pdf" onChange={(e) => addFiles(e.target.files)} disabled={busy} />
        </label>
        <button className="ghost" onClick={useSample} disabled={busy}>Use the sample water-complaint file</button>
        <button className="ghost" onClick={showDemo} disabled={busy}>See a demo result (no API key needed)</button>
        {files.length > 0 && <p className="chosen">Ready: {files.map((f) => f.name).join(', ')}</p>}
      </section>

      <div className="actions">
        <button onClick={analyze} disabled={!files.length || busy || Boolean(validateFiles(files))}>
          {busy ? 'Working…' : 'Analyze evidence'}
        </button>
      </div>

      {busy && <Progress stage={stage} chars={chars} />}
      {error && (
        <div className="error" role="alert">
          <p>{error}</p>
          <button className="ghost" onClick={showDemo}>Show the demo result instead</button>
        </div>
      )}
      <div ref={resultRef}>{data && <Results data={data} />}</div>

      <footer>
        <p>
          Analysis by Gemma 4, an open-weights model. Check important findings against your original documents.
          Files are processed in memory and are not stored.
        </p>
      </footer>
    </main>
  )
}
