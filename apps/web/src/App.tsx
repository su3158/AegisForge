import * as Tabs from "@radix-ui/react-tabs";
import {
  Activity,
  AlertTriangle,
  Boxes,
  Eye,
  FileText,
  GitBranch,
  KeyRound,
  Languages,
  Moon,
  Play,
  Plus,
  Shield,
  Square,
  Sun,
} from "lucide-react";
import type { FormEvent, ReactElement, ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { loadConsoleData } from "./api";
import type { AegisData, Evidence, Finding, ModuleName, Project, Scan, SecretRef, Target } from "./types";

type Theme = "light" | "dark";

const MODULES: ModuleName[] = ["http", "llm", "browser", "rag", "agent", "mcp"];
const CANCELLABLE_PHASES: Scan["phase"][] = ["running", "verifying", "analyzing", "reporting"];

export default function App() {
  const { t, i18n } = useTranslation();
  const [data, setData] = useState<AegisData | null>(null);
  const [theme, setTheme] = useState<Theme>(() =>
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light",
  );
  const [projectId, setProjectId] = useState("prj-customer-ai");
  const [activeTab, setActiveTab] = useState("overview");
  const [preferredTargetId, setPreferredTargetId] = useState("");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    void loadConsoleData().then(setData);
  }, []);

  if (!data) return <main className="shell loading">{t("loading")}</main>;

  const project = data.projects.find((item) => item.id === projectId) ?? data.projects[0];

  const updateData = (next: AegisData | ((current: AegisData) => AegisData)) => {
    setData((current) => {
      if (!current) return current;
      const value = typeof next === "function" ? next(current) : next;
      const exists = value.projects.some((item) => item.id === projectId);
      if (!exists) setProjectId(value.projects[0]?.id ?? "");
      return value;
    });
  };

  return (
    <main className="shell">
      <aside className="sidebar" aria-label={t("projects")}>
        <div className="brand">
          <Shield aria-hidden size={24} />
          <div>
            <strong>AegisForge</strong>
            <span>0.2.0-alpha</span>
          </div>
        </div>
        <ProjectList projects={data.projects} selected={project.id} onSelect={setProjectId} />
      </aside>
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{t("dashboard")}</p>
            <h1>{project.name}</h1>
          </div>
          <div className="toolbar">
            <button
              className="iconButton"
              type="button"
              onClick={() => i18n.changeLanguage(i18n.language === "ja" ? "en" : "ja")}
              aria-label={t("language")}
              title={t("language")}
            >
              <Languages size={18} />
            </button>
            <button
              className="iconButton"
              type="button"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              aria-label={t("theme")}
              title={t("theme")}
            >
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button className="primary" type="button" onClick={() => setActiveTab("scans")}>
              <Play size={16} />
              {t("newScan")}
            </button>
          </div>
        </header>
        <Dashboard data={data} project={project} />
        <ProjectTabs
          activeTab={activeTab}
          data={data}
          project={project}
          setActiveTab={setActiveTab}
          setData={updateData}
          setPreferredTargetId={setPreferredTargetId}
          preferredTargetId={preferredTargetId}
          labels={{
            attackChains: t("attackChains"),
            coverage: t("coverage"),
            dashboard: t("dashboard"),
            evidence: t("evidence"),
            findings: t("findings"),
            reports: t("reports"),
            scans: t("scans"),
            settings: t("settings"),
            targets: t("targets"),
          }}
        />
      </section>
    </main>
  );
}

function ProjectList({ projects, selected, onSelect }: { projects: Project[]; selected: string; onSelect: (id: string) => void }) {
  return (
    <nav className="projectList">
      {projects.map((project) => (
        <button
          key={project.id}
          className={project.id === selected ? "project active" : "project"}
          type="button"
          onClick={() => onSelect(project.id)}
        >
          <span>{project.name}</span>
          <small>{project.risk} risk</small>
        </button>
      ))}
    </nav>
  );
}

