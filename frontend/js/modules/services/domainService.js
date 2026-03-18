import { getReviewDomain } from "../../api/request.js";
import { loadCases, loadDisputes } from "./casesService.js";
import { getDataCenterAssets } from "./dataCenterService.js";
import { syncWorkbenchSource, loadWorkbenchSource } from "./workbenchService.js";
import { syncRiskSource, loadRiskSource } from "./riskService.js";
import { listReportRecords } from "./reportsService.js";

export function applyServerSnapshot(state, snapshot, preferredCaseId = "") {
  if (!snapshot || typeof snapshot !== "object") return false;

  if (Array.isArray(snapshot.cases)) {
    state.cases = snapshot.cases;
  }
  if (Array.isArray(snapshot.disputes)) {
    state.disputes = snapshot.disputes;
  }
  if (Array.isArray(snapshot.report_actions)) {
    state.reportLogs = snapshot.report_actions;
  }
  if (snapshot.workbench && typeof snapshot.workbench === "object") {
    state.workbench = snapshot.workbench;
  }
  if (snapshot.risk && typeof snapshot.risk === "object") {
    state.riskSnapshot = snapshot.risk;
  }

  state.selectedCaseId = preferredCaseId || snapshot.selected_case_id || state.selectedCaseId || "";
  return true;
}

export async function loadDomainState(state, preferredCaseId = "") {
  const remote = await getReviewDomain(preferredCaseId || state.selectedCaseId || "");
  if (remote.ok && remote.data && remote.data.status === "success" && remote.data.snapshot) {
    applyServerSnapshot(state, remote.data.snapshot, preferredCaseId);
    state.resources = getDataCenterAssets();
    return true;
  }

  state.cases = loadCases();
  state.disputes = loadDisputes();
  state.resources = getDataCenterAssets();
  state.reportLogs = listReportRecords(state.selectedCaseId || "");
  return false;
}

export function syncDerivedState(state, forceLocal = false) {
  if (!forceLocal && state.workbench && state.riskSnapshot) {
    return;
  }
  state.workbench = syncWorkbenchSource({
    role: state.user.role,
    user: state.user,
    cases: state.cases,
    disputes: state.disputes
  });
  state.riskSnapshot = syncRiskSource({
    cases: state.cases,
    disputes: state.disputes
  });
}

export function restoreDerivedState(state) {
  state.workbench = loadWorkbenchSource(state.user.role);
  state.riskSnapshot = loadRiskSource();
}
