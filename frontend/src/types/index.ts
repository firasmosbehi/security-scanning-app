export type TargetType =
  | 'code'
  | 'docker_image'
  | 'docker_compose'
  | 'kubernetes'
  | 'terraform'
  | 'ansible'
  | 'github_repo'

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type FindingCategory = 'security' | 'cost' | 'performance'

export interface Finding {
  id: string
  severity: Severity
  category: FindingCategory
  title: string
  message: string
  file_path: string | null
  line_number: number | null
  scanner: string
  remediation: string | null
  cve_id: string | null
}

export interface ScanResult {
  status: 'pending' | 'running' | 'completed' | 'failed'
  findings: Finding[]
  error?: string
}

export interface ScannersHealth {
  trivy: { available: boolean; path: string | null }
  checkov: { available: boolean; path: string | null }
  infracost: { available: boolean; path: string | null; api_key_set: boolean }
}
