import { useCallback, useEffect, useState } from 'react'
import { createScan, getScan, getScannersHealth } from './api/scans'
import { FileUpload } from './components/FileUpload'
import { FindingsTable } from './components/FindingsTable'
import { ScanConfig } from './components/ScanConfig'
import { ScanStatus } from './components/ScanStatus'
import type { Finding, ScanResult, Severity, TargetType } from './types'

const POLL_INTERVAL_MS = 1500

export default function App() {
  const [targetType, setTargetType] = useState<TargetType>('code')
  const [dockerImageRef, setDockerImageRef] = useState('')
  const [githubUrl, setGithubUrl] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [scanId, setScanId] = useState<string | null>(null)
  const [scanResult, setScanResult] = useState<ScanResult | null>(null)
  const [severityFilter, setSeverityFilter] = useState<Severity | 'all'>('all')
  const [error, setError] = useState<string | null>(null)
  const [scannerHealth, setScannerHealth] = useState<Awaited<ReturnType<typeof getScannersHealth>> | null>(null)

  useEffect(() => {
    getScannersHealth().then(setScannerHealth).catch(() => setScannerHealth(null))
  }, [])

  useEffect(() => {
    if (!scanId) return
    const interval = setInterval(async () => {
      try {
        const res = await getScan(scanId)
        setScanResult({
          status: res.status as ScanResult['status'],
          findings: res.findings as Finding[],
          error: res.error,
        })
        if (res.status === 'completed' || res.status === 'failed') {
          clearInterval(interval)
        }
      } catch {
        clearInterval(interval)
      }
    }, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [scanId])

  const handleStartScan = useCallback(async () => {
    setError(null)
    const isImageScan = targetType === 'docker_image'
    const isGithubScan = targetType === 'github_repo'
    if (isImageScan && !dockerImageRef.trim()) {
      setError('Enter a Docker image reference (e.g. nginx:latest or ghcr.io/owner/img:tag)')
      return
    }
    if (isGithubScan && !githubUrl.trim()) {
      setError('Enter a GitHub repo URL (e.g. https://github.com/user/repo or user/repo)')
      return
    }
    if (!isImageScan && !isGithubScan && !file) {
      setError('Upload a file to scan')
      return
    }

    try {
      const formData = new FormData()
      formData.set('target_type', targetType)
      if (isImageScan) {
        formData.set('docker_image_ref', dockerImageRef.trim())
      } else if (isGithubScan) {
        formData.set('github_url', githubUrl.trim())
      } else if (file) {
        formData.append('file', file)
      }
      const { scan_id } = await createScan(formData)
      setScanId(scan_id)
      setScanResult({ status: 'pending', findings: [] })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start scan')
    }
  }, [targetType, dockerImageRef, githubUrl, file])

  const handleNewScan = useCallback(() => {
    setScanId(null)
    setScanResult(null)
    setFile(null)
    setGithubUrl('')
    setError(null)
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <header className="mb-10">
          <h1 className="text-2xl font-bold text-cyan-400">Security Scanner</h1>
          <p className="text-slate-400 mt-1">
            Scan code, Docker images, and infrastructure configs for security, cost, and performance issues
          </p>
          {scannerHealth && (
            <div className="mt-4 flex gap-4 text-xs">
              <span className={scannerHealth.trivy.available ? 'text-emerald-400' : 'text-red-400'}>
                Trivy {scannerHealth.trivy.available ? '✓' : '✗'}
              </span>
              <span className={scannerHealth.checkov.available ? 'text-emerald-400' : 'text-red-400'}>
                Checkov {scannerHealth.checkov.available ? '✓' : '✗'}
              </span>
              <span className={scannerHealth.infracost.available ? 'text-emerald-400' : 'text-slate-500'}>
                Infracost {scannerHealth.infracost.available ? '✓' : '(optional)'}
              </span>
            </div>
          )}
        </header>

        {!scanResult || scanResult.status === 'pending' || scanResult.status === 'running' ? (
          <div className="space-y-8">
            <div className="rounded-xl bg-slate-900/50 border border-slate-700 p-6">
              <h2 className="text-lg font-semibold text-slate-200 mb-4">Scan configuration</h2>
              <ScanConfig
                targetType={targetType}
                onTargetTypeChange={setTargetType}
                dockerImageRef={dockerImageRef}
                onDockerImageRefChange={setDockerImageRef}
                githubUrl={githubUrl}
                onGithubUrlChange={setGithubUrl}
                hasFile={!!file}
              />
            </div>

            {targetType !== 'docker_image' && targetType !== 'github_repo' && (
              <div className="rounded-xl bg-slate-900/50 border border-slate-700 p-6">
                <h2 className="text-lg font-semibold text-slate-200 mb-4">Upload</h2>
                <FileUpload
                  onFileSelect={(f) => {
                    setFile(f)
                    setError(null)
                  }}
                />
                {file && <p className="mt-3 text-slate-400 text-sm">Selected: {file.name}</p>}
              </div>
            )}

            {scanResult && (scanResult.status === 'pending' || scanResult.status === 'running') && (
              <div className="rounded-xl bg-slate-900/50 border border-slate-700 p-6">
                <ScanStatus status={scanResult.status} error={scanResult.error} />
              </div>
            )}

            {error && <p className="text-red-400">{error}</p>}

            <button
              type="button"
              onClick={handleStartScan}
              disabled={
                scanResult?.status === 'running' ||
                (targetType === 'docker_image' ? !dockerImageRef.trim() :
                  targetType === 'github_repo' ? !githubUrl.trim() : !file)
              }
              className="px-6 py-3 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {scanResult?.status === 'running' ? 'Scanning…' : 'Run scan'}
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <ScanStatus status={scanResult.status} error={scanResult.error} />
              <button
                type="button"
                onClick={handleNewScan}
                className="px-4 py-2 rounded-lg border border-slate-600 hover:border-cyan-500 text-slate-300"
              >
                New scan
              </button>
            </div>

            <FindingsTable
              findings={scanResult.findings}
              severityFilter={severityFilter}
              onSeverityFilterChange={setSeverityFilter}
            />
          </div>
        )}
      </div>
    </div>
  )
}
