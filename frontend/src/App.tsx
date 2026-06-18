import { Activity } from 'lucide-react';
import { useMonitors } from './hooks/useMonitors';
import { useWebSocket } from './hooks/useWebSocket';
import { MonitorCard } from './components/MonitorCard';
import { IncidentList } from './components/IncidentList';

function App() {
  const { monitors, setMonitors, incidents, loading } = useMonitors();

  // Connect to websocket to receive live status updates
  const connected = useWebSocket('/ws/status', (eventData) => {
    // If it's a bulk initial state (dict of monitors)
    if (!eventData.monitor_id && typeof eventData === 'object') {
      setMonitors(current => 
        current.map(m => {
          const liveData = eventData[m.id];
          return liveData ? { ...m, ...liveData } : m;
        })
      );
    } 
    // If it's a single update from pub/sub
    else if (eventData.monitor_id) {
      setMonitors(current => 
        current.map(m => 
          m.id === eventData.monitor_id 
            ? { ...m, ...eventData } 
            : m
        )
      );
    }
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center space-y-4">
        <Activity className="text-indigo-500 animate-pulse" size={48} />
        <p className="text-slate-400 font-medium tracking-widest uppercase">Loading Pulse...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 selection:bg-indigo-500/30">
      <header className="sticky top-0 z-10 bg-slate-950/80 backdrop-blur-md border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-indigo-500/10 p-1.5 rounded-lg border border-indigo-500/20">
              <Activity className="text-indigo-500" size={24} />
            </div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">Pulse</h1>
          </div>
          
          <div className="flex items-center gap-3 text-sm font-medium">
            <span className="relative flex h-3 w-3">
              {connected && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
              <span className={`relative inline-flex rounded-full h-3 w-3 ${connected ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
            </span>
            <span className={connected ? 'text-emerald-400' : 'text-rose-400'}>
              {connected ? 'LIVE' : 'DISCONNECTED'}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-10 space-y-12">
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">Services Overview</h2>
            <span className="text-sm font-medium text-slate-400 bg-slate-800/50 px-3 py-1 rounded-full border border-slate-800">
              {monitors.length} Monitors
            </span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {monitors.map(monitor => (
              <MonitorCard key={monitor.id} monitor={monitor} />
            ))}
          </div>
        </section>

        <section>
          <IncidentList incidents={incidents} />
        </section>
      </main>
    </div>
  );
}

export default App;
