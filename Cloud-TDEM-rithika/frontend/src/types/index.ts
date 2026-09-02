export type FileStatus = 'ACTIVE' | 'EXPIRING_SOON' | 'EXPIRED';

export interface VaultFile {
  file_id: string;
  filename: string;
  status: FileStatus;
  created_at: string;
  expires_at: string;
  last_accessed_at?: string | null;
  last_refreshed_at?: string | null;
  file_size?: number;
  integrity_status?: string;
  encryption_status?: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  environment: string;
  crypto_available: boolean;
  ai_available: boolean;
  storage_available: boolean;
}

export interface AuditEntry {
  timestamp: string;
  action: string;
  result: string;
  user_id?: string | null;
  file_id?: string | null;
  risk_score?: number | null;
  ai_decision?: string | null;
  request_id?: string | null;
  details?: Record<string, unknown> | null;
}

export interface SecurityMetrics {
  encryption_time_ms: number;
  decryption_time_ms: number;
  request_count: number;
  failure_count: number;
  ai_decision_count: number;
  files_active: number;
  files_expired: number;
}

export interface RetrieveRequest {
  file_id: string;
  login_hour?: number;
  trusted_device?: number;
  country?: string;
  ip_reputation?: number;
  vpn_detected?: number;
  failed_login_attempts?: number;
  browser?: string;
  access_frequency?: number;
  file_sensitivity?: string;
  refresh_frequency?: number;
}

export interface UploadResult {
  file_id: string;
  filename: string;
  file_size: number;
  created_at: string;
  expires_at: string;
  status: string;
  integrity_status: string;
  encryption_status: string;
}
