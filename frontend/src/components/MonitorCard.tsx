import type { Monitor } from '../types';
import { Activity, Clock } from 'lucide-react';
import { StatusBadge } from './StatusBadge.tsx';
import { UptimeBar } from './UptimeBar.tsx';
import { ResponseChart } from './ResponseChart.tsx';

interface MonitorCardProps {
  monitor: Monitor;
}

export function MonitorCard({ monitor }: MonitorCardProps) {
  
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col space-y-4 hover:border-slate-700 transition-colors">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-lg font-semibold text-white truncate max-w-[200px]" title={monitor.name}>
            {monitor.name}
          </h3>
          <a 
            href={monitor.url} 
            target="_blank" 
            rel="noreferrer" 
            className="text-xs text-slate-400 hover:text-indigo-400 transition-colors truncate max-w-[200px] block"
          >
            {monitor.url}
          </a>
        </div>
        <StatusBadge status={monitor.status} />
      </div>
      
      <div className="grid grid-cols-2 gap-4 py-2 border-y border-slate-800">
        <div className="flex flex-col">
          <span className="text-xs text-slate-500 uppercase tracking-wider flex items-center gap-1">
            <Activity size={12} /> Response
          </span>
          <span className="text-lg font-medium text-slate-200">
            {monitor.response_time_ms ? `${Math.round(monitor.response_time_ms)} ms` : '--'}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-slate-500 uppercase tracking-wider flex items-center gap-1">
            <Clock size={12} /> Checked
          </span>
          <span className="text-sm font-medium text-slate-300 mt-1">
            {monitor.last_checked ? new Date(monitor.last_checked).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'Never'}
          </span>
        </div>
      </div>
      
      <div className="h-24">
        <ResponseChart monitorId={monitor.id} />
      </div>
      
      <div>
        <UptimeBar monitorId={monitor.id} />
      </div>
    </div>
  );
}
