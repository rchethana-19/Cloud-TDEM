import { apiRequest } from './client';
import type { AuditEntry } from '../types';

export async function getAudit(limit = 50): Promise<AuditEntry[]> {
  return apiRequest<AuditEntry[]>(`/api/v1/audit?limit=${limit}`);
}
