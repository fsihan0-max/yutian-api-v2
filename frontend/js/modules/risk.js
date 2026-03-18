import { renderRiskCenter } from "../components/risk.js";
import { syncRiskSource } from "./services/riskService.js";

export function renderRiskModule(state) {
  const payload = state.riskSnapshot || syncRiskSource({
    cases: state.cases,
    disputes: state.disputes
  });
  state.riskSnapshot = payload;
  renderRiskCenter(state, payload);
}
