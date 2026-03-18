import { renderReportCenter } from "../components/reports.js";

export function refreshReportCenterModule(state) {
  renderReportCenter(state, {
    records: state.reportLogs || [],
    evidenceTemplate: window.AppConfig.evidenceTemplate
  });
}
