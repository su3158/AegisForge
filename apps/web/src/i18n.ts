import i18n from "i18next";
import { initReactI18next } from "react-i18next";

export const resources = {
  en: {
    translation: {
      dashboard: "Project Dashboard",
      loading: "Loading AegisForge",
      startScan: "Start scan",
      newScan: "New Scan",
      language: "Language",
      theme: "Theme",
      projects: "Projects",
      project: "Project",
      risk: "Risk",
      targets: "Targets",
      scans: "Scans",
      findings: "Findings",
      evidence: "Evidence",
      chains: "Chains",
      reports: "Reports",
      coverage: "Coverage",
      settings: "Settings",
    },
  },
  ja: {
    translation: {
      dashboard: "プロジェクトダッシュボード",
      loading: "AegisForgeを読み込み中",
      startScan: "スキャン開始",
      newScan: "新規スキャン",
      language: "言語",
      theme: "テーマ",
      projects: "プロジェクト",
      project: "プロジェクト",
      risk: "リスク",
      targets: "ターゲット",
      scans: "スキャン",
      findings: "検出事項",
      evidence: "証跡",
      chains: "チェーン",
      reports: "レポート",
      coverage: "カバレッジ",
      settings: "設定",
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;
