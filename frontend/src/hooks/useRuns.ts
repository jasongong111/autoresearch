import { useCallback, useEffect, useState } from "react";
import {
  createConfig,
  deleteConfig,
  fetchConfigs,
  fetchInstances,
  startRun,
  stopRun,
  subscribeEvents,
  updateConfig,
  validateConfig,
} from "../api";
import type { RunConfig, RunInstance } from "../types";

export function useRuns() {
  const [configs, setConfigs] = useState<RunConfig[]>([]);
  const [instances, setInstances] = useState<RunInstance[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [cfgs, insts] = await Promise.all([fetchConfigs(), fetchInstances()]);
      setConfigs(cfgs);
      setInstances(insts);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    const unsub = subscribeEvents((event) => {
      if (
        event.type === "run_started" ||
        event.type === "run_stopped" ||
        event.type === "run_updated" ||
        event.type === "run_output"
      ) {
        refresh();
      }
    });
    return unsub;
  }, [refresh]);

  const saveConfig = useCallback(
    async (data: Partial<RunConfig>) => {
      if (data.id) {
        const cfg = await updateConfig(data.id, data);
        setConfigs((prev) => prev.map((c) => (c.id === cfg.id ? cfg : c)));
        return cfg;
      }
      const cfg = await createConfig(data);
      setConfigs((prev) => [...prev, cfg]);
      return cfg;
    },
    []
  );

  const removeConfig = useCallback(async (configId: string) => {
    await deleteConfig(configId);
    setConfigs((prev) => prev.filter((c) => c.id !== configId));
  }, []);

  const runConfig = useCallback(async (configId: string) => {
    const instance = await startRun(configId);
    setInstances((prev) => [instance, ...prev]);
    return instance;
  }, []);

  const stopInstance = useCallback(async (instanceId: string) => {
    await stopRun(instanceId);
    setInstances((prev) =>
      prev.map((i) => (i.id === instanceId ? { ...i, status: "stopped" as const } : i))
    );
  }, []);

  const dryRunValidate = useCallback(async (data: Partial<RunConfig>) => {
    return validateConfig(data);
  }, []);

  return {
    configs,
    instances,
    loading,
    refresh,
    saveConfig,
    removeConfig,
    runConfig,
    stopInstance,
    dryRunValidate,
  };
}
