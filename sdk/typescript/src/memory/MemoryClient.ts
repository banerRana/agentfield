import axios, { AxiosInstance } from 'axios';
import type { MemoryScope } from '../types/agent.js';

export class MemoryClient {
  private readonly http: AxiosInstance;

  constructor(baseUrl: string) {
    this.http = axios.create({
      baseURL: baseUrl.replace(/\/$/, '')
    });
  }

  async set(key: string, data: any, scope: MemoryScope, scopeId?: string) {
    await this.http.post('/api/v1/memory/set', {
      key,
      data,
      scope,
      scope_id: scopeId
    });
  }

  async get<T = any>(key: string, scope?: MemoryScope, scopeId?: string): Promise<T | undefined> {
    const res = await this.http.post('/api/v1/memory/get', {
      key,
      scope,
      scope_id: scopeId
    });
    return res.data?.data as T;
  }

  async setVector(key: string, vector: number[], metadata?: any, scope?: MemoryScope, scopeId?: string) {
    await this.http.post('/api/v1/memory/vector/set', {
      key,
      vector,
      metadata,
      scope,
      scope_id: scopeId
    });
  }

  async searchVector(query: number[] | string, options: { limit?: number } = {}) {
    const res = await this.http.post('/api/v1/memory/vector/search', {
      query,
      limit: options.limit ?? 5
    });
    return res.data?.results ?? [];
  }
}
