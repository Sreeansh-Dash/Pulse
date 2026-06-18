interface StatusBadgeProps {
  status?: "up" | "down";
}

export function StatusBadge({ status }: StatusBadgeProps) {
  if (!status) {
    return <span className="px-2 py-1 bg-slate-800 text-slate-400 text-xs font-bold rounded-full">PENDING</span>;
  }

  const isUp = status === "up";
  
  return (
    <div className={`flex items-center px-2 py-1 rounded-full text-xs font-bold ${
      isUp ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 
             'bg-rose-500/10 text-rose-400 border border-rose-500/20'
    }`}>
      {!isUp && (
        <span className="relative flex h-2 w-2 mr-1.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
        </span>
      )}
      {isUp && (
        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500 mr-1.5"></span>
      )}
      {status.toUpperCase()}
    </div>
  );
}
