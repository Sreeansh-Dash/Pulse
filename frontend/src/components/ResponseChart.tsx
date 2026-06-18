import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import type { CheckResult } from '../types';

interface ResponseChartProps {
  monitorId: string;
}

export function ResponseChart({ monitorId }: ResponseChartProps) {
  const [data, setData] = useState<CheckResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/monitors/${monitorId}/results?hours=24`)
      .then(r => r.json())
      .then(res => {
        // Format for recharts
        const formatted = res.map((r: CheckResult) => ({
          ...r,
          time: new Date(r.checked_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }));
        setData(formatted);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [monitorId]);

  if (loading) {
    return <div className="w-full h-full bg-slate-800/30 animate-pulse rounded flex items-center justify-center text-xs text-slate-500">Loading chart...</div>;
  }

  if (data.length === 0) {
    return <div className="w-full h-full border border-dashed border-slate-700 rounded flex items-center justify-center text-xs text-slate-500">No data yet</div>;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data}>
        <XAxis dataKey="time" hide />
        <YAxis hide domain={['auto', 'auto']} />
        <Tooltip 
          contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
          itemStyle={{ color: '#818cf8' }}
          labelStyle={{ color: '#94a3b8' }}
          formatter={(value: any) => [`${Math.round(Number(value))} ms`, 'Response Time']}
        />
        <Line 
          type="monotone" 
          dataKey="response_time_ms" 
          stroke="#6366f1" 
          strokeWidth={2} 
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
