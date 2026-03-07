function RegionCards({ regions }) {
  const riskStyles = {
    high: 'border-red-500/50 bg-red-500/10',
    medium: 'border-amber-500/50 bg-amber-500/10',
    low: 'border-emerald-500/50 bg-emerald-500/10',
  };

  const scoreColors = {
    high: 'text-red-400',
    medium: 'text-amber-400',
    low: 'text-emerald-400',
  };

  return (
    <div className="rounded-xl border border-grid-border bg-grid-card p-6">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
        Outage Risk by Region
      </h3>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {regions.map((r) => (
          <div
            key={r.id}
            className={`rounded-lg border p-4 ${riskStyles[r.risk]}`}
          >
            <p className="text-xs font-medium text-slate-500 uppercase">{r.abbreviation}</p>
            <p className="mt-1 font-semibold text-slate-200">{r.name}</p>
            <p className={`mt-2 font-mono text-2xl font-bold ${scoreColors[r.risk]}`}>
              {r.score}
            </p>
            <p className="text-xs text-slate-500 capitalize">{r.risk} risk</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default RegionCards;
