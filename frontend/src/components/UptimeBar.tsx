import { useEffect, useState } from 'react';
import { getApiUrl } from '../utils/api';

interface UptimeBarProps {
  monitorId: string;
}

export function UptimeBar({ monitorId }: UptimeBarProps) {
  const [uptimes, setUptimes] = useState<Record<string, number>>({ "24h": 100, "7d": 100, "30d": 100 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(getApiUrl(`/api/monitors/${monitorId}/uptime`))
      .then(r => r.json())
      .then(data => {
        setUptimes(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [monitorId]);

  if (loading) return <div className="h-4 bg-slate-800 animate-pulse rounded"></div>;

  return (
    <div className="flex gap-2 text-xs">
      {["24h", "7d", "30d"].map(period => {
        const value = uptimes[period] || 0;
        let colorClass = "text-emerald-400";
        if (value < 95) colorClass = "text-rose-400";
        else if (value < 99.5) colorClass = "text-amber-400";

        return (
          <div key={period} className="flex flex-col flex-1 bg-slate-800/50 p-1.5 rounded text-center">
            <span className="text-slate-500 text-[10px] uppercase">{period}</span>
            <span className={`font-semibold ${colorClass}`}>
              {value === 100 ? "100" : value.toFixed(2)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}
