import { useState, useEffect } from 'react';
import type { Monitor, Incident } from '../types';

export function useMonitors() {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [monitorsRes, incidentsRes] = await Promise.all([
          fetch('/api/monitors'),
          fetch('/api/incidents')
        ]);
        
        if (monitorsRes.ok) {
          setMonitors(await monitorsRes.json());
        }
        if (incidentsRes.ok) {
          setIncidents(await incidentsRes.json());
        }
      } catch (e) {
        console.error('Failed to fetch initial data', e);
      } finally {
        setLoading(false);
      }
    };
    
    fetchInitialData();
  }, []);

  return { monitors, setMonitors, incidents, loading };
}
