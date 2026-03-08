function IncidentFeed({ incidents }) {
  const severityStyles = {
    critical: 'bg-red-500/20 text-red-400',
    high: 'bg-red-500/20 text-red-400',
    medium: 'bg-amber-500/20 text-amber-400',
    low: 'bg-emerald-500/20 text-emerald-400',
  };

  const formatTime = (ts) => {
    const d = new Date(ts);
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="h-[22rem] rounded-xl border border-grid-border bg-grid-card p-6">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
        Recent Incident Reports
      </h3>
      <p className="mt-1 text-xs text-slate-500">Blended from outage telemetry, NLP inputs, and NOAA/FIRMS disaster feeds</p>
      <ul className="mt-4 h-64 space-y-4 overflow-y-auto">
        {incidents.map((inc) => (
          <li key={inc.id} className="border-b border-grid-border pb-4 last:border-0 last:pb-0">
            <div className="flex items-start justify-between gap-2">
              <span className="text-xs font-mono text-slate-500">{formatTime(inc.timestamp)}</span>
              <span className={`rounded px-2 py-0.5 text-xs font-medium ${severityStyles[inc.severity] ?? severityStyles.medium}`}>
                {inc.severity}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-300">{inc.text}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className="rounded bg-slate-700/50 px-2 py-0.5 text-xs text-slate-400">
                {inc.eventType}
              </span>
              <span className="rounded bg-slate-700/50 px-2 py-0.5 text-xs text-slate-400">
                {inc.region}
              </span>
              <span className="rounded bg-slate-700/50 px-2 py-0.5 text-xs text-slate-400">
                cause: {inc.cause}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default IncidentFeed;
