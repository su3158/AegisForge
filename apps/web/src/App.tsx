import * as Tabs from "@radix-ui/react-tabs";
import { Activity, AlertTriangle, Boxes, FileText, GitBranch, Languages, Moon, Play, Shield, Sun } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { loadConsoleData } from "./api";
import type { AegisData, Evidence, Project, Scan } from "./types";

type Theme = "light" | "dark";

export default function App() {
  const { t, i18n } = useTranslation();
  const [data, setData] = useState<AegisData | null>(null);
  const [theme, setTheme] = useState<Theme>(() =>
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light",
  );
  const [projectId, setProjectId] = useState("prj-customer-ai");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    void loadConsoleData().then(setData);
  }, []);

  if (!data) return <main className="shell loading">{t("loading")}</main>;

  const project = data.projects.find((item) => item.id === projectId) ?? data.projects[0];

  return (
    <main className="shell">
      <aside className="sidebar" aria-label={t("projects")}>
        <div className="brand">
          <Shield size={24} />
          <div>
            <strong>AegisForge</strong>
            <span>0.1.0-alpha</span>
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
            <button className="iconButton" onClick={() => i18n.changeLanguage(i18n.language === "ja" ? "en" : "ja")} aria-label={t("language")}>
              <Languages size={18} />
            </button>
            <button className="iconButton" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label={t("theme")}>
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button className="primary"><Play size={16} />{t("newScan")}</button>
          </div>
        </header>
        <Dashboard data={data} project={project} />
        <ProjectTabs data={data} project={project} />
      </section>
    </main>
  );
}

function ProjectList({ projects, selected, onSelect }: { projects: Project[]; selected: string; onSelect: (id: string) => void }) {
  return (
    <nav className="projectList">
      {projects.map((project) => (
        <button key={project.id} className={project.id === selected ? "project active" : "project"} onClick={() => onSelect(project.id)}>
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
      <Metric icon={<Activity />} label="Active scans" value={running} />
      <Metric icon={<AlertTriangle />} label="Critical" value={critical} tone="critical" />
      <Metric icon={<AlertTriangle />} label="High" value={high} tone="high" />
      <Metric icon={<Boxes />} label="Coverage" value={`${project.coverage}%`} />
    </section>
  );
}

function Metric({ icon, label, value, tone }: { icon: ReactNode; label: string; value: string | number; tone?: string }) {
  return (
    <div className={`metric ${tone ?? ""}`}>
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ProjectTabs({ data, project }: { data: AegisData; project: Project }) {
  const projectScans = data.scans.filter((scan) => scan.projectId === project.id);
  const findings = data.findings.filter((finding) => finding.projectId === project.id);
  const evidence = data.evidence.filter((item) => item.projectId === project.id);
  const chains = data.chains.filter((chain) => chain.projectId === project.id);

  return (
    <Tabs.Root defaultValue="overview" className="tabs">
      <Tabs.List className="tabList" aria-label="Project sections">
        {["overview", "targets", "scans", "findings", "evidence", "chains", "reports", "coverage", "settings"].map((tab) => (
          <Tabs.Trigger key={tab} value={tab}>{tab}</Tabs.Trigger>
        ))}
      </Tabs.List>
      <Tabs.Content value="overview"><ScanPanel scans={projectScans} /></Tabs.Content>
      <Tabs.Content value="targets"><DataTable rows={data.targets.filter((target) => target.projectId === project.id)} /></Tabs.Content>
      <Tabs.Content value="scans"><ScanPanel scans={projectScans} /></Tabs.Content>
      <Tabs.Content value="findings"><DataTable rows={findings} /></Tabs.Content>
      <Tabs.Content value="evidence"><EvidenceViewer evidence={evidence} /></Tabs.Content>
      <Tabs.Content value="chains"><ChainView chain={chains[0]} /></Tabs.Content>
      <Tabs.Content value="reports"><Empty title="Reports" text="HTML, Markdown, JSON, and SARIF exports are generated from stored evidence." /></Tabs.Content>
      <Tabs.Content value="coverage"><DataTable rows={data.coverage} /></Tabs.Content>
      <Tabs.Content value="settings"><Empty title="Project settings" text="Scope, modules, browser flows, and runtime overrides are edited here." /></Tabs.Content>
    </Tabs.Root>
  );
}

function ScanPanel({ scans }: { scans: Scan[] }) {
  return (
    <section className="split">
      <div>
        <h2>Scans</h2>
        {scans.map((scan) => (
          <article className="rowCard" key={scan.id}>
            <div>
              <strong>{scan.name}</strong>
              <span>{scan.phase} · {scan.activePlugin}</span>
            </div>
            <progress value={scan.progress} max={100} aria-label={`${scan.name} progress`} />
          </article>
        ))}
      </div>
      <ScanWizard />
    </section>
  );
}

function ScanWizard() {
  const steps = ["Target", "Profile", "Modules", "Safety", "AI/Budget", "Scope", "Start"];
  return (
    <aside className="panel">
      <h2>New Scan</h2>
      <ol className="wizard">{steps.map((step, index) => <li key={step}><span>{index + 1}</span>{step}</li>)}</ol>
    </aside>
  );
}

function EvidenceViewer({ evidence }: { evidence: Evidence[] }) {
  const [selected, setSelected] = useState(evidence[0]?.id);
  const item = evidence.find((entry) => entry.id === selected) ?? evidence[0];
  return (
    <section className="split">
      <DataTable rows={evidence} onSelect={setSelected} />
      {item && <Diff item={item} />}
    </section>
  );
}

function Diff({ item }: { item: Evidence }) {
  const before = item.before ?? "";
  const after = item.after;
  return (
    <article className="panel">
      <h2>{item.title}</h2>
      <p className="muted">{item.type} · SHA-256 {item.sha256}</p>
      <div className="diff">
        <pre><code>{before}</code></pre>
        <pre><code>{after}</code></pre>
      </div>
    </article>
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
        <p className="muted">{chain.status}</p>
        {chain.edges.map((edge) => <p key={`${edge.from}-${edge.to}`}>{edge.from} to {edge.to}: {edge.label}</p>)}
      </aside>
    </section>
  );
}

function DataTable<T extends object>({ rows, onSelect }: { rows: T[]; onSelect?: (id: string) => void }) {
  const columns = useMemo(() => Object.keys(rows[0] ?? {}).slice(0, 6), [rows]);
  if (!rows.length) return <Empty title="No records" text="Run a scan or create a target to populate this view." />;
  return (
    <div className="tableWrap">
      <table>
        <thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={String((row as { id?: unknown }).id)} onClick={() => onSelect?.(String((row as { id?: unknown }).id))}>
              {columns.map((column) => <td key={column}>{String((row as Record<string, unknown>)[column])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Empty({ title, text }: { title: string; text: string }) {
  return <section className="empty"><FileText size={20} /><strong>{title}</strong><span>{text}</span></section>;
}
