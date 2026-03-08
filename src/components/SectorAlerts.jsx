function SectorAlerts({ alerts }) {
  const priorityStyles = {
    high: 'border-l-4 border-l-red-500 bg-red-500/10 shadow-md',
    medium: 'border-l-4 border-l-amber-500 bg-amber-500/10 shadow-md',
    low: 'border-l-4 border-l-emerald-500 bg-emerald-500/10 shadow-md',
  };

  return (
    <div className="rounded-3xl border border-grid-border bg-grid-card p-6 shadow-xl">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
        Sector Alerts
      </h3>
      <p className="mt-1 text-xs text-slate-500">
        Elevated outage risk in priority U.S. regions within the next 2 hours
      </p>
      <ul className="mt-4 space-y-4">
        {alerts.map((a, i) => (
          <li
            key={i}
            className={`rounded-2xl p-4 ${priorityStyles[a.priority]}`}
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-200">{a.sector}</span>
              <span className="text-xs text-slate-500">{a.region}</span>
            </div>
            <p className="mt-2 text-sm text-slate-400">{a.recommendation}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default SectorAlerts;
