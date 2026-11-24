import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

interface ProjectContextValue {
  projectId: string;
  setProjectId: (id: string) => void;
}

const ProjectContext = createContext<ProjectContextValue>({ projectId: "", setProjectId: () => undefined });

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [projectId, setProjectIdState] = useState(() => localStorage.getItem("selectedProjectId") || "");
  const value = useMemo<ProjectContextValue>(
    () => ({
      projectId,
      setProjectId: (id: string) => {
        setProjectIdState(id);
        if (id) localStorage.setItem("selectedProjectId", id);
        else localStorage.removeItem("selectedProjectId");
      },
    }),
    [projectId],
  );
  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
}

export function useProjectId() {
  return useContext(ProjectContext);
}
