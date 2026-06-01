const STORAGE_KEY = "autoresearch:activeOrchestratorRun";

export interface ActiveOrchestratorRun {
  instanceId: string;
  conversationId?: string | null;
  projectPath?: string;
}

export function setActiveOrchestratorRun(run: ActiveOrchestratorRun): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(run));
  } catch {
    /* ignore quota / private mode */
  }
}

export function getActiveOrchestratorRun(): ActiveOrchestratorRun | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as ActiveOrchestratorRun;
    if (!parsed?.instanceId) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function patchActiveOrchestratorRun(patch: Partial<ActiveOrchestratorRun>): ActiveOrchestratorRun | null {
  const current = getActiveOrchestratorRun();
  if (!current) return null;
  const next = { ...current, ...patch };
  setActiveOrchestratorRun(next);
  return next;
}

export function clearActiveOrchestratorRun(instanceId?: string): void {
  if (instanceId) {
    const current = getActiveOrchestratorRun();
    if (current?.instanceId !== instanceId) return;
  }
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

/** Match dashboard project path to a local conversation id. */
export function localConversationIdForProject(workspaceProject: string, taskProjectPath: string): string {
  const normalize = (p: string) => p.replace(/\\/g, "/").replace(/\/+$/, "") || ".";
  const workspace = normalize(workspaceProject);
  const task = normalize(taskProjectPath);
  if (task === workspace || task === ".") return "local";
  if (task.startsWith(workspace + "/")) {
    return `${task.slice(workspace.length + 1)}/local`;
  }
  return "local";
}

export function conversationIdForInstance(
  instance: { conversation_id?: string | null; cursor_agent_id?: string | null; project_path?: string },
  workspaceProject: string
): string | null {
  if (instance.conversation_id) return instance.conversation_id;
  if (instance.cursor_agent_id) return instance.cursor_agent_id;
  if (instance.project_path) {
    return localConversationIdForProject(workspaceProject, instance.project_path);
  }
  return null;
}

export function collectOrchestratorConversationIds(
  instances: Array<{
    conversation_id?: string | null;
    cursor_agent_id?: string | null;
    project_path?: string;
  }>,
  workspaceProject: string
): Set<string> {
  const ids = new Set<string>();
  for (const instance of instances) {
    const id = conversationIdForInstance(instance, workspaceProject);
    if (id) ids.add(id);
  }
  return ids;
}
