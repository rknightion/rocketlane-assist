import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { configApi, Config } from '../services/api';

interface ConfigState {
  config: Config | null;
  isLoading: boolean;
  error: string | null;
  hasApiKeys: boolean;
}

interface ConfigActions {
  fetchConfig: () => Promise<void>;
  updateConfig: (updates: Partial<Config>) => Promise<void>;
  clearError: () => void;
}

type ConfigStore = ConfigState & ConfigActions;

export const useConfigStore = create<ConfigStore>()(
  persist(
    (set, get) => ({
      // State
      config: null,
      isLoading: false,
      error: null,
      hasApiKeys: false,

      // Actions
      fetchConfig: async () => {
        set({ isLoading: true, error: null });
        try {
          const config = await configApi.getConfig();
          const hasApiKeys = config.has_rocketlane_key &&
            (config.has_openai_key || config.has_anthropic_key);
          set({
            config,
            hasApiKeys,
            isLoading: false
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch config',
            isLoading: false
          });
        }
      },

      updateConfig: async (updates) => {
        set({ isLoading: true, error: null });
        try {
          await configApi.updateConfig(updates);
          // Refetch to get updated state
          await get().fetchConfig();
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to update config',
            isLoading: false
          });
          throw error; // Re-throw for component handling
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'config-storage',
      partialize: (state) => ({ config: state.config, hasApiKeys: state.hasApiKeys }),
    }
  )
);
