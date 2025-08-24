import { NextResponse } from 'next/server';
import { mkdtemp, writeFile } from 'fs/promises';
import { tmpdir } from 'os';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export async function POST(request: Request) {
  try {
    const { code, evaluator, config } = await request.json();
    if (!code || !evaluator) {
      return NextResponse.json({ ok: false, error: 'code and evaluator required' }, { status: 400 });
    }
    const dir = await mkdtemp(path.join(tmpdir(), 'oe-'));
    const codePath = path.join(dir, 'seed.py');
    const evalPath = path.join(dir, 'eval.py');
    await writeFile(codePath, code);
    await writeFile(evalPath, evaluator);

    // Write minimal YAML config for OpenEvolve
    const cfgPath = path.join(dir, 'config.yaml');
    const yaml = [
      `max_iterations: ${config?.generations ?? 10}`,
      `random_seed: ${config?.seed ?? 42}`,
      'database:',
      `  population_size: ${config?.population ?? 24}`,
      'llm:',
      '  models:',
      `    - name: ${config?.model ?? 'gpt-4o-mini'}`,
      '      weight: 1.0',
    ].join('\n');
    await writeFile(cfgPath, yaml);

    const outDir = path.join(dir, 'output');
    const root = path.resolve(process.cwd(), '..');
    const runScript = path.join(root, 'openevolve-run.py');
    const iterations = config?.generations ?? 10;
    const cmd = `python ${runScript} ${codePath} ${evalPath} -o ${outDir} -c ${cfgPath} -i ${iterations}`;
    await execAsync(cmd, { cwd: root });
    return NextResponse.json({ ok: true, runId: outDir });
  } catch (err: any) {
    console.error('start evolution failed', err);
    return NextResponse.json({ ok: false, error: String(err) }, { status: 500 });
  }
}
