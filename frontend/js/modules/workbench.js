import { renderWorkbench } from "../components/workbench.js";
import { syncWorkbenchSource } from "./services/workbenchService.js";

export function renderWorkbenchModule(state, goToMenu) {
  const payload = state.workbench || syncWorkbenchSource({
    role: state.user.role,
    user: state.user,
    cases: state.cases,
    disputes: state.disputes
  });
  state.workbench = payload;
  renderWorkbench(state, goToMenu, payload);
}
