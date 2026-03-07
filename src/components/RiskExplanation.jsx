function RiskExplanation({ factors }) {
  const severityColors = {
    high: 'bg-red-500/20 text-red-400 border-red-500/30',
    medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    low: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  };

  return (
    <div className="rounded-xl border border-grid-border bg-grid-card p-6">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
        Why the risk is high
      </h3>
      <p className="mt-1 text-xs text-slate-500">
        Contributing factors to current grid stress score
      </p>
      <ul className="mt-4 space-y-3">
        {factors.map((f, i) => (
          <li key={i} className="flex items-center justify-between gap-4">
            <span className="text-slate-300">{f.factor}</span>
            <div className="flex items-center gap-2">
              <span className="text-sm font-mono text-cyan-400">{f.contribution}%</span>
              <span
                className={`rounded px-2 py-0.5 text-xs font-medium border ${severityColors[f.severity]}`}
              >
                {f.severity}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default RiskExplanation;
