import { state, initState, bindSelectedCase } from "../utils/globalStore.js";
import { getHealth, postReview } from "../api/request.js";
import { createAppRouter } from "../utils/appRouter.js";
import { createSurveyModule } from "../modules/survey.js";
import { renderWorkbenchModule } from "../modules/workbench.js";
import { renderCasesModule } from "../modules/cases.js";
import { refreshReportCenterModule } from "../modules/reports.js";
import { renderRiskModule } from "../modules/risk.js";
import { renderDataCenterModule } from "../modules/data-center.js";
import { renderSettingsCenter } from "../components/settings.js";
import { openReportModal, closeReportModal, printReport } from "../components/reports.js";
import { formatNow } from "../components/utils.js";
import { applyServerSnapshot, loadDomainState, syncDerivedState } from "./services/domainService.js";

const el = (id) => document.getElementById(id);

let router;
let surveyModule;

async function updateHealthBadge() {
  const result = await getHealth();
  el("healthBadge").textContent = result.ok && result.data.status === "ok" ? "服务在线" : "服务异常";
}

function initHeader() {
  const roleName = window.AppConfig.roleLabel[state.user.role] || state.user.role;
  el("currentUserName").textContent = state.user.displayName || state.user.username;
  el("currentRoleName").textContent = roleName;
  el("roleLabel").textContent = roleName;
  el("dateBadge").textContent = formatNow();
  updateHealthBadge();
}

async function refreshDomain(caseId = "") {
  const loadedFromServer = await loadDomainState(state, caseId || state.selectedCaseId);
  bindSelectedCase(caseId || state.selectedCaseId);
  if (state.selectedCaseId && Array.isArray(state.reportLogs)) {
    state.reportLogs = state.reportLogs.filter((item) => item.caseId === state.selectedCaseId);
  }
  syncDerivedState(state, !loadedFromServer);
}

function refreshCurrentPage() {
  if (state.currentMenu === "workbench") renderWorkbenchModule(state, (menu) => router.go(menu));
  if (state.currentMenu === "cases") renderCasesModule(state, selectCase);
  if (state.currentMenu === "reports") refreshReportCenterModule(state);
  if (state.currentMenu === "risk") renderRiskModule(state);
  if (state.currentMenu === "data") renderDataCenterModule(state);
  if (state.currentMenu === "settings") renderSettingsCenter(state);
  if (state.currentMenu === "survey") {
    surveyModule.ensureMapReady();
    surveyModule.refreshPanels();
  }
}

function rerenderLinkedViews() {
  if (state.currentMenu === "cases") renderCasesModule(state, selectCase);
  if (state.currentMenu === "reports") refreshReportCenterModule(state);
  if (state.currentMenu === "risk") renderRiskModule(state);
  if (state.currentMenu === "workbench") renderWorkbenchModule(state, (menu) => router.go(menu));
}

function applySnapshotAndRerender(snapshot, caseId = "") {
  if (snapshot) {
    applyServerSnapshot(state, snapshot, caseId || state.selectedCaseId);
  }
  bindSelectedCase(caseId || state.selectedCaseId);
  if (state.selectedCaseId && Array.isArray(state.reportLogs)) {
    state.reportLogs = state.reportLogs.filter((item) => item.caseId === state.selectedCaseId);
  }
  syncDerivedState(state, false);
  rerenderLinkedViews();
}

function selectCase(caseId) {
  state.selectedCaseId = caseId;
  bindSelectedCase(caseId);
  state.reportLogs = [];
  refreshReportCenterModule(state);
  if (state.currentMenu === "cases") {
    renderCasesModule(state, selectCase);
  }
  refreshDomain(caseId).then(() => {
    rerenderLinkedViews();
  });
}

async function handleSubmitReview() {
  if (state.user.role === "surveyor") {
    alert("查勘员无复核权限。");
    return;
  }
  if (!state.selectedCase) {
    alert("请先选择案件。");
    return;
  }

  const payload = {
    case_id: state.selectedCase.id,
    reviewer: state.user.displayName || state.user.username,
    corrected_label: el("reviewLabelSelect").value,
    corrected_area_mu: el("reviewAreaInput").value,
    comment: el("reviewCommentInput").value
  };

  const result = await postReview(payload);
  if (!result.ok || !result.data || result.data.status !== "success") {
    alert(result.error || result.data?.message || "提交失败");
    return;
  }

  const nextCaseId = result.data?.data?.case?.id || state.selectedCase.id;
  applySnapshotAndRerender(result.data.snapshot, nextCaseId);

  el("reviewAreaInput").value = "";
  el("reviewCommentInput").value = "";

  alert(result.data.message || "复核已提交");
}

function bindGlobalEvents() {
  el("logoutBtn").addEventListener("click", () => {
    window.Auth.logout();
    window.location.href = "../login/index.html";
  });

  ["caseFilterTown", "caseFilterStatus", "caseFilterCrop"].forEach((id) => {
    el(id).addEventListener("change", () => renderCasesModule(state, selectCase));
  });

  el("submitReviewBtn").addEventListener("click", handleSubmitReview);

  el("generateFarmerReportBtn").addEventListener("click", () => {
    if (!state.selectedCase) {
      alert("请先选择案件。");
      return;
    }
    openReportModal(state, "farmer");
  });

  el("generateArchiveReportBtn").addEventListener("click", () => {
    if (!state.selectedCase) {
      alert("请先选择案件。");
      return;
    }
    openReportModal(state, "archive");
  });

  el("exportPdfBtn").addEventListener("click", () => {
    if (!state.selectedCase) {
      alert("请先选择案件。");
      return;
    }
    printReport(state);
  });

  el("closeReportModalBtn").addEventListener("click", closeReportModal);
  el("closeReportModalMask").addEventListener("click", closeReportModal);

  window.addEventListener("afterprint", () => {
    document.body.classList.remove("print-report-mode");
  });
}

function initRouter() {
  router = createAppRouter(state, (menuKey) => {
    state.currentMenu = menuKey;
    refreshCurrentPage();
  });
  window.addEventListener("hashchange", () => router.setFromHash());
}

export async function bootstrapApp() {
  const session = window.Auth.currentSession();
  if (!session) {
    window.location.href = "../login/index.html";
    return;
  }

  initState(session);
  await refreshDomain();
  initHeader();
  initRouter();

  surveyModule = createSurveyModule(state, {
    onBackendSync: (snapshot, caseId) => {
      applySnapshotAndRerender(snapshot, caseId);
    },
    goToMenu: (menu) => router.go(menu)
  });
  surveyModule.initSurveyTabs();
  surveyModule.bindEvents();
  surveyModule.loadSamples();

  bindGlobalEvents();
  router.setFromHash();
}
