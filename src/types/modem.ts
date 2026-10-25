export interface DslRawValues {
  Downstream_current_rate: string;
  Upstream_current_rate: string;
  Downstream_max_rate: string;
  Upstream_max_rate: string;
  Downstream_noise_margin: string;
  Upstream_noise_margin: string;
  Downstream_attenuation: string;
  Upstream_attenuation: string;
  CurrentProfile: string;
  Module_type: string;
  Status?: string;
  Downstream_power?: string;
  Upstream_power?: string;
  Data_path?: string;
  DownInterleavedepth?: string;
  UpInterleaveDepth?: string;
  DownInterleaveDelay?: string;
  UpInterleaveDelay?: string;
  DownstreamInp?: string;
  UpstreamInp?: string;
  Showtime_start?: string;
  tLinkEncapsulationUsed?: string;
  DownCrc_errors?: string;
  UpCrc_errors?: string;
  Fec_errors?: string;
  Atuc_fec_errors?: string;
  [key: string]: string | undefined;
}

export interface DslNormalizedData {
  downstream_sync: number; // Mbit/s
  upstream_sync: number; // Mbit/s
  downstream_max: number; // Mbit/s
  upstream_max: number; // Mbit/s
  downstream_snr: number; // dB
  upstream_snr: number; // dB
  downstream_attenuation: number; // dB
  upstream_attenuation: number; // dB
  profile: string; // e.g. 17a, 35b
  modulation: string; // e.g. VDSL2
  dsl_status?: string; // e.g. Up, Showtime
  downstream_power?: number; // dBm
  upstream_power?: number; // dBm
  data_path?: string; // Interleaved, Fast
  downstream_interleave_depth?: number;
  upstream_interleave_depth?: number;
  downstream_interleave_delay?: number; // ms
  upstream_interleave_delay?: number; // ms
  downstream_inp?: number; // symbols
  upstream_inp?: number; // symbols
  showtime?: number; // seconds
  link_encapsulation?: string; // PTM, ATM
  downstream_crc?: number; // errors
  upstream_crc?: number; // errors
  downstream_fec?: number; // errors
  upstream_fec?: number; // errors
}

export interface ModemStatsResponse {
  status: 'ok' | 'error';
  sampled_at: string | null;
  data: DslNormalizedData | Record<string, never>;
  raw?: DslRawValues;
  error_code?: string;
  error_message?: string;
  is_demo?: boolean;
}

export interface ProtocolStepResult {
  step: number;
  name: string;
  description: string;
  status: 'pending' | 'success' | 'failed' | 'skipped';
  details?: string;
  latencyMs?: number;
  httpStatus?: number;
}

export interface ModemConnectionConfig {
  host: string;
  username: string;
  password?: string;
  demoMode: boolean;
  demoProfilePreset: 'vdsl100' | 'supervectoring250' | 'degraded' | 'errorSpike';
  pollIntervalSec: number;
  autoPoll: boolean;
}

export interface HistoricalDataPoint {
  timestamp: string;
  downstream_sync: number;
  upstream_sync: number;
  downstream_snr: number;
  upstream_snr: number;
  downstream_attenuation: number;
  upstream_crc: number;
  downstream_crc: number;
  downstream_fec: number;
}
