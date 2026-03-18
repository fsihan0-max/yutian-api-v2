import {
  getSamples,
  postSample,
  postAnalyzeJson,
  postAnalyzeForm,
  geocodeCN
} from "../api/request.js";
import { initMap, renderOverlay } from "./map.js";
import {
  applyThemeButtons,
  renderSurveyAuxPanels,
  renderSampleList,
  setAnalyzeResult,
  readEvidenceFiles
} from "../components/survey.js";
import { formatNow } from "../components/utils.js";

const el = (id) => document.getElementById(id);

export function createSurveyModule(state, deps = {}) {
  const onBackendSync = deps.onBackendSync || (() => {});
  const goToMenu = deps.goToMenu || (() => {});

  function initSurveyTabs() {
    document.querySelectorAll("[data-survey-tab]").forEach((button) => {
      button.addEventListener("click", () => {
        const key = button.dataset.surveyTab;
        document.querySelectorAll("[data-survey-tab]").forEach((item) => item.classList.toggle("active", item === button));
        document.querySelectorAll(".subpage").forEach((page) => page.classList.toggle("active", page.dataset.subpage === key));
      });
    });
  }

  async function ensureMapReady() {
    if (state.mapApi) return;
    try {
      state.mapApi = await initMap({
        onAoiChange: (hasAoi) => {
          el("btnAnalyze").disabled = !hasAoi;
          renderSurveyAuxPanels(state);
        }
      });
      el("btnAnalyze").disabled = !state.mapApi.hasAoi();
    } catch (error) {
      alert(error.message || "地图初始化失败。");
    }
  }

  async function loadSamples() {
    const result = await getSamples();
    state.samples = result.ok ? (result.data.items || []) : [];
    renderSampleList(state.samples);
  }

  async function handleSearchLocation() {
    if (!state.mapApi) return;
    const query = el("searchInput").value.trim();
    if (!query) return;

    const result = await geocodeCN(query);
    if (!result.ok || !result.data.length) {
      alert("未找到位置。");
      return;
    }
    const location = result.data[0];
    state.mapApi.goToLonLat(parseFloat(location.lon), parseFloat(location.lat), 16);
  }

  async function handleDroneUpload(event) {
    if (!state.mapApi) return;
    const file = event.target.files[0];
    state.droneFile = file || null;
    if (!file) return;

    try {
      await state.mapApi.zoomToGeoTiff(file);
    } catch {
      state.droneFile = null;
      el("droneUploadInput").value = "";
      alert("GeoTIFF 解析失败。");
    }
  }

  async function handleAnalyze() {
    if (!state.selectedCase) {
      alert("请先在案件中心选择案件。");
      goToMenu("cases");
      return;
    }
    if (!state.mapApi || !state.mapApi.hasAoi()) {
      alert("请先绘制 AOI。");
      return;
    }

    const geometry = state.mapApi.getGeometryWgsJson();
    const areaMu = state.mapApi.getAreaMu();
    const cropMode = el("cropModeSelect").value;
    const modelMode = el("modelModeSelect").value;
    const operator = state.user.displayName || state.user.username;

    let result;
    if (state.droneFile) {
      const form = new FormData();
      form.append("file", state.droneFile);
      form.append("geometry", JSON.stringify(geometry));
      form.append("area_mu", areaMu);
      form.append("crop_mode", cropMode);
      form.append("model_mode", modelMode);
      form.append("case_id", state.selectedCase.id);
      form.append("operator", operator);
      result = await postAnalyzeForm(form);
    } else {
      result = await postAnalyzeJson({
        geometry: JSON.stringify(geometry),
        area_mu: areaMu,
        crop_mode: cropMode,
        model_mode: modelMode,
        case_id: state.selectedCase.id,
        operator
      });
    }

    const payload = result.data?.data || {};
    const nextCaseId = payload.case?.id || state.selectedCase.id;
    if (result.data?.snapshot) {
      onBackendSync(result.data.snapshot, nextCaseId);
    }

    if (!result.ok || !result.data || result.data.status !== "success") {
      alert(result.error || result.data?.message || "分析失败。");
      return;
    }

    const analysis = payload.analysis || {};
    state.currentAnalysis = analysis;
    setAnalyzeResult(analysis, state.selectedCase);
    renderSurveyAuxPanels(state);
    renderOverlay(state.currentAnalysis, state.currentTheme);
  }

  async function handleSaveSample(labelKey) {
    if (!state.currentAnalysis) {
      alert("请先执行分析。");
      return;
    }

    const payload = {
      label_key: labelKey,
      crop_mode: state.currentAnalysis.crop_mode,
      feature_vector: state.currentAnalysis.feature_vector,
      notes: el("sampleNoteInput").value.trim(),
      geometry: state.mapApi ? state.mapApi.getGeometryWgsJson() : null
    };

    const result = await postSample(payload);
    if (!result.ok) {
      alert(result.error || "样本保存失败");
      return;
    }
    loadSamples();
  }

  async function handleAddEvidence() {
    const files = Array.from(el("fieldPhotoInput").files || []);
    const note = el("fieldNoteInput").value.trim();
    if (!files.length && !note) {
      alert("请先上传照片或填写说明。");
      return;
    }

    try {
      const photoItems = await readEvidenceFiles(files, note);
      const items = photoItems.length
        ? photoItems
        : [{ title: `外业说明 ${formatNow()}`, detail: note || "外业证据", thumbnail: "" }];
      state.evidence = items.concat(state.evidence);
      el("fieldPhotoInput").value = "";
      el("fieldNoteInput").value = "";
      renderSurveyAuxPanels(state);
    } catch (error) {
      alert(error.message || "照片读取失败。");
    }
  }

  function bindEvents() {
    el("btnSearch").addEventListener("click", handleSearchLocation);
    el("droneUploadInput").addEventListener("change", handleDroneUpload);
    el("btnAnalyze").addEventListener("click", handleAnalyze);
    el("addFieldEvidenceBtn").addEventListener("click", handleAddEvidence);

    document.querySelectorAll("[data-theme-key]").forEach((button) => {
      button.addEventListener("click", () => {
        state.currentTheme = button.dataset.themeKey;
        applyThemeButtons(state.currentTheme);
        renderOverlay(state.currentAnalysis, state.currentTheme);
      });
    });

    document.querySelectorAll("[data-sample-label]").forEach((button) => {
      button.addEventListener("click", () => handleSaveSample(button.dataset.sampleLabel));
    });
  }

  function refreshPanels() {
    applyThemeButtons(state.currentTheme);
    renderSurveyAuxPanels(state);
  }

  return {
    initSurveyTabs,
    ensureMapReady,
    loadSamples,
    bindEvents,
    refreshPanels
  };
}
