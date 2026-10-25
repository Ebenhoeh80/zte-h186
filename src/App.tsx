import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  ArrowDownCircle,
  ArrowUpCircle,
  CheckCircle2,
  Clock,
  Code2,
  Copy,
  Download,
  ExternalLink,
  FileCode,
  Gauge,
  HelpCircle,
  Layers,
  Network,
  Play,
  RefreshCw,
  Server,
  Settings,
  Shield,
  Sliders,
  Terminal,
  Wifi,
  XCircle,
  AlertTriangle
} from 'lucide-react';
import { DslNormalizedData, ModemStatsResponse, ProtocolStepResult } from './types/modem';

interface HacsFile {
  path: string;
  description: string;
  content: string;
  size: number;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'entities' | 'hacs' | 'config_flow' | 'protocol' | 'raw'>('dashboard');
  const [stats, setStats] = useState<ModemStatsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Settings & Demo State
  const [demoMode, setDemoMode] = useState<boolean>(true);
  const [preset, setPreset] = useState<'vdsl100' | 'supervectoring250' | 'degraded' | 'errorSpike'>('vdsl100');
  const [host, setHost] = useState<string>('192.168.1.1');
  const [username, setUsername] = useState<string>('admin');
  const [password, setPassword] = useState<string>('');
  const [autoPoll, setAutoPoll] = useState<boolean>(true);
  const [pollInterval, setPollInterval] = useState<number>(10);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // HACS Files state
  const [hacsFiles, setHacsFiles] = useState<HacsFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('custom_components/zte_h186/sensor.py');

  // Protocol steps
  const [protocolSteps, setProtocolSteps] = useState<ProtocolStepResult[]>([]);
  const [testingProtocol, setTestingProtocol] = useState<boolean>(false);

