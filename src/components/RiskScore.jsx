function RiskScore({ score = 78, label = 'Current Risk Score' }) {
  const getStrokeColor = (s) => {
    if (s >= 70) return '#f87171'; // red-400
    if (s >= 40) return '#fbbf24'; // amber-400
    return '#34d399'; // emerald-400
  };

  const getBgColor = (s) => {
    if (s >= 70) return 'from-red-500/20 to-red-600/5';
    if (s >= 40) return 'from-amber-500/20 to-amber-600/5';
    return 'from-emerald-500/20 to-emerald-600/5';
  };

  const getTextColor = (s) => {
    if (s >= 70) return 'text-red-400';
    if (s >= 40) return 'text-amber-400';
    return 'text-emerald-400';
  };

  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className={`rounded-xl border border-grid-border bg-gradient-to-br ${getBgColor(score)} p-6`}>
      <p className="text-sm font-medium text-slate-400 uppercase tracking-wider">{label}</p>
      <div className="mt-4 flex items-center justify-center">
        <div className="relative">
          <svg className="h-36 w-36 -rotate-90" viewBox="0 0 120 120">
            {/* Background circle */}
            <circle
              cx="60"
              cy="60"
              r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth="10"
              className="text-slate-700"
            />
            {/* Progress circle */}
            <circle
              cx="60"
              cy="60"
              r={radius}
              fill="none"
              stroke={getStrokeColor(score)}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-500 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`font-mono text-3xl font-bold ${getTextColor(score)}`}>{score}</span>
            <span className="text-xs text-slate-500">out of 100</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RiskScore;
