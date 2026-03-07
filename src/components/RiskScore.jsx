function RiskScore({ score = 78, label = 'Current Risk Score' }) {
  const getColor = (s) => {
    if (s >= 70) return 'text-red-400';
    if (s >= 40) return 'text-amber-400';
    return 'text-emerald-400';
  };

  const getBgColor = (s) => {
    if (s >= 70) return 'from-red-500/20 to-red-600/5';
    if (s >= 40) return 'from-amber-500/20 to-amber-600/5';
    return 'from-emerald-500/20 to-emerald-600/5';
  };

  return (
    <div className={`rounded-xl border border-grid-border bg-gradient-to-br ${getBgColor(score)} p-6`}>
      <p className="text-sm font-medium text-slate-400 uppercase tracking-wider">{label}</p>
      <p className={`mt-2 font-mono text-5xl font-bold ${getColor(score)}`}>{score}</p>
      <p className="mt-1 text-sm text-slate-500">out of 100</p>
    </div>
  );
}

export default RiskScore;
