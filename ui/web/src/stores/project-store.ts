import { create } from "zustand";

interface ProjectStoreState {
  activeProject: string | null;
  setActiveProject: (name: string | null) => void;
}

const STORAGE_KEY = "pw-ui:active-project";

export const useProjectStore = create<ProjectStoreState>((set) => ({
  activeProject:
    typeof window !== "undefined"
      ? window.localStorage.getItem(STORAGE_KEY)
      : null,
  setActiveProject: (name) => {
    if (typeof window !== "undefined") {
      if (name) window.localStorage.setItem(STORAGE_KEY, name);
      else window.localStorage.removeItem(STORAGE_KEY);
    }
    set({ activeProject: name });
  },
}));