  // Fetch modem stats
  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/modem/stats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          host,
          username,
          password,
          simulate: demoMode,
          preset,
        }),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        setStats(data);
        setError(null);
      } else {
        setError(data.error_message || 'Verbindung zum Modem fehlgeschlagen.');
      }
    } catch (err: any) {
      setError(err?.message || 'Netzwerkfehler');
    } finally {
      setLoading(false);
    }
  }, [host, username, password, demoMode, preset]);

  // Load HACS files
  useEffect(() => {
    fetch('/api/hacs/files')
      .then((res) => res.json())
      .then((data) => {
        if (data.files) {
          setHacsFiles(data.files);
        }
      })
      .catch(console.error);
  }, []);

  // Polling loop
  useEffect(() => {
    fetchStats();
    if (!autoPoll) return;
    const interval = setInterval(fetchStats, pollInterval * 1000);
    return () => clearInterval(interval);
  }, [fetchStats, autoPoll, pollInterval]);

  // Run protocol test
  const runProtocolTest = async () => {
    setTestingProtocol(true);
    try {
      const res = await fetch('/api/modem/test-protocol', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host, username, password, simulate: demoMode }),
      });
      const data = await res.json();
      setProtocolSteps(data.steps || []);
    } catch {
      // fallback
    } finally {
      setTestingProtocol(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(id);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const formatShowtime = (seconds?: number) => {
    if (!seconds) return '0s';
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${d > 0 ? `${d}d ` : ''}${h}h ${m}m ${s}s`;
  };

  const dsl = (stats?.data as DslNormalizedData) || null;

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <Network className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight text-white">ZTE H186</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 font-medium">
                  HACS Component &amp; Monitor
                </span>
              </div>
              <p className="text-xs text-slate-400">Home Assistant Integration &amp; DSL Diagnostics</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Live Indicator */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs">
              <span className={`w-2 h-2 rounded-full ${demoMode ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400 animate-ping'}`} />
              <span className="text-slate-300 font-medium">
                {demoMode ? `Simulationsmodus (${preset})` : `Modem: ${host}`}
              </span>
            </div>

            {/* Quick Demo Switcher */}
            <button
              onClick={() => {
                setDemoMode(!demoMode);
                setTimeout(fetchStats, 50);
              }}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition flex items-center gap-1.5 ${
                demoMode
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/20'
                  : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              {demoMode ? 'Demo Aktiv' : 'Echte IP'}
            </button>

            {/* Download Release ZIP */}
            <a
              href="/api/download/release-zip"
              download="zte-h186-v1.0.0.zip"
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center gap-1.5 shadow-md shadow-emerald-600/20"
              title="Release-Paket (v1.0.0.zip) herunterladen"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Release ZIP (v1.0.0)</span>
            </a>

            {/* Refresh Button */}
            <button
              onClick={fetchStats}
              disabled={loading}
              className="p-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition disabled:opacity-50 shadow-md shadow-sky-600/20"
              title="Daten jetzt aktualisieren"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-1 overflow-x-auto text-sm border-t border-slate-800/60">
          {[
            { id: 'dashboard', label: 'DSL Dashboard', icon: Gauge },
            { id: 'entities', label: 'HA Entitäten (26 Sensoren)', icon: Layers },
            { id: 'hacs', label: 'HACS Repository Code', icon: FileCode },
            { id: 'config_flow', label: 'Config Flow UI', icon: Sliders },
            { id: 'protocol', label: 'Protokoll Inspector', icon: Terminal },
            { id: 'raw', label: 'Rohdaten & Export', icon: Code2 },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 py-3 px-3.5 font-medium border-b-2 transition whitespace-nowrap ${
                  isActive
                    ? 'border-sky-500 text-sky-400 bg-sky-500/5'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Error notification if any */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between text-rose-300 text-sm">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => {
                setDemoMode(true);
                setError(null);
                setTimeout(fetchStats, 50);
              }}
              className="px-3 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-xs font-semibold"
            >
              Zu Demo-Modus wechseln
            </button>
          </div>
        )}

        {/* ----------------- TAB: DASHBOARD ----------------- */}
        {activeTab === 'dashboard' && dsl && (
          <div className="space-y-6">
            {/* Quick Line Status Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3.5">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium">DSL Verbindungsstatus</p>
                  <p className="text-base font-bold text-white capitalize">{dsl.dsl_status || 'Verbunden'}</p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3.5">
                <div className="w-10 h-10 rounded-lg bg-sky-500/10 text-sky-400 flex items-center justify-center">
                  <Wifi className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium">Modulation &amp; Profil</p>
                  <p className="text-base font-bold text-white">{dsl.modulation} (Profil {dsl.profile})</p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3.5">
                <div className="w-10 h-10 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center">
                  <Clock className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium">Showtime (Link-Uptime)</p>
                  <p className="text-base font-bold text-white">{formatShowtime(dsl.showtime)}</p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3.5">
                <div className="w-10 h-10 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
                  <Shield className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium">Kapselung &amp; Pfad</p>
                  <p className="text-base font-bold text-white">{dsl.link_encapsulation || 'PTM'} · {dsl.data_path || 'Interleaved'}</p>
                </div>
              </div>
            </div>

            {/* Throughput Highlights Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Downstream Card */}
              <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-900/60 border border-slate-800/80 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 p-6 opacity-10">
                  <ArrowDownCircle className="w-32 h-32 text-sky-400" />
                </div>
                <div className="relative z-10 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sky-400 font-semibold text-sm">
                      <ArrowDownCircle className="w-5 h-5" />
                      Downstream Empfangsrichtung
                    </div>
                    <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 font-mono">
                      Max: {dsl.downstream_max.toFixed(1)} Mbit/s
                    </span>
                  </div>

                  <div className="flex items-baseline gap-2">
                    <span className="text-5xl font-black text-white tracking-tight">
                      {dsl.downstream_sync.toFixed(1)}
                    </span>
                    <span className="text-slate-400 font-medium text-lg">Mbit/s</span>
                  </div>

                  {/* Progress bar vs Max */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Synchronisation zur Leitungskapazität</span>
                      <span className="text-white font-medium">
                        {((dsl.downstream_sync / (dsl.downstream_max || 1)) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full h-2.5 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-sky-500 to-cyan-400 transition-all duration-500"
                        style={{ width: `${Math.min(100, (dsl.downstream_sync / (dsl.downstream_max || 1)) * 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Downstream Metrics grid */}
                  <div className="pt-3 grid grid-cols-3 gap-3 border-t border-slate-800/80">
                    <div>
                      <p className="text-xs text-slate-400">Störabstand (SNR)</p>
                      <p className={`text-base font-bold ${dsl.downstream_snr >= 9 ? 'text-emerald-400' : dsl.downstream_snr >= 6 ? 'text-amber-400' : 'text-rose-400'}`}>
                        {dsl.downstream_snr.toFixed(1)} dB
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400">Leitungsdämpfung</p>
                      <p className="text-base font-bold text-white">{dsl.downstream_attenuation.toFixed(1)} dB</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400">Ausgangsleistung</p>
                      <p className="text-base font-bold text-white">{dsl.downstream_power ?? 14.5} dBm</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Upstream Card */}
              <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-900/60 border border-slate-800/80 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 p-6 opacity-10">
                  <ArrowUpCircle className="w-32 h-32 text-emerald-400" />
                </div>
                <div className="relative z-10 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
                      <ArrowUpCircle className="w-5 h-5" />
                      Upstream Senderichtung
                    </div>
                    <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 font-mono">
                      Max: {dsl.upstream_max.toFixed(1)} Mbit/s
                    </span>
                  </div>

                  <div className="flex items-baseline gap-2">
                    <span className="text-5xl font-black text-white tracking-tight">
                      {dsl.upstream_sync.toFixed(1)}
                    </span>
                    <span className="text-slate-400 font-medium text-lg">Mbit/s</span>
                  </div>

                  {/* Progress bar vs Max */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Synchronisation zur Leitungskapazität</span>
                      <span className="text-white font-medium">
                        {((dsl.upstream_sync / (dsl.upstream_max || 1)) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full h-2.5 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-500"
                        style={{ width: `${Math.min(100, (dsl.upstream_sync / (dsl.upstream_max || 1)) * 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Upstream Metrics grid */}
                  <div className="pt-3 grid grid-cols-3 gap-3 border-t border-slate-800/80">
                    <div>
                      <p className="text-xs text-slate-400">Störabstand (SNR)</p>
                      <p className={`text-base font-bold ${dsl.upstream_snr >= 9 ? 'text-emerald-400' : dsl.upstream_snr >= 6 ? 'text-amber-400' : 'text-rose-400'}`}>
                        {dsl.upstream_snr.toFixed(1)} dB
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400">Leitungsdämpfung</p>
                      <p className="text-base font-bold text-white">{dsl.upstream_attenuation.toFixed(1)} dB</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400">Ausgangsleistung</p>
                      <p className="text-base font-bold text-white">{dsl.upstream_power ?? 7.2} dBm</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Error Diagnostics & Quality Table */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="font-bold text-base text-white flex items-center gap-2">
                  <Activity className="w-5 h-5 text-sky-400" />
                  Leitungsqualität &amp; Fehlerzähler (CRC / FEC / INP)
                </h3>
                <span className="text-xs text-slate-400">
                  Letzter Abruf: {stats?.sampled_at ? new Date(stats.sampled_at).toLocaleTimeString() : 'eben'}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <span className="text-xs text-slate-400">CRC Fehler (Down / Up)</span>
                  <p className="text-xl font-bold text-white mt-1">
                    <span className={dsl.downstream_crc && dsl.downstream_crc > 0 ? 'text-rose-400' : 'text-emerald-400'}>
                      {dsl.downstream_crc ?? 0}
                    </span>{' '}
                    /{' '}
                    <span className={dsl.upstream_crc && dsl.upstream_crc > 0 ? 'text-rose-400' : 'text-slate-300'}>
                      {dsl.upstream_crc ?? 0}
                    </span>
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">Unkorrigierbare Paketfehler</p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <span className="text-xs text-slate-400">FEC Fehler (Down / Up)</span>
                  <p className="text-xl font-bold text-white mt-1">
                    {dsl.downstream_fec ?? 0} / {dsl.upstream_fec ?? 0}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">Korrigierte Bitfehler</p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <span className="text-xs text-slate-400">Interleave Verzögerung</span>
                  <p className="text-xl font-bold text-white mt-1">
                    {dsl.downstream_interleave_delay ?? 0} ms / {dsl.upstream_interleave_delay ?? 0} ms
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">Tiefe: {dsl.downstream_interleave_depth ?? 1}</p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <span className="text-xs text-slate-400">Impulsschutz (INP)</span>
                  <p className="text-xl font-bold text-white mt-1">
                    {dsl.downstream_inp ?? 0} / {dsl.upstream_inp ?? 0} Symb.
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">G.INP Schutzsymbole</p>
                </div>
              </div>
            </div>

            {/* Simulation Preset Selector */}
            {demoMode && (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-amber-400" />
                  <span className="text-xs font-semibold text-amber-300">
                    Simulations-Szenario testen (Verhalten in Home Assistant prüfen):
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {[
                    { id: 'vdsl100', label: 'VDSL 100/40 (Optimal)' },
                    { id: 'supervectoring250', label: 'Supervectoring 250 (Profil 35b)' },
                    { id: 'degraded', label: 'Leitungsrauschen (Niedriges SNR)' },
                    { id: 'errorSpike', label: 'CRC Fehler-Spike' },
                  ].map((p) => (
                    <button
                      key={p.id}
                      onClick={() => {
                        setPreset(p.id as any);
                        setTimeout(fetchStats, 50);
                      }}
                      className={`px-3 py-1 text-xs rounded-lg font-medium transition ${
                        preset === p.id
                          ? 'bg-amber-500 text-slate-950 font-bold shadow'
                          : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ----------------- TAB: ENTITIES (26 SENSORS) ----------------- */}
        {activeTab === 'entities' && dsl && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
              <div>
                <h2 className="text-xl font-bold text-white">Home Assistant Entitätenkatalog (26 Sensoren)</h2>
                <p className="text-xs text-slate-400">
                  Alle automatisch über den DataUpdateCoordinator und SensorEntityDescription bereitgestellten Entitäten.
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="px-2.5 py-1 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                  Device: ZTE H186 ({host})
                </span>
                <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  26 Sensoren + 2 Binär + 1 Button
                </span>
              </div>
            </div>

            <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-950/80 border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider font-semibold">
                    <tr>
                      <th className="py-3 px-4">Entity ID</th>
                      <th className="py-3 px-4">Name / Übersetzung</th>
                      <th className="py-3 px-4">Kategorie</th>
                      <th className="py-3 px-4">Einheit</th>
                      <th className="py-3 px-4">Aktueller Wert</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                    {[
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_downstream_sync`, name: 'Downstream Sync Rate', cat: 'Measurement', unit: 'Mbit/s', val: `${dsl.downstream_sync.toFixed(1)} Mbit/s` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_upstream_sync`, name: 'Upstream Sync Rate', cat: 'Measurement', unit: 'Mbit/s', val: `${dsl.upstream_sync.toFixed(1)} Mbit/s` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_downstream_max`, name: 'Downstream Attainable Rate', cat: 'Measurement', unit: 'Mbit/s', val: `${dsl.downstream_max.toFixed(1)} Mbit/s` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_upstream_max`, name: 'Upstream Attainable Rate', cat: 'Measurement', unit: 'Mbit/s', val: `${dsl.upstream_max.toFixed(1)} Mbit/s` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_downstream_snr`, name: 'Downstream SNR Margin', cat: 'Measurement', unit: 'dB', val: `${dsl.downstream_snr.toFixed(1)} dB` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_upstream_snr`, name: 'Upstream SNR Margin', cat: 'Measurement', unit: 'dB', val: `${dsl.upstream_snr.toFixed(1)} dB` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_downstream_attenuation`, name: 'Downstream Attenuation', cat: 'Measurement', unit: 'dB', val: `${dsl.downstream_attenuation.toFixed(1)} dB` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_upstream_attenuation`, name: 'Upstream Attenuation', cat: 'Measurement', unit: 'dB', val: `${dsl.upstream_attenuation.toFixed(1)} dB` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_profile`, name: 'DSL Profile', cat: 'Info', unit: '-', val: dsl.profile },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_modulation`, name: 'Modulation Standard', cat: 'Info', unit: '-', val: dsl.modulation },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_dsl_status`, name: 'DSL Status', cat: 'Status', unit: '-', val: dsl.dsl_status || 'Up' },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_downstream_power`, name: 'Downstream Power', cat: 'Diagnostic', unit: 'dBm', val: `${dsl.downstream_power ?? 14.5} dBm` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_upstream_power`, name: 'Upstream Power', cat: 'Diagnostic', unit: 'dBm', val: `${dsl.upstream_power ?? 7.2} dBm` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_showtime`, name: 'DSL Showtime (Uptime)', cat: 'Diagnostic', unit: 's', val: `${dsl.showtime ?? 0} s (${formatShowtime(dsl.showtime)})` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_data_path`, name: 'Data Path Mode', cat: 'Diagnostic', unit: '-', val: dsl.data_path || 'Interleaved' },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_link_encapsulation`, name: 'Link Encapsulation', cat: 'Diagnostic', unit: '-', val: dsl.link_encapsulation || 'PTM' },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_downstream_interleave_depth`, name: 'Downstream Interleave Depth', cat: 'Diagnostic', unit: '-', val: dsl.downstream_interleave_depth ?? 8 },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_upstream_interleave_depth`, name: 'Upstream Interleave Depth', cat: 'Diagnostic', unit: '-', val: dsl.upstream_interleave_depth ?? 1 },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_downstream_interleave_delay`, name: 'Downstream Interleave Delay', cat: 'Diagnostic', unit: 'ms', val: `${dsl.downstream_interleave_delay ?? 4} ms` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_upstream_interleave_delay`, name: 'Upstream Interleave Delay', cat: 'Diagnostic', unit: 'ms', val: `${dsl.upstream_interleave_delay ?? 0} ms` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_downstream_inp`, name: 'Downstream INP', cat: 'Diagnostic', unit: 'symbols', val: `${dsl.downstream_inp ?? 2.0} symbols` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_upstream_inp`, name: 'Upstream INP', cat: 'Diagnostic', unit: 'symbols', val: `${dsl.upstream_inp ?? 0.0} symbols` },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_downstream_crc`, name: 'Downstream CRC Errors', cat: 'Diagnostic', unit: 'errors', val: dsl.downstream_crc ?? 0 },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_upstream_crc`, name: 'Upstream CRC Errors', cat: 'Diagnostic', unit: 'errors', val: dsl.upstream_crc ?? 0 },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_downstream_fec`, name: 'Downstream FEC Errors', cat: 'Diagnostic', unit: 'errors', val: dsl.downstream_fec ?? 0 },
                      { id: `sensor.zte_h186_${host.replace(/\./g, '_')}_upstream_fec`, name: 'Upstream FEC Errors', cat: 'Diagnostic', unit: 'errors', val: dsl.upstream_fec ?? 0 },
                      { id: `binary_sensor.zte_h186_${host.replace(/\./g, '_')}_dsl_link`, name: 'DSL Line Connected', cat: 'Binary Sensor (Connectivity)', unit: '-', val: 'On (Aktiv)' },
                      { id: `binary_sensor.zte_h186_${host.replace(/\./g, '_')}_line_noise_warning`, name: 'Line Noise Warning (Low SNR)', cat: 'Binary Sensor (Problem)', unit: '-', val: dsl.downstream_snr < 6 ? 'On (Warnung)' : 'Off (Normal)' },
                      { id: `button.zte_h186_${host.replace(/\./g, '_')}_refresh_stats`, name: 'Refresh DSL Stats Now', cat: 'Button Action', unit: '-', val: 'Press' },
                    ].map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-4 text-sky-400 select-all">{row.id}</td>
                        <td className="py-2.5 px-4 font-sans text-slate-200">{row.name}</td>
                        <td className="py-2.5 px-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            row.cat === 'Measurement'
                              ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                              : row.cat === 'Diagnostic'
                              ? 'bg-slate-800 text-slate-400 border border-slate-700'
                              : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          }`}>
                            {row.cat}
                          </span>
                        </td>
                        <td className="py-2.5 px-4 text-slate-400 font-sans">{row.unit}</td>
                        <td className="py-2.5 px-4 text-white font-bold">{row.val}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ----------------- TAB: HACS FILE EXPLORER ----------------- */}
        {activeTab === 'hacs' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <FileCode className="w-5 h-5 text-sky-400" />
                  HACS Component Quellcode-Browser
                </h2>
                <p className="text-xs text-slate-400">
                  Vollständige Repository-Dateien für <code className="text-sky-300">custom_components/zte_h186/</code> bereit für GitHub &amp; HACS.
                </p>
              </div>
              <button
                onClick={() => {
                  const curr = hacsFiles.find((f) => f.path === selectedFile);
                  if (curr) copyToClipboard(curr.content, 'hacs_current');
                }}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow"
              >
                <Copy className="w-3.5 h-3.5" />
                {copiedKey === 'hacs_current' ? 'Kopiert!' : 'Dateiinhalt kopieren'}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* File List Navigation */}
              <div className="rounded-2xl bg-slate-900 border border-slate-800 p-3 space-y-1">
                <p className="text-xs font-semibold text-slate-400 px-3 py-2 uppercase tracking-wider">
                  Dateien im Projekt
                </p>
                <div className="space-y-0.5">
                  {hacsFiles.map((file) => {
                    const isSelected = selectedFile === file.path;
                    return (
                      <button
                        key={file.path}
                        onClick={() => setSelectedFile(file.path)}
                        className={`w-full text-left px-3 py-2.5 rounded-xl text-xs font-mono transition flex items-center justify-between ${
                          isSelected
                            ? 'bg-sky-600/10 text-sky-400 border border-sky-500/20 font-bold'
                            : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-transparent'
                        }`}
                      >
                        <div className="truncate">
                          <span>{file.path.split('/').pop()}</span>
                          <p className="text-[10px] text-slate-500 truncate font-sans font-normal mt-0.5">
                            {file.description}
                          </p>
                        </div>
                        <span className="text-[10px] text-slate-600 ml-2">{(file.size / 1024).toFixed(1)}k</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Code Viewer */}
              <div className="md:col-span-2 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col overflow-hidden shadow-2xl">
                <div className="bg-slate-950/80 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-rose-500/80 inline-block" />
                    <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block" />
                    <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block" />
                    <span className="text-xs font-mono text-slate-300 ml-2">{selectedFile}</span>
                  </div>
                  <span className="text-[11px] text-slate-500">
                    {hacsFiles.find((f) => f.path === selectedFile)?.content.split('\n').length || 0} Zeilen
                  </span>
                </div>
                <div className="p-4 overflow-x-auto max-h-[620px] bg-slate-950/60 font-mono text-xs text-slate-300 leading-relaxed select-all">
                  <pre>{hacsFiles.find((f) => f.path === selectedFile)?.content || '# Lade Datei...'}</pre>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ----------------- TAB: CONFIG FLOW SIMULATOR ----------------- */}
        {activeTab === 'config_flow' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Sliders className="w-5 h-5 text-sky-400" />
                Home Assistant UI-Einrichtung (Config Flow Vorschau)
              </h2>
              <p className="text-xs text-slate-400">
                So erscheint die Integration in Home Assistant unter <em>Einstellungen &gt; Geräte &amp; Dienste</em>.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Step 1: User Add Dialog */}
              <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-sky-400" />
                    <h3 className="font-bold text-white text-sm">1. Ersteinrichtung (async_step_user)</h3>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">Initial Setup</span>
                </div>

                <p className="text-xs text-slate-400">
                  Benutzer gibt Router-IP und Passwort in der Weboberfläche ein. Die Integration validiert den Zugriff sofort:
                </p>

                <div className="space-y-3 pt-2">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">IP-Adresse oder Hostname</label>
                    <input
                      type="text"
                      value={host}
                      onChange={(e) => setHost(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white font-mono focus:outline-none focus:border-sky-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Benutzername</label>
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white font-mono focus:outline-none focus:border-sky-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Passwort</label>
                    <input
                      type="password"
                      placeholder="••••••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white font-mono focus:outline-none focus:border-sky-500"
                    />
                  </div>
                  <button
                    onClick={fetchStats}
                    className="w-full py-2.5 px-4 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs shadow-md transition"
                  >
                    Absenden &amp; Verbindung prüfen
                  </button>
                </div>
              </div>

              {/* Step 2: Options & Reconfigure Dialog */}
              <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                    <h3 className="font-bold text-white text-sm">2. Optionen &amp; Reconfiguration</h3>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">Options Flow</span>
                </div>

                <p className="text-xs text-slate-400">
                  Optionen-Dialog zur Anpassung des Abrufintervalls und Reconfigure-Schritt bei IP- oder Passwortänderung:
                </p>

                <div className="space-y-3 pt-2">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Abfrageintervall: {pollInterval} Sekunden
                    </label>
                    <input
                      type="range"
                      min="15"
                      max="300"
                      step="5"
                      value={pollInterval}
                      onChange={(e) => setPollInterval(parseInt(e.target.value, 10))}
                      className="w-full accent-sky-500"
                    />
                    <div className="flex justify-between text-[10px] text-slate-500">
                      <span>15s (Schnell)</span>
                      <span>60s (Standard)</span>
                      <span>300s (Schonend)</span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5 text-xs">
                    <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Reconfigure Flow unterstützt</span>
                    </div>
                    <p className="text-slate-400 text-[11px]">
                      Bei geänderter Router-IP oder neuem Passwort kann der Eintrag per 3-Punkte-Menü in Home Assistant aktualisiert werden, ohne dass Entitäten, Dashboards oder Langzeitstatistiken verloren gehen.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ----------------- TAB: PROTOCOL INSPECTOR ----------------- */}
        {activeTab === 'protocol' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Terminal className="w-5 h-5 text-sky-400" />
                  ZTE H186 Authentifizierungs- &amp; Abfrageprotokoll
                </h2>
                <p className="text-xs text-slate-400">
                  Detaillierte Einsicht in die 5 Schritte des ZTE-Weboberflächen-Protokolls gemäß <code className="text-sky-300">docs/PROTOCOL.md</code>.
                </p>
              </div>
              <button
                onClick={runProtocolTest}
                disabled={testingProtocol}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                {testingProtocol ? 'Teste Schritte...' : 'Protokolltest ausführen'}
              </button>
            </div>

            <div className="space-y-3">
              {[
                {
                  step: 1,
                  title: '1. Startseite laden & Session-Token dekodieren',
                  req: `GET http://${host}/`,
                  desc: 'Liest HTML der Startseite und extrahiert Variable _sessionTmpToken = "\\x..\\x..". Die Hex-Bytes werden in einen ASCII-String dekodiert.',
                  tag: 'Session Token',
                },
                {
                  step: 2,
                  title: '2. Einmaligen Login-Token anfordern',
                  req: `GET http://${host}/function_module/login_module/login_page/logintoken_lua.lua`,
                  desc: 'Referer: Startseite. Liefert eine numerische Einmal-Zufallszahl zur Verhinderung von Replay-Angriffen.',
                  tag: 'Challenge Token',
                },
                {
                  step: 3,
                  title: '3. SHA-256 Hash berechnen & Formular senden',
                  req: `POST http://${host}/ (Username=admin, Password=SHA256(pwd+token), _sessionTOKEN)`,
                  desc: 'Authentifiziert die Sitzung. Das Modem setzt das Cookie SID. Erfolgreich bei HTTP 200/302 und erhaltener SID.',
                  tag: 'Authentication',
                },
                {
                  step: 4,
                  title: '4. DSL-Statusseite aufrufen (Zustandssynchronisation)',
                  req: `GET http://${host}/getpage.lua?pid=1002&nextpage=Internet_AdminInternetStatus_DSL_t.lp`,
                  desc: 'Referer: Startseite. Priming-Request: Ohne diesen Zwischenschritt blockiert die Firmware den XML-Endpunkt mit Timeout.',
                  tag: 'Session Priming',
                },
                {
                  step: 5,
                  title: '5. DSL-XML Daten abrufen & parsen',
                  req: `GET http://${host}/common_page/internet_dsl_interface_lua.lua?_=<timestamp>`,
                  desc: 'Referer: Statusseite, Header: X-Requested-With: XMLHttpRequest. Liefert XML mit allen 26 Parametern (ParaName/ParaValue).',
                  tag: 'XML Payload',
                },
              ].map((step) => {
                const stepResult = protocolSteps.find((s) => s.step === step.step);
                return (
                  <div
                    key={step.step}
                    className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2.5 transition hover:border-slate-700"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-sky-500/10 text-sky-400 font-bold text-xs flex items-center justify-center border border-sky-500/20">
                          {step.step}
                        </span>
                        <h3 className="font-bold text-sm text-white">{step.title}</h3>
                      </div>
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-medium">
                        {step.tag}
                      </span>
                    </div>

                    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-xs font-mono text-sky-300">
                      {step.req}
                    </div>

                    <p className="text-xs text-slate-400 leading-relaxed">{step.desc}</p>

                    {stepResult && (
                      <div className="mt-2 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                        <span>{stepResult.details} ({stepResult.latencyMs} ms)</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ----------------- TAB: RAW & EXPORT ----------------- */}
        {activeTab === 'raw' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-white">Rohdaten &amp; Home Assistant YAML</h2>
                <p className="text-xs text-slate-400">
                  Exportformate für JSON, CLI-Skripte und Home Assistant Package-Vorlagen.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Live JSON Payload */}
              <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="text-sm font-bold text-white">Home Assistant JSON Attribut-Payload</h3>
                  <button
                    onClick={() => copyToClipboard(JSON.stringify(stats, null, 2), 'raw_json')}
                    className="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-1"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    {copiedKey === 'raw_json' ? 'Kopiert!' : 'Kopieren'}
                  </button>
                </div>
                <pre className="p-3 bg-slate-950 rounded-xl text-xs font-mono text-slate-300 max-h-96 overflow-y-auto">
                  {JSON.stringify(stats, null, 2)}
                </pre>
              </div>

              {/* Raw Modem XML */}
              <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="text-sm font-bold text-white">Extrahierte XML Name-Value Paare</h3>
                  <button
                    onClick={() => copyToClipboard(JSON.stringify(stats?.raw || {}, null, 2), 'raw_xml')}
                    className="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-1"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    {copiedKey === 'raw_xml' ? 'Kopiert!' : 'Kopieren'}
                  </button>
                </div>
                <pre className="p-3 bg-slate-950 rounded-xl text-xs font-mono text-slate-300 max-h-96 overflow-y-auto">
                  {JSON.stringify(stats?.raw || {}, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/60 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400">
          <div>
            ZTE H186 DSL Modem Home Assistant Integration · Copyright (C) 2026 Daniel Ebenhöh
          </div>
          <div className="flex items-center gap-4">
            <span className="text-slate-500">GPL-3.0-only</span>
            <span className="text-slate-500">HACS Quality Scale: Bronze</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
