import { apiRequest } from './client';
import type { RetrieveRequest, UploadResult, VaultFile } from '../types';

export async function listFiles(): Promise<VaultFile[]> {
  return apiRequest<VaultFile[]>('/api/v1/files');
}

export async function getFileDetails(fileId: string): Promise<VaultFile> {
  return apiRequest<VaultFile>(`/api/v1/files/${fileId}`);
}

export async function uploadFile(file: File, expiryMinutes: number): Promise<UploadResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'}/api/v1/files/ingest?expiry_minutes=${expiryMinutes}`, {
    method: 'POST',
    headers: {
      Authorization: 'Bearer dev-token',
    },
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail ?? payload?.message ?? 'Upload failed';
    throw new Error(detail);
  }

  return (await response.json()) as UploadResult;
}

export async function refreshFile(fileId: string): Promise<{ file_id: string; expires_at: string; status: string }> {
  return apiRequest(`/api/v1/files/${fileId}/refresh`, {
    method: 'POST',
  });
}

export async function deleteFile(fileId: string): Promise<{ success: boolean; message: string }> {
  return apiRequest(`/api/v1/files/${fileId}`, {
    method: 'DELETE',
  });
}

export async function retrieveFile(fileId: string, request: Partial<RetrieveRequest> = {}): Promise<Blob> {
  const body: RetrieveRequest = {
    file_id: fileId,
    login_hour: new Date().getHours(),
    trusted_device: 1,
    country: 'Unknown',
    ip_reputation: 0.8,
    vpn_detected: 0,
    failed_login_attempts: 0,
    browser: 'Chrome',
    access_frequency: 1,
    file_sensitivity: 'Medium',
    refresh_frequency: 0,
    ...request,
  };

  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'}/api/v1/files/retrieve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'Bearer dev-token',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const message = payload?.detail ?? 'Retrieve failed';
    throw new Error(message);
  }

  const contentType = response.headers.get('content-type') ?? 'application/octet-stream';
  if (contentType.includes('application/json')) {
    const payload = (await response.json()) as { content?: string | number[] | ArrayBuffer | null };
    const rawContent = payload.content ?? '';

    if (typeof rawContent === 'string') {
      return new Blob([rawContent], { type: 'application/octet-stream' });
    }

    if (Array.isArray(rawContent)) {
      return new Blob([Uint8Array.from(rawContent)], { type: 'application/octet-stream' });
    }

    return new Blob([String(rawContent)], { type: 'application/octet-stream' });
  }

  return response.blob();
}
