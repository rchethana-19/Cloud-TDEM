import { apiRequest } from './client';
import type { SecurityMetrics } from '../types';

export async function getSecurityMetrics(): Promise<SecurityMetrics> {
  return apiRequest<SecurityMetrics>('/api/v1/metrics');
}
