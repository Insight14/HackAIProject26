import { useState } from 'react'

function IncidentInput({ onAnalyze, loading }) {
  const [text, setText] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (text.trim().length >= 5) {
      onAnalyze(text.trim())
      setText('')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border border-grid-border bg-grid-card p-4">
      <label className="block text-sm font-medium text-slate-400">
        Analyze incident with NLP (min 5 chars)
      </label>
      <div className="mt-2 flex gap-2">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. Transmission line failure due to severe storm in North Texas"
          className="flex-1 rounded-lg border border-grid-border bg-slate-800/50 px-4 py-2 text-slate-200 placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
          minLength={5}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || text.trim().length < 5}
          className="rounded-lg bg-cyan-600 px-4 py-2 font-medium text-white hover:bg-cyan-500 disabled:opacity-50"
        >
          {loading ? 'Analyzing…' : 'Analyze'}
        </button>
      </div>
    </form>
  )
}

export default IncidentInput
