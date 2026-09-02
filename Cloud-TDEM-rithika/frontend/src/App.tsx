import { useEffect, useMemo, useState } from 'react';
import './App.css';
import { getAudit } from './api/audit';
import { deleteFile, listFiles, refreshFile, retrieveFile, uploadFile } from './api/files';
import { getHealth } from './api/health';
import { getSecurityMetrics } from './api/security';
import type { AuditEntry, HealthStatus, SecurityMetrics, VaultFile } from './types';

type View = 'vault' | 'upload' | 'security' | 'activity';

type UploadForm = {
  file: File | null;
  duration: number;
  unit: 'minutes' | 'hours' | 'days';
};

const NAV_ITEMS: { key: View; label: string }[] = [
  { key: 'vault', label: 'Vault' },
  { key: 'upload', label: 'Upload' },
  { key: 'security', label: 'Security' },
  { key: 'activity', label: 'Activity' },
];

const formatDate = (value: string | undefined | null): string => {
  if (!value) return 'Not available';
  return new Date(value).toLocaleString([], {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
};

const formatRemaining = (value: string): string => {
  const target = new Date(value).getTime();
  const diff = target - Date.now();

  if (diff <= 0) return 'Expired';

  const totalMinutes = Math.max(0, Math.floor(diff / 60000));
  const days = Math.floor(totalMinutes / (60 * 24));
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
  const minutes = totalMinutes % 60;

  if (days > 0) {
    return `${days} day${days === 1 ? '' : 's'} ${hours} hour${hours === 1 ? '' : 's'}`;
  }

  if (hours > 0) {
    return `${hours} hour${hours === 1 ? '' : 's'} ${minutes} minute${minutes === 1 ? '' : 's'}`;
  }

  return `${minutes} minute${minutes === 1 ? '' : 's'}`;
};

const getStatusClass = (status: string): string => {
  switch (status) {
    case 'EXPIRING_SOON':
      return 'status-soon';
    case 'EXPIRED':
      return 'status-expired';
    default:
      return 'status-active';
  }
};

function App() {
  const [activeView, setActiveView] = useState<View>('vault');
  const [files, setFiles] = useState<VaultFile[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [metrics, setMetrics] = useState<SecurityMetrics | null>(null);
  const [selectedFile, setSelectedFile] = useState<VaultFile | null>(null);
  const [uploadForm, setUploadForm] = useState<UploadForm>({
    file: null,
    duration: 10,
    unit: 'hours',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [activityMessage, setActivityMessage] = useState<string | null>(null);

  const activeCount = useMemo(
    () => files.filter((file) => file.status === 'ACTIVE').length,
    [files],
  );
  const expiringSoonCount = useMemo(
    () => files.filter((file) => file.status === 'EXPIRING_SOON').length,
    [files],
  );
  const expiredCount = useMemo(
    () => files.filter((file) => file.status === 'EXPIRED').length,
    [files],
  );

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [filesData, healthData, auditData, metricsData] = await Promise.allSettled([
        listFiles(),
        getHealth(),
        getAudit(25),
        getSecurityMetrics(),
      ]);

      if (filesData.status === 'fulfilled') setFiles(filesData.value);
      if (healthData.status === 'fulfilled') setHealth(healthData.value);
      if (auditData.status === 'fulfilled') setAudit(auditData.value);
      if (metricsData.status === 'fulfilled') setMetrics(metricsData.value);

      const firstError = [filesData, healthData, auditData, metricsData].find(
        (result) => result.status === 'rejected',
      );

      if (firstError) {
        setError('The backend is unavailable or the API request failed.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected API error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  useEffect(() => {
    if (files.length > 0 && !selectedFile) {
      setSelectedFile(files[0]);
    }
  }, [files, selectedFile]);

  const refreshVault = async () => {
    await loadData();
  };

  const handleUpload = async () => {
    if (!uploadForm.file) {
      setError('Choose a file before uploading.');
      return;
    }

    const multiplier = {
      minutes: 1,
      hours: 60,
      days: 60 * 24,
    }[uploadForm.unit] ?? 60;

    const expiryMinutes = Math.max(1, uploadForm.duration * multiplier);

    setUploading(true);
    setError(null);

    try {
      const result = await uploadFile(uploadForm.file, expiryMinutes);
      setActivityMessage(`File uploaded successfully: ${result.filename}`);
      setUploadForm({ file: null, duration: 10, unit: 'hours' });
      const input = document.getElementById('file-upload-input') as HTMLInputElement | null;
      if (input) input.value = '';
      await refreshVault();
      setActiveView('vault');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected upload error');
    } finally {
      setUploading(false);
    }
  };

  const handleRetrieve = async (file: VaultFile) => {
    try {
      const response = await retrieveFile(file.file_id);
      const url = URL.createObjectURL(response);
      const link = document.createElement('a');
      link.href = url;
      link.download = file.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      setActivityMessage(`File retrieved successfully: ${file.filename}`);
      await refreshVault();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Retrieve failed';
      setError(message);
      setActivityMessage(null);
    }
  };

  const handleRefresh = async (fileId: string) => {
    try {
      await refreshFile(fileId);
      setActivityMessage('Access refreshed successfully.');
      await refreshVault();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Refresh failed');
    }
  };

  const handleDelete = async (fileId: string) => {
    try {
      const result = await deleteFile(fileId);
      setActivityMessage(result.message || 'File deleted successfully.');
      await refreshVault();
      setSelectedFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark">TDEM</div>
          <div>
            <div className="brand-name">Secure Vault</div>
            <div className="brand-subtitle">Temporal Data Encryption Model</div>
          </div>
        </div>

        <nav className="nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              type="button"
              className={activeView === item.key ? 'nav-item active' : 'nav-item'}
              onClick={() => setActiveView(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="status-pill">
          <span className="status-dot" />
          {health ? health.status : 'Checking'}
        </div>
      </header>

      <main className="main-panel">
        {activeView === 'vault' && (
          <section className="vault-layout">
            <div className="vault-stage panel-card">
              <div className="vault-summary">
                <div className="summary-small">ACTIVE FILES</div>
                <div className="summary-value">{activeCount}</div>
              </div>

              <div className="orb-wrap">
                {files.length === 0 ? (
                  <div className="empty-orb">
                    <div className="empty-orb-title">No files yet</div>
                    <div className="empty-orb-copy">Upload a file to create the first secure ring.</div>
                  </div>
                ) : (
                  files.map((file, index) => {
                    const ringRadius = 120 + index * 30;
                    const isSelected = selectedFile?.file_id === file.file_id;
                    return (
                      <button
                        type="button"
                        key={file.file_id}
                        className={`ring ${getStatusClass(file.status)} ${isSelected ? 'selected' : ''}`}
                        style={{ width: ringRadius, height: ringRadius }}
                        onClick={() => setSelectedFile(file)}
                        title={`${file.filename}\n${file.status}\nExpires: ${formatDate(file.expires_at)}`}
                      >
                        <span>{file.filename}</span>
                      </button>
                    );
                  })
                )}

                <div className="vault-orb">
                  <div className="orb-text">TDEM</div>
                  <div className="orb-subtext">SECURE VAULT</div>
                  <div className="orb-stat">ACTIVE FILES: {activeCount}</div>
                </div>
              </div>
            </div>

            <aside className="side-panel panel-card">
              <div className="panel-header">
                <h3>Vault Overview</h3>
              </div>

              <div className="stat-grid">
                <div className="mini-stat">
                  <span className="mini-label">ACTIVE</span>
                  <strong>{activeCount}</strong>
                </div>
                <div className="mini-stat warning">
                  <span className="mini-label">EXPIRING</span>
                  <strong>{expiringSoonCount}</strong>
                </div>
                <div className="mini-stat muted">
                  <span className="mini-label">EXPIRED</span>
                  <strong>{expiredCount}</strong>
                </div>
              </div>

              {selectedFile ? (
                <div className="selected-file">
                  <div className="selected-name">{selectedFile.filename}</div>
                  <div className={`table-badge ${getStatusClass(selectedFile.status)}`}>
                    {selectedFile.status}
                  </div>
                  <dl>
                    <div>
                      <dt>Expires</dt>
                      <dd>{formatDate(selectedFile.expires_at)}</dd>
                    </div>
                    <div>
                      <dt>Remaining</dt>
                      <dd>{formatRemaining(selectedFile.expires_at)}</dd>
                    </div>
                    <div>
                      <dt>Created</dt>
                      <dd>{formatDate(selectedFile.created_at)}</dd>
                    </div>
                  </dl>
                  <div className="selected-actions">
                    <button type="button" className="primary-button" onClick={() => void handleRetrieve(selectedFile)}>
                      Retrieve
                    </button>
                    <button type="button" className="secondary-button" onClick={() => void handleRefresh(selectedFile.file_id)}>
                      Extend Access
                    </button>
                    <button type="button" className="danger-button" onClick={() => void handleDelete(selectedFile.file_id)}>
                      Delete
                    </button>
                  </div>
                </div>
              ) : (
                <div className="empty-state">
                  Select a ring to inspect its metadata.
                </div>
              )}
            </aside>
          </section>
        )}

        {activeView === 'upload' && (
          <section className="panel-card form-panel">
            <div className="panel-header">
              <h3>Secure Upload</h3>
            </div>

            <div className="upload-grid">
              <label className="field-block">
                <span>File</span>
                <input
                  id="file-upload-input"
                  type="file"
                  onChange={(event) =>
                    setUploadForm((current) => ({
                      ...current,
                      file: event.target.files?.[0] ?? null,
                    }))
                  }
                />
              </label>

              <div className="field-row">
                <label className="field-block compact">
                  <span>Validity</span>
                  <input
                    type="number"
                    min={1}
                    max={7}
                    value={uploadForm.duration}
                    onChange={(event) =>
                      setUploadForm((current) => ({
                        ...current,
                        duration: Number(event.target.value || 1),
                      }))
                    }
                  />
                </label>

                <label className="field-block compact">
                  <span>Unit</span>
                  <select
                    value={uploadForm.unit}
                    onChange={(event) =>
                      setUploadForm((current) => ({
                        ...current,
                        unit: event.target.value as 'minutes' | 'hours' | 'days',
                      }))
                    }
                  >
                    <option value="minutes">Minutes</option>
                    <option value="hours">Hours</option>
                    <option value="days">Days</option>
                  </select>
                </label>
              </div>
            </div>

            <div className="panel-actions">
              <button type="button" className="primary-button large" onClick={() => void handleUpload()} disabled={uploading}>
                {uploading ? 'Securing upload...' : 'SECURE UPLOAD'}
              </button>
            </div>

            {uploadForm.file && (
              <div className="upload-preview">
                <div className="summary-small">SELECTED FILE</div>
                <strong>{uploadForm.file.name}</strong>
                <span>{Math.round(uploadForm.file.size / 1024)} KB</span>
              </div>
            )}
          </section>
        )}

        {activeView === 'security' && (
          <section className="security-grid">
            <div className="panel-card">
              <div className="panel-header">
                <h3>Security Status</h3>
              </div>
              <div className="security-block">
                <div>
                  <span className="mini-label">Vault Health</span>
                  <strong>{health?.status ?? 'Unknown'}</strong>
                </div>
                <div>
                  <span className="mini-label">Crypto Adapter</span>
                  <strong>{health?.crypto_available ? 'Online' : 'Offline'}</strong>
                </div>
                <div>
                  <span className="mini-label">AI Adapter</span>
                  <strong>{health?.ai_available ? 'Online' : 'Offline'}</strong>
                </div>
              </div>
            </div>

            <div className="panel-card">
              <div className="panel-header">
                <h3>System Metrics</h3>
              </div>
              <div className="metric-grid">
                <div className="metric-item">
                  <span>Encryption time</span>
                  <strong>{metrics ? `${metrics.encryption_time_ms.toFixed(2)} ms` : 'Unavailable'}</strong>
                </div>
                <div className="metric-item">
                  <span>Decryption time</span>
                  <strong>{metrics ? `${metrics.decryption_time_ms.toFixed(2)} ms` : 'Unavailable'}</strong>
                </div>
                <div className="metric-item">
                  <span>Active files</span>
                  <strong>{metrics?.files_active ?? 0}</strong>
                </div>
                <div className="metric-item">
                  <span>Expired files</span>
                  <strong>{metrics?.files_expired ?? 0}</strong>
                </div>
              </div>
            </div>

            <div className="panel-card full-span">
              <div className="panel-header">
                <h3>Recent Security Activity</h3>
              </div>
              <div className="audit-list">
                {audit.slice(0, 8).map((entry) => (
                  <div key={`${entry.timestamp}-${entry.action}-${entry.file_id ?? 'global'}`} className="audit-row">
                    <div>
                      <strong>{entry.action}</strong>
                      <span>{entry.result}</span>
                    </div>
                    <div className="audit-meta">
                      <span>{entry.file_id ?? 'System'}</span>
                      <span>{entry.ai_decision ?? 'N/A'}</span>
                      <span>{entry.risk_score != null ? entry.risk_score.toFixed(2) : 'N/A'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {activeView === 'activity' && (
          <section className="panel-card">
            <div className="panel-header">
              <h3>Audit Trail</h3>
            </div>
            <div className="audit-table">
              <div className="audit-table-head audit-row">
                <span>Timestamp</span>
                <span>Action</span>
                <span>Result</span>
                <span>File</span>
                <span>Risk</span>
              </div>
              {audit.map((entry) => (
                <div key={`${entry.timestamp}-${entry.action}-${entry.file_id ?? 'global'}`} className="audit-row audit-data-row">
                  <span>{formatDate(entry.timestamp)}</span>
                  <span>{entry.action}</span>
                  <span>{entry.result}</span>
                  <span>{entry.file_id ?? 'System'}</span>
                  <span>{entry.risk_score != null ? entry.risk_score.toFixed(2) : 'N/A'}</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      {(error || activityMessage) && (
        <div className="notice-bar">
          {error && <div className="notice error">{error}</div>}
          {activityMessage && <div className="notice success">{activityMessage}</div>}
        </div>
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="spinner" />
          <span>Synchronizing vault state...</span>
        </div>
      )}
    </div>
  );
}

export default App;
