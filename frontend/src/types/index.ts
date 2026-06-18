export interface Monitor {
  id: string;
  name: string;
  url: string;
  check_interval_seconds: number;
  created_at: string;
  status?: "up" | "down";
  response_time_ms?: number;
  status_code?: number;
  last_checked?: string;
  consecutive_failures?: number;
}

export interface CheckResult {
  checked_at: string;
  response_time_ms: number;
  status: "up" | "down";
}

export interface Incident {
  id: string;
  monitor_id: string;
  monitor_name: string;
  started_at: string;
  resolved_at: string | null;
}