function Dashboard({ data, project }: { data: AegisData; project: Project }) {
  const projectFindings = data.findings.filter((finding) => finding.projectId === project.id);
  const running = data.scans.filter((scan) => scan.projectId === project.id && scan.phase === "running").length;
  const critical = projectFindings.filter((finding) => finding.severity === "critical").length;
  const high = projectFindings.filter((finding) => finding.severity === "high").length;
  return (
    <section className="metrics" aria-label="Project metrics">
      <Metric label="Active scans" value={running} />
      <Metric label="Critical" value={critical} tone="critical" />
      <Metric label="High" value={high} tone="high" />
      <Metric label="ASVS coverage" value={`${project.coverage}%`} />
    </section>
  );
}

function Metric({ label, value, tone }: { label: string; value: string | number; tone?: string }) {
  return (
    <div className={`metric ${tone ?? ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ProjectTabs({
  activeTab,
  data,
  project,
  setActiveTab,
  setData,
  setPreferredTargetId,
  preferredTargetId,
  labels,
}: {
  activeTab: string;
  data: AegisData;
  project: Project;
  setActiveTab: (tab: string) => void;
  setData: (data: AegisData | ((current: AegisData) => AegisData)) => void;
  setPreferredTargetId: (targetId: string) => void;
  preferredTargetId: string;
  labels: Record<string, string>;
}) {
  const targets = data.targets.filter((target) => target.projectId === project.id);
  const scans = data.scans.filter((scan) => scan.projectId === project.id);
  const findings = data.findings.filter((finding) => finding.projectId === project.id);
  const evidence = data.evidence.filter((item) => item.projectId === project.id);
  const secrets = data.secrets.filter((secret) => secret.projectId === project.id);
  const chains = data.chains.filter((chain) => chain.projectId === project.id);

  return (
    <Tabs.Root value={activeTab} onValueChange={setActiveTab} className="tabs">
      <Tabs.List className="tabList" aria-label="Project sections">
        {[
          ["overview", labels.dashboard],
          ["targets", labels.targets],
          ["scans", labels.scans],
          ["findings", labels.findings],
          ["evidence", labels.evidence],
          ["chains", labels.attackChains],
          ["reports", labels.reports],
          ["coverage", labels.coverage],
          ["settings", labels.settings],
        ].map(([value, label]) => (
          <Tabs.Trigger key={value} value={value}>
            {label}
          </Tabs.Trigger>
        ))}
      </Tabs.List>
      <Tabs.Content value="overview">
        <Overview project={project} scans={scans} findings={findings} targets={targets} />
      </Tabs.Content>
      <Tabs.Content value="targets">
        <TargetsView
          data={data}
          project={project}
          targets={targets}
          setData={setData}
          setPreferredTargetId={setPreferredTargetId}
        />
      </Tabs.Content>
      <Tabs.Content value="scans">
        <ScansView
          data={data}
          project={project}
          scans={scans}
          targets={targets}
          setData={setData}
          preferredTargetId={preferredTargetId}
        />
      </Tabs.Content>
      <Tabs.Content value="findings">
        <FindingsView findings={findings} evidence={evidence} />
      </Tabs.Content>
      <Tabs.Content value="evidence">
        <EvidenceViewer evidence={evidence} />
      </Tabs.Content>
      <Tabs.Content value="chains">
        <ChainView chain={chains[0]} />
      </Tabs.Content>
      <Tabs.Content value="reports">
        <ReportsView findings={findings} evidence={evidence} />
      </Tabs.Content>
      <Tabs.Content value="coverage">
        <CoverageView rows={data.coverage} />
      </Tabs.Content>
      <Tabs.Content value="settings">
        <SettingsView data={data} project={project} secrets={secrets} setData={setData} />
      </Tabs.Content>
    </Tabs.Root>
  );
}

function Overview({ project, scans, findings, targets }: { project: Project; scans: Scan[]; findings: Finding[]; targets: Target[] }) {
  return (
    <section className="overviewGrid">
      <Panel title="Current project">
        <dl className="facts">
          <dt>Owner</dt>
          <dd>{project.owner}</dd>
          <dt>Targets</dt>
          <dd>{targets.length}</dd>
          <dt>Last scan</dt>
          <dd>{project.lastScan}</dd>
        </dl>
      </Panel>
      <Panel title="Recent scan">
        <ScanRows scans={scans.slice(0, 2)} />
      </Panel>
      <Panel title="Open findings">
        <ul className="plainList">
          {findings.slice(0, 3).map((finding) => (
            <li key={finding.id}>
              <SeverityBadge value={finding.severity} />
              <span>{finding.title}</span>
            </li>
          ))}
        </ul>
      </Panel>
    </section>
  );
}

function TargetsView({
  data,
  project,
  targets,
  setData,
  setPreferredTargetId,
}: {
  data: AegisData;
  project: Project;
  targets: Target[];
  setData: (data: AegisData | ((current: AegisData) => AegisData)) => void;
  setPreferredTargetId: (targetId: string) => void;
}) {
  return (
    <section className="split">
      <div>
        <h2>{project.name} targets</h2>
        <DataTable rows={targets} columns={["name", "type", "endpoint", "scope", "health", "scopeConfirmed"]} />
      </div>
      <TargetForm
        projectId={project.id}
        onCreate={(target) => {
          setPreferredTargetId(target.id);
          setData((current) => ({ ...current, targets: [target, ...current.targets] }));
        }}
      />
    </section>
  );
}

function TargetForm({
  projectId,
  onCreate,
}: {
  projectId: string;
  onCreate: (target: Target) => void;
}) {
  const [name, setName] = useState("Staging chat");
  const [endpoint, setEndpoint] = useState("http://localhost:8001/v1/chat/completions");
  const [type, setType] = useState<Target["type"]>("llm");
  const scope = useMemo(() => scopeFromEndpoint(endpoint), [endpoint]);

  const create = () => {
    const target: Target = {
      id: `t-${Date.now()}`,
      projectId,
      name,
      type,
      endpoint,
      scope: "safe",
      health: "unknown",
      allowedHosts: scope.host ? [scope.host] : [],
      allowedPorts: scope.port ? [scope.port] : [],
      scopeConfirmed: true,
    };
    onCreate(target);
  };

  return (
    <form className="panel formStack" onSubmit={(event) => event.preventDefault()} aria-label="Add target">
      <h2>Add target</h2>
      <Field label="Target name">
        <input id="target-name" name="targetName" value={name} onChange={(event) => setName(event.target.value)} />
      </Field>
      <Field label="Target endpoint">
        <input id="target-endpoint" name="targetEndpoint" value={endpoint} onChange={(event) => setEndpoint(event.target.value)} />
      </Field>
      <Field label="Target type">
        <select id="target-type" name="targetType" value={type} onChange={(event) => setType(event.target.value as Target["type"])}>
          {["web", "api", ...MODULES].map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
      </Field>
      <div className="scopeBox">
        <strong>Scope candidate</strong>
        <span>{scope.host ? `${scope.host}:${scope.port}` : "Invalid URL"}</span>
      </div>
      <label className="checkLine" htmlFor="scope-confirmed">
        <input id="scope-confirmed" name="scopeConfirmed" type="checkbox" required />
        Confirm this scope before scanning
      </label>
      <button className="primary" type="button" onClick={create} disabled={!scope.host}>
        <Plus size={16} />
        Add target
      </button>
    </form>
  );
}

function ScansView({
  data,
  project,
  scans,
  targets,
  setData,
  preferredTargetId,
}: {
  data: AegisData;
  project: Project;
  scans: Scan[];
  targets: Target[];
  setData: (data: AegisData | ((current: AegisData) => AegisData)) => void;
  preferredTargetId: string;
}) {
  const [cancelNotice, setCancelNotice] = useState("");
  const cancel = (scanId: string) => {
    setData((current) => ({
      ...current,
      scans: current.scans.map((scan) =>
        scan.id === scanId ? { ...scan, phase: "cancelled", activePlugin: "cancelled" } : scan,
      ),
    }));
    setCancelNotice("cancelled");
  };

  return (
    <section className="split">
      <div>
        <h2>{project.name} scans</h2>
        <ScanRows scans={scans} onCancel={cancel} />
        {cancelNotice ? <p className="muted" role="status">{cancelNotice}</p> : null}
      </div>
      <ScanWizard
        projectId={project.id}
        targets={targets}
        preferredTargetId={preferredTargetId}
        onStart={(scan) => setData((current) => ({ ...current, scans: [scan, ...current.scans] }))}
      />
    </section>
  );
}

function ScanRows({ scans, onCancel }: { scans: Scan[]; onCancel?: (scanId: string) => void }) {
  if (!scans.length) return <Empty title="No scans" text="Start a quick scan after confirming target scope." />;
  return (
    <div className="rowList">
      {scans.map((scan) => (
        <article className="rowCard" key={scan.id}>
          <div>
            <strong>{scan.name}</strong>
            <span>
              {scan.phase} · {scan.activePlugin} · {scan.requests} requests
            </span>
            <progress value={scan.progress} max={100} aria-label={`${scan.name} progress`} />
          </div>
          {onCancel && CANCELLABLE_PHASES.includes(scan.phase) ? (
            <button className="secondary" type="button" onClick={() => onCancel(scan.id)}>
              <Square size={14} />
              Cancel scan
            </button>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function ScanWizard({
  projectId,
  targets,
  preferredTargetId,
  onStart,
}: {
  projectId: string;
  targets: Target[];
  preferredTargetId: string;
  onStart: (scan: Scan) => void;
}) {
  const [targetId, setTargetId] = useState(targets[0]?.id ?? "");
  const [profile, setProfile] = useState<Scan["profile"]>("quick");
  const [safety, setSafety] = useState<Scan["safety"]>("safe");
  const [budget, setBudget] = useState("5");
  const [consent, setConsent] = useState(false);
  const [scopeConfirmed, setScopeConfirmed] = useState(false);
  const preferredExists = targets.some((target) => target.id === preferredTargetId);
  const selected = targets.find((target) => target.id === targetId);
  const enabled = Boolean(selected?.scopeConfirmed || scopeConfirmed) && (profile !== "standard" || consent);

  useEffect(() => {
    // Hidden tabs mount early; prefer the most recently created target when available.
    if (preferredExists) setTargetId(preferredTargetId);
  }, [preferredExists, preferredTargetId]);

  const start = (event: FormEvent) => {
    event.preventDefault();
    if (!selected || !enabled) return;
    onStart({
      id: `scan-${Date.now()}`,
      projectId,
      targetId: selected.id,
      name: `${profile} scan for ${selected.name}`,
      profile,
      safety,
      phase: "running",
      progress: 8,
      activePlugin: profile === "standard" ? "llm.prompt_injection.realistic" : "http.baseline",
      requests: 1,
      aiCostUsd: Number(budget) > 0 ? 0.01 : 0,
      findings: 0,
      errors: [],
    });
  };

  return (
    <form className="panel formStack" aria-label="Scan wizard" onSubmit={start}>
      <h2>Scan wizard</h2>
      <Field label="Scan target">
        <select id="scan-target" name="scanTarget" value={targetId} onChange={(event) => setTargetId(event.target.value)}>
          {targets.map((target) => (
            <option key={target.id} value={target.id}>
              {target.name}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Scan profile">
        <select id="scan-profile" name="scanProfile" value={profile} onChange={(event) => setProfile(event.target.value as Scan["profile"])}>
          <option value="quick">quick</option>
          <option value="standard">standard</option>
        </select>
      </Field>
      <Field label="Safety profile">
        <select id="safety-profile" name="safetyProfile" value={safety} onChange={(event) => setSafety(event.target.value as Scan["safety"])}>
          <option value="safe">safe</option>
          <option value="standard">standard</option>
          <option value="intrusive">intrusive</option>
        </select>
      </Field>
      <fieldset className="fieldSet">
        <legend>Modules</legend>
        {MODULES.map((module) => (
          <label className="checkLine" key={module} htmlFor={`module-${module}`}>
            <input
              id={`module-${module}`}
              name="modules"
              type="checkbox"
              defaultChecked={["http", "llm", "browser"].includes(module)}
            />
            {module}
          </label>
        ))}
      </fieldset>
      <Field label="AI budget">
        <input id="ai-budget" name="aiBudget" min="0" type="number" value={budget} onChange={(event) => setBudget(event.target.value)} />
      </Field>
      <label className="checkLine" htmlFor="standard-consent">
        <input id="standard-consent" name="standardConsent" type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
        Allow standard probes against local/demo fixtures
      </label>
      <label className="checkLine" htmlFor="scan-scope-confirmed">
        <input
          id="scan-scope-confirmed"
          name="scanScopeConfirmed"
          type="checkbox"
          checked={scopeConfirmed}
          onChange={(event) => setScopeConfirmed(event.target.checked)}
        />
        Confirm scope for this scan
      </label>
      <button className="primary" type="submit" disabled={!enabled}>
        <Play size={16} />
        Start scan
      </button>
    </form>
  );
}

function FindingsView({ findings, evidence }: { findings: Finding[]; evidence: Evidence[] }) {
  const [selectedId, setSelectedId] = useState(findings[0]?.id);
  const finding = findings.find((item) => item.id === selectedId) ?? findings[0];
  const linked = evidence.filter((item) => finding?.evidenceIds.includes(item.id));
  return (
    <section className="split">
      <DataTable rows={findings} columns={["id", "severity", "status", "confidence", "category", "title"]} onSelect={setSelectedId} />
      {finding ? (
        <Panel title={finding.title}>
          <p className="muted">{finding.target}</p>
          <div className="badgeRow">
            <SeverityBadge value={finding.severity} />
            <span className="badge">{finding.status}</span>
            <span className="badge">{finding.confidence}</span>
          </div>
          <h3>Framework mapping</h3>
          <ul className="plainList">{finding.frameworks.map((item) => <li key={item}>{item}</li>)}</ul>
          <h3>Evidence</h3>
          <ul className="plainList">{linked.map((item) => <li key={item.id}>{item.id} · {item.title}</li>)}</ul>
        </Panel>
      ) : null}
    </section>
  );
}

function EvidenceViewer({ evidence }: { evidence: Evidence[] }) {
  const [selected, setSelected] = useState(evidence[0]?.id);
  const [showRaw, setShowRaw] = useState(false);
  const [password, setPassword] = useState("");
  const item = evidence.find((entry) => entry.id === selected) ?? evidence[0];
  return (
    <section className="split">
      <DataTable rows={evidence} columns={["id", "type", "title", "redacted", "sha256"]} onSelect={setSelected} />
      {item ? (
        <article className="panel" aria-label="Evidence detail">
          <div className="panelHeader">
            <h2>{item.title}</h2>
            <span className="badge">{item.type}</span>
          </div>
          <p className="muted">SHA-256 {item.sha256}</p>
          <div className="diff">
            <pre><code>{item.before ?? ""}</code></pre>
            <pre><code>{showRaw ? item.after : redactText(item.after)}</code></pre>
          </div>
          <form className="inlineForm" onSubmit={(event) => { event.preventDefault(); setShowRaw(password.length > 0); }}>
            <Field label="Admin password">
              <input id="admin-password" name="adminPassword" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </Field>
            <button className="secondary" type="submit">
              <Eye size={14} />
              Reveal raw evidence
            </button>
          </form>
        </article>
      ) : null}
    </section>
  );
}

function ChainView({ chain }: { chain: AegisData["chains"][number] | undefined }) {
  if (!chain) return <Empty title="Attack Chains" text="No chain candidates yet." />;
  return (
    <section className="chain">
      <div className="graph" aria-label={chain.title}>
        {chain.nodes.map((node, index) => (
          <div className="node" key={node.id} style={{ gridColumn: index + 1 }}>
            <GitBranch size={16} />
            <strong>{node.label}</strong>
            <span>{node.kind}</span>
          </div>
        ))}
      </div>
      <aside className="panel">
        <h2>{chain.title}</h2>
        <p className="muted">{chain.status} · AI priority candidate</p>
        {chain.edges.map((edge) => (
          <p key={`${edge.from}-${edge.to}`}>{edge.from} to {edge.to}: {edge.label}</p>
        ))}
      </aside>
    </section>
  );
}

function CoverageView({ rows }: { rows: AegisData["coverage"] }) {
  return (
    <section className="split">
      <DataTable rows={rows} columns={["id", "framework", "status", "title"]} />
      <Panel title="ASVS 5.0 L2">
        <div className="coverageBars">
          {["pass", "fail", "manual", "not_tested"].map((status) => {
            const count = rows.filter((row) => row.status === status).length;
            return (
              <div key={status}>
                <span>{status}</span>
                <strong>{count}</strong>
              </div>
            );
          })}
        </div>
      </Panel>
    </section>
  );
}

function ReportsView({ findings, evidence }: { findings: Finding[]; evidence: Evidence[] }) {
  return (
    <Panel title="Report exports">
      <div className="buttonGrid">
        {["HTML", "Markdown", "JSON", "SARIF"].map((format) => (
          <button className="secondary" type="button" key={format}>{format}</button>
        ))}
      </div>
      <p className="muted">{findings.length} findings and {evidence.length} redacted evidence records ready for export.</p>
    </Panel>
  );
}

function SettingsView({
  data,
  project,
  secrets,
  setData,
}: {
  data: AegisData;
  project: Project;
  secrets: SecretRef[];
  setData: (data: AegisData) => void;
}) {
  const [name, setName] = useState("staging-openai-key");
  const [kind, setKind] = useState<SecretRef["kind"]>("ai_provider");

  const addSecret = (event: FormEvent) => {
    event.preventDefault();
    setData({
      ...data,
      secrets: [
        { id: `sec-${Date.now()}`, projectId: project.id, name, kind, createdAt: "Today", lastUsed: "Never" },
        ...data.secrets,
      ],
    });
  };

  return (
    <section className="split">
      <div>
        <h2>Encrypted secrets</h2>
        <DataTable rows={secrets} columns={["name", "kind", "createdAt", "lastUsed"]} />
      </div>
      <form className="panel formStack" aria-label="Add secret" onSubmit={addSecret}>
        <h2>Add secret</h2>
        <Field label="Secret name">
          <input id="secret-name" name="secretName" value={name} onChange={(event) => setName(event.target.value)} />
        </Field>
        <Field label="Secret value">
          <input id="secret-value" name="secretValue" type="password" placeholder="Encrypted by API before storage" />
        </Field>
        <Field label="Secret kind">
          <select id="secret-kind" name="secretKind" value={kind} onChange={(event) => setKind(event.target.value as SecretRef["kind"])}>
            <option value="ai_provider">ai_provider</option>
            <option value="target_auth">target_auth</option>
            <option value="browser_login">browser_login</option>
          </select>
        </Field>
        <button className="primary" type="submit">
          <KeyRound size={16} />
          Add secret
        </button>
      </form>
    </section>
  );
}

function DataTable<T extends object>({
  rows,
  columns,
  onSelect,
}: {
  rows: T[];
  columns: Array<keyof T & string>;
  onSelect?: (id: string) => void;
}) {
  if (!rows.length) return <Empty title="No records" text="Create a target or run a scan to populate this view." />;
  return (
    <div className="tableWrap">
      <table>
        <thead>
          <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={String((row as { id?: unknown }).id ?? index)} onClick={() => onSelect?.(String((row as { id?: unknown }).id))}>
              {columns.map((column) => (
                <td key={column}>{formatCell((row as Record<string, unknown>)[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <article className="panel">
      <h2>{title}</h2>
      {children}
    </article>
  );
}

function Field({ label, children }: { label: string; children: ReactElement<{ id?: string }> }) {
  const id = children.props.id ?? label.toLowerCase().replaceAll(" ", "-");
  return (
    <label className="field" htmlFor={id}>
      <span>{label}</span>
      {children}
    </label>
  );
}

function SeverityBadge({ value }: { value: Finding["severity"] }) {
  return <span className={`badge severity ${value}`}>{value}</span>;
}

function Empty({ title, text }: { title: string; text: string }) {
  return (
    <section className="empty">
      <FileText size={20} />
      <strong>{title}</strong>
      <span>{text}</span>
    </section>
  );
}

function scopeFromEndpoint(endpoint: string): { host: string; port: number } {
  try {
    const url = new URL(endpoint);
    return { host: url.hostname, port: Number(url.port || (url.protocol === "https:" ? 443 : 80)) };
  } catch {
    return { host: "", port: 0 };
  }
}

function formatCell(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "boolean") return value ? "yes" : "no";
  return String(value ?? "");
}

function redactText(value: string): string {
  // Keep UI safe-by-default even when demo/API evidence contains realistic probe text.
  return value.replace(/user_id|order|ticket|Ignore previous rules/gi, "[REDACTED]");
}
