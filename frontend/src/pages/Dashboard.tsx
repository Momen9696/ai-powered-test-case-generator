import { Alert, Box, Button, Chip, Paper, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { CoveragePanel } from "../components/CoveragePanel";
import { useProjectId } from "../project";
import type { Project, Summary } from "../types";

export function DashboardPage() {
  const navigate = useNavigate();
  const { projectId, setProjectId } = useProjectId();
  const [projects, setProjects] = useState<Project[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const rows = await api<Project[]>("/api/projects");
      setProjects(rows);
      const selected = rows.some((item) => item.id === projectId) ? projectId : rows[0]?.id || "";
      if (selected !== projectId) setProjectId(selected);
      if (selected) setSummary(await api<Summary>(`/api/projects/${selected}/summary`));
      else setSummary(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load projects");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // The stored project id is read once when the dashboard opens.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function seed() {
    setError("");
    try {
      const project = await api<Project>("/api/demo/seed", { method: "POST" });
      setProjectId(project.id);
      navigate("/");
      const rows = await api<Project[]>("/api/projects");
      setProjects(rows);
      setSummary(await api<Summary>(`/api/projects/${project.id}/summary`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load the demo");
    }
  }

  return (
    <Stack spacing={2}>
      <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2, flexWrap: "wrap" }}>
        <Box>
          <Typography variant="h4">Dashboard</Typography>
          <Typography color="text.secondary">Counts come from saved projects. There are no placeholder metrics.</Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" onClick={() => void seed()}>
            Load demo project
          </Button>
          <Button variant="contained" component={RouterLink} to="/generate">
            New generation
          </Button>
        </Stack>
      </Box>
      {error && <Alert severity="error">{error}</Alert>}
      {loading && <Typography>Loading saved projects…</Typography>}
      {!loading && projects.length === 0 && (
        <Alert severity="info">No projects yet. Load the labeled demo or create a project from New generation.</Alert>
      )}
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "280px 1fr" }, gap: 2 }}>
        <Stack spacing={1}>
          {projects.map((project) => (
            <Paper
              key={project.id}
              variant="outlined"
              data-testid="project-card"
              sx={{ p: 1.5, cursor: "pointer", borderColor: project.id === projectId ? "primary.main" : "divider" }}
              onClick={() => {
                setProjectId(project.id);
                void api<Summary>(`/api/projects/${project.id}/summary`).then(setSummary).catch((err: Error) => setError(err.message));
              }}
            >
              <Typography fontWeight={700}>{project.name}</Typography>
              {project.is_demo && <Chip size="small" label="Demo data" color="secondary" sx={{ mt: 0.5 }} />}
              <Typography variant="body2" color="text.secondary">
                {project.description}
              </Typography>
            </Paper>
          ))}
        </Stack>
        {summary && (
          <Stack spacing={2}>
            {summary.project.is_demo && (
              <Alert severity="info">
                This is the seeded demo project. Figures below are stored records from that seed, not a live model evaluation.
              </Alert>
            )}
            <Box sx={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 1 }}>
              {Object.entries({
                "Test cases": summary.counts.test_cases,
                Suites: summary.counts.suites,
                Sources: summary.counts.sources,
                Analyses: summary.counts.analyses,
              }).map(([label, value]) => (
                <Paper key={label} variant="outlined" sx={{ p: 1.5 }}>
                  <Typography variant="body2" color="text.secondary">{label}</Typography>
                  <Typography variant="h5">{value}</Typography>
                </Paper>
              ))}
            </Box>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle1">Cases by type</Typography>
              {Object.keys(summary.by_type).length === 0 && <Typography color="text.secondary">No cases stored.</Typography>}
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mt: 1 }}>
                {Object.entries(summary.by_type).map(([type, count]) => (
                  <Chip key={type} label={`${type.replaceAll("_", " ")} · ${count}`} />
                ))}
              </Stack>
              {summary.latest_run && (
                <Typography variant="body2" sx={{ mt: 1.5 }}>
                  Latest run: {summary.latest_run.provider} / {summary.latest_run.model} · {summary.latest_run.status}
                  {summary.latest_run.stats?.deterministic ? " · deterministic" : ""}
                </Typography>
              )}
            </Paper>
            <CoveragePanel coverage={summary.coverage} />
          </Stack>
        )}
      </Box>
    </Stack>
  );
}
