export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type FindingStatus = "confirmed" | "candidate" | "draft" | "fixed";
export type ScanPhase =
  | "created"
  | "validating"
  | "discovering"
  | "planning"
  | "running"
  | "verifying"
  | "analyzing"
  | "reporting"
  | "completed"
  | "cancelled"
  | "failed";

export type ModuleName = "http" | "llm" | "browser" | "rag" | "agent" | "mcp";

export interface Project {
  id: string;
  name: string;
  owner: string;
  risk: "critical" | "high" | "medium" | "low";
  targets: number;
  scans: number;
  coverage: number;
  lastScan: string;
}

export interface Target {
  id: string;
  projectId: string;
  name: string;
  type: "web" | "api" | ModuleName;
  endpoint: string;
  scope: "safe" | "standard" | "intrusive";
  health: "healthy" | "degraded" | "unknown";
  allowedHosts: string[];
  allowedPorts: number[];
  scopeConfirmed: boolean;
}

export interface Scan {
  id: string;
  projectId: string;
  targetId: string;
  name: string;
  profile: "quick" | "standard" | "deep";
  safety: "safe" | "standard" | "intrusive";
  phase: ScanPhase;
  progress: number;
  activePlugin: string;
  requests: number;
  aiCostUsd: number;
  findings: number;
  errors: string[];
}

export interface SecretRef {
  id: string;
  projectId: string;
  name: string;
  kind: "ai_provider" | "target_auth" | "browser_login";
  createdAt: string;
  lastUsed: string;
}

export interface Finding {
  id: string;
  projectId: string;
  title: string;
  severity: Severity;
  status: FindingStatus;
  confidence: "low" | "medium" | "high" | "confirmed";
  category: string;
  target: string;
  frameworks: string[];
  evidenceIds: string[];
}

export interface Evidence {
  id: string;
  projectId: string;
  type: "HTTP_REQUEST" | "HTTP_RESPONSE" | "PROMPT" | "COMPLETION" | "TOOL_CALL" | "AGENT_TRACE" | "CONFIGURATION";
  title: string;
  timestamp: string;
  sha256: string;
  redacted: boolean;
  before?: string;
  after: string;
  language: "text" | "json" | "http";
}

export interface ChainNode {
  id: string;
  label: string;
  kind: "web" | "api" | "rag" | "llm" | "agent" | "mcp" | "external";
  findingId?: string;
}

export interface AttackChain {
  id: string;
  projectId: string;
  title: string;
  status: "candidate" | "confirmed";
  nodes: ChainNode[];
  edges: Array<{ from: string; to: string; label: string }>;
}

export interface CoverageControl {
  id: string;
  framework: string;
  title: string;
  status: "pass" | "fail" | "manual" | "not_tested" | "na";
}

export interface AegisData {
  projects: Project[];
  targets: Target[];
  scans: Scan[];
  secrets: SecretRef[];
  findings: Finding[];
  evidence: Evidence[];
  chains: AttackChain[];
  coverage: CoverageControl[];
}
