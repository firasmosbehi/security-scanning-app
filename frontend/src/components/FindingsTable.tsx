import { useState } from 'react'
import type { Finding, Severity } from '../types'

interface FindingsTableProps {
  findings: Finding[]
  severityFilter: Severity | 'all'
  onSeverityFilterChange: (s: Severity | 'all') => void
}

const SEVERITY_COLORS: Record<Severity | 'all', string> = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/50',
  high: 'bg-amber-500/20 text-amber-400 border-amber-500/50',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
  low: 'bg-slate-500/20 text-slate-400 border-slate-500/50',
  info: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50',
  all: '',
}

export function FindingsTable({ findings, severityFilter, onSeverityFilterChange }: FindingsTableProps) {
  const filtered =
    severityFilter === 'all'
      ? findings
      : findings.filter((f) => f.severity === severityFilter)

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {(['all', 'critical', 'high', 'medium', 'low', 'info'] as const).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSeverityFilterChange(s)}
            className={`
              px-3 py-1 rounded-md text-sm font-medium transition-colors
              ${severityFilter === s ? 'ring-2 ring-cyan-500' : ''}
              ${s === 'all' ? 'bg-slate-700 text-slate-300' : SEVERITY_COLORS[s]}
            `}
          >
            {s === 'all' ? `All (${findings.length})` : `${s} (${findings.filter((f) => f.severity === s).length})`}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-700">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700 bg-slate-800/50">
              <th className="px-4 py-3 text-left text-slate-400 font-medium">Severity</th>
              <th className="px-4 py-3 text-left text-slate-400 font-medium">Title</th>
              <th className="px-4 py-3 text-left text-slate-400 font-medium">File</th>
              <th className="px-4 py-3 text-left text-slate-400 font-medium">Scanner</th>
              <th className="px-4 py-3 text-left text-slate-400 font-medium">Details</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                  {findings.length === 0 ? 'No findings' : `No ${severityFilter} findings`}
                </td>
              </tr>
            ) : (
              filtered.map((f) => (
                <FindingRow key={f.id} finding={f} />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function FindingRow({ finding }: { finding: Finding }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <>
      <tr
        className="border-b border-slate-700/50 hover:bg-slate-800/30 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <td className="px-4 py-3">
          <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium border ${SEVERITY_COLORS[finding.severity]}`}>
            {finding.severity}
          </span>
        </td>
        <td className="px-4 py-3 text-slate-200 font-medium">{finding.title}</td>
        <td className="px-4 py-3 text-slate-400 font-mono text-xs">
          {finding.file_path ? (
            <span title={finding.file_path}>
              {finding.file_path.split('/').pop()}
              {finding.line_number != null && `:${finding.line_number}`}
            </span>
          ) : (
            '-'
          )}
        </td>
        <td className="px-4 py-3 text-slate-500">{finding.scanner}</td>
        <td className="px-4 py-3">
          <span className="text-cyan-400">{expanded ? '−' : '+'}</span>
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={5} className="px-4 py-3 bg-slate-900/50 border-b border-slate-700">
            <div className="space-y-2 text-sm">
              <p className="text-slate-400">{finding.message}</p>
              {finding.remediation && (
                <p className="text-emerald-400/90">
                  <span className="font-medium">Remediation:</span> {finding.remediation}
                </p>
              )}
              {finding.cve_id && (
                <p className="text-slate-500">CVE: {finding.cve_id}</p>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
