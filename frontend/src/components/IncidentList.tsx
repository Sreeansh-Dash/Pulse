import type { Incident } from '../types';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

interface IncidentListProps {
  incidents: Incident[];
}

export function IncidentList({ incidents }: IncidentListProps) {
  if (incidents.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center">
        <CheckCircle2 className="mx-auto text-emerald-500 mb-3" size={32} />
        <h3 className="text-lg font-medium text-slate-200">No recent incidents</h3>
        <p className="text-slate-500 mt-1">All monitored services are operating normally.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
      <div className="px-6 py-4 border-b border-slate-800 flex items-center gap-2">
        <AlertCircle className="text-rose-500" size={18} />
        <h3 className="text-lg font-semibold text-white">Recent Incidents</h3>
      </div>
      <div className="divide-y divide-slate-800/50">
        {incidents.map(incident => {
          const isResolved = !!incident.resolved_at;
          const startedAt = new Date(incident.started_at);
          const resolvedAt = incident.resolved_at ? new Date(incident.resolved_at) : null;
          
          let duration = "Ongoing";
          if (resolvedAt) {
            const diffMins = Math.round((resolvedAt.getTime() - startedAt.getTime()) / 60000);
            duration = diffMins < 60 ? `${diffMins} mins` : `${Math.round(diffMins / 60)} hrs ${diffMins % 60} mins`;
          }

          return (
            <div key={incident.id} className="px-6 py-4 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 hover:bg-slate-800/20 transition-colors">
              <div>
                <h4 className="text-slate-200 font-medium flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${isResolved ? 'bg-emerald-500' : 'bg-rose-500 animate-pulse'}`}></span>
                  {incident.monitor_name}
                </h4>
                <div className="text-sm text-slate-500 mt-1">
                  Started: {startedAt.toLocaleString()}
                </div>
              </div>
              <div className="flex flex-col sm:items-end">
                <span className={`px-2 py-1 text-xs font-bold rounded-full border ${
                  isResolved 
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                    : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                }`}>
                  {isResolved ? 'RESOLVED' : 'ACTIVE'}
                </span>
                <span className="text-xs text-slate-500 mt-2 font-medium">
                  Downtime: {duration}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
