import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

function StressChart({ data }) {
  return (
    <div className="rounded-xl border border-grid-border bg-grid-card p-6">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
        Grid Stress Score Over Time
      </h3>
      <p className="mt-1 text-xs text-slate-500">Last 12 hours — United States</p>
      <div className="mt-4 h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="stressGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.4} />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="time"
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
            />
            <YAxis
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              domain={[0, 100]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#94a3b8' }}
              formatter={(value) => [`${value}`, 'Stress Score']}
            />
            <Area
              type="monotone"
              dataKey="score"
              stroke="#06b6d4"
              strokeWidth={2}
              fill="url(#stressGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default StressChart;
