import { apiRequest } from './client';
import type { HealthStatus } from '../types';

export async function getHealth(): Promise<HealthStatus> {
  return apiRequest<HealthStatus>('/health');
}
