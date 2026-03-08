import React from "react";

function calculateAverage(arr) {
  if (!arr || arr.length === 0) return 0;
  return arr.reduce((sum, val) => sum + val, 0) / arr.length;
}

function clampScore(val) {
  return Math.max(0, Math.min(100, Math.round(val)));
}

function calculateOutageForecast({
  currentStressScore,
  historicalStressScores,
  disasterSeverity,
  incidentSeverity,
}) {
  const avg = calculateAverage(historicalStressScores);
  const trend = currentStressScore - avg;

  // Reduced multipliers for more realistic risk
  const risk1Hour = clampScore(
    currentStressScore + trend * 0.2 + disasterSeverity * 5 + incidentSeverity * 3
  );
  const risk3Hour = clampScore(
    currentStressScore + trend * 0.5 + disasterSeverity * 7 + incidentSeverity * 5
  );
  const risk24Hour = clampScore(
    currentStressScore + trend * 0.8 + disasterSeverity * 10 + incidentSeverity * 7
  );

  return {
    current: clampScore(currentStressScore),
    average: Math.round(avg),
    forecast: {
      oneHour: risk1Hour,
      threeHour: risk3Hour,
      twentyFourHour: risk24Hour,
    },
  };
}


function getRiskColor(score) {
  if (score >= 70) return 'text-red-400';
  if (score >= 40) return 'text-amber-400';
  return 'text-emerald-400';
}

function getRiskBg(score) {
  if (score >= 70) return 'border-red-500/50 bg-red-500/10';
  if (score >= 40) return 'border-amber-500/50 bg-amber-500/10';
  return 'border-emerald-500/50 bg-emerald-500/10';
}

export default function OutageForecast({
  currentStressScore = 0,
  historicalStressScores = [],
  disasterSeverity = 0,
  incidentSeverity = 0,
  region = "Unknown",
}) {
  const result = calculateOutageForecast({
    currentStressScore,
    historicalStressScores,
    disasterSeverity,
    incidentSeverity,
  });

  return (
    <div className={`rounded-xl border border-grid-border bg-grid-card p-6 mt-6`}>
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-2">
        Outage Risk Forecast
      </h3>
      <div className="mb-4">
        <div className="text-slate-400 text-xs uppercase">Region</div>
        <div className="text-slate-200 font-semibold mb-1">{region}</div>
        <div className="flex gap-6">
          <div>
            <div className="text-slate-400 text-xs uppercase">Current Stress Score</div>
            <div className={`font-mono text-2xl font-bold ${getRiskColor(result.current)}`}>{result.current}</div>
          </div>
          <div>
            <div className="text-slate-400 text-xs uppercase">Historical Average</div>
            <div className="font-mono text-2xl font-bold text-slate-300">{result.average}</div>
          </div>
        </div>
      </div>
      <table className="w-full text-left border-collapse mt-2">
        <thead>
          <tr className="border-b border-slate-700">
            <th className="py-2 px-3 text-slate-400 text-xs uppercase">Forecast</th>
            <th className="py-2 px-3 text-slate-400 text-xs uppercase">Risk Score</th>
          </tr>
        </thead>
        <tbody>
          <tr className={getRiskBg(result.forecast.oneHour)}>
            <td className="py-2 px-3">1 Hour</td>
            <td className={`py-2 px-3 font-mono font-bold ${getRiskColor(result.forecast.oneHour)}`}>{result.forecast.oneHour}</td>
          </tr>
          <tr className={getRiskBg(result.forecast.threeHour)}>
            <td className="py-2 px-3">3 Hours</td>
            <td className={`py-2 px-3 font-mono font-bold ${getRiskColor(result.forecast.threeHour)}`}>{result.forecast.threeHour}</td>
          </tr>
          <tr className={getRiskBg(result.forecast.twentyFourHour)}>
            <td className="py-2 px-3">24 Hours</td>
            <td className={`py-2 px-3 font-mono font-bold ${getRiskColor(result.forecast.twentyFourHour)}`}>{result.forecast.twentyFourHour}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
