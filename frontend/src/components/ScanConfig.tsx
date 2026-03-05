import type { TargetType } from '../types'

interface ScanConfigProps {
  targetType: TargetType
  onTargetTypeChange: (t: TargetType) => void
  dockerImageRef: string
  onDockerImageRefChange: (s: string) => void
  hasFile: boolean
}

const TARGET_OPTIONS: { value: TargetType; label: string; description: string }[] = [
  { value: 'code', label: 'Code', description: 'Source code, dependencies, Dockerfile' },
  { value: 'docker_image', label: 'Docker Image', description: 'Container image (e.g. nginx:latest)' },
  { value: 'docker_compose', label: 'Docker Compose', description: 'docker-compose.yml configs' },
  { value: 'kubernetes', label: 'Kubernetes', description: 'K8s manifests, Helm charts' },
  { value: 'terraform', label: 'Terraform', description: '.tf files and modules' },
  { value: 'ansible', label: 'Ansible', description: 'Playbooks and roles' },
]

export function ScanConfig({
  targetType,
  onTargetTypeChange,
  dockerImageRef,
  onDockerImageRefChange,
  hasFile,
}: ScanConfigProps) {
  const isImageScan = targetType === 'docker_image'

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-3">Target type</label>
        <div className="grid gap-2 sm:grid-cols-2">
          {TARGET_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onTargetTypeChange(opt.value)}
              className={`
                text-left px-4 py-3 rounded-lg border transition-colors
                ${targetType === opt.value ? 'border-cyan-500 bg-cyan-500/10 text-cyan-100' : 'border-slate-600 hover:border-slate-500 text-slate-300'}
              `}
            >
              <span className="font-medium">{opt.label}</span>
              <p className="text-xs text-slate-400 mt-1">{opt.description}</p>
            </button>
          ))}
        </div>
      </div>

      {isImageScan && (
        <div>
          <label htmlFor="docker-image" className="block text-sm font-medium text-slate-300 mb-2">
            Image reference
          </label>
          <input
            id="docker-image"
            type="text"
            value={dockerImageRef}
            onChange={(e) => onDockerImageRefChange(e.target.value)}
            placeholder="nginx:latest"
            className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-600 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
          />
        </div>
      )}

      {!isImageScan && !hasFile && (
        <p className="text-amber-400/90 text-sm">Upload a zip or config file to scan.</p>
      )}
    </div>
  )
}
