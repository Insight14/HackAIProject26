function SectorAlerts({ alerts }) {
  const priorityStyles = {
    high: 'border-l-red-500',
    medium: 'border-l-amber-500',
    low: 'border-l-emerald-500',
  };

  return (
    <div className="rounded-xl border border-grid-border bg-grid-card p-6">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
        Sector Alerts
      </h3>
      <p className="mt-1 text-xs text-slate-500">
        Elevated outage risk in priority U.S. regions within the next 2 hours
      </p>
      <ul className="mt-4 space-y-3">
        {alerts.map((a, i) => (
          <li
            key={i}
            className={`rounded-r-lg border-l-4 bg-slate-800/30 p-4 ${priorityStyles[a.priority]}`}
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
