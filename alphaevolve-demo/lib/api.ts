import type { Metric, RunConfig } from './world';

export async function startEvolution(payload: { code: string; evaluator?: string; metrics: Metric[]; config: RunConfig }) {
  if (!payload?.code) throw new Error('startEvolution: code required');
  const res = await fetch('/api/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      code: payload.code,
      evaluator: payload.evaluator || '',
      metrics: payload.metrics,
      config: payload.config,
    }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`startEvolution failed: ${text}`);
  }
  return res.json() as Promise<{ ok: true; runId: string }>;
}
