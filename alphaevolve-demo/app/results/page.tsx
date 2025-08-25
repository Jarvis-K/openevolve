export default function ResultsPage(){
  const rows = [
    { id: 'alg-1', fitness: 0.92, gen: 5, createdAt: '2024-12-08 14:30:22' },
    { id: 'alg-2', fitness: 0.89, gen: 4, createdAt: '2024-12-08 14:25:15' },
  ];
  return (
    <div className="p-4 space-y-2">
      <h1 className="text-xl font-semibold text-slate-900">Results Workbench</h1>
      <div className="rounded-2xl border border-slate-200 bg-white">
        <table className="w-full table-fixed">
          <thead><tr className="border-b border-slate-200 text-left text-xs text-slate-500">
            <th className="px-3 py-2">Algorithm ID</th><th className="px-3 py-2">Fitness</th><th className="px-3 py-2">Generation</th><th className="px-3 py-2">Created</th>
          </tr></thead>
          <tbody>
            {rows.map(r=> (
              <tr key={r.id} className="border-b border-slate-100">
                <td className="px-3 py-3 font-medium">{r.id}</td>
                <td className="px-3 py-3">{r.fitness.toFixed(2)}</td>
                <td className="px-3 py-3">Gen {r.gen}</td>
                <td className="px-3 py-3 text-xs text-slate-500">{r.createdAt}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
