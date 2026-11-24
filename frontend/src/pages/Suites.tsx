import { Alert, Button, List, ListItem, ListItemButton, ListItemText, Paper, Stack, TextField, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useProjectId } from "../project";
import type { Suite, TestCase } from "../types";

export function SuitesPage() {
  const { projectId } = useProjectId();
  const [suites, setSuites] = useState<Suite[]>([]);
  const [cases, setCases] = useState<TestCase[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  async function load(id: string) {
    const [suiteRows, caseBody] = await Promise.all([
      api<Suite[]>(`/api/projects/${id}/suites`),
      api<{ items: TestCase[] }>(`/api/projects/${id}/test-cases?limit=500`),
    ]);
    setSuites(suiteRows);
    setCases(caseBody.items);
  }

  useEffect(() => {
    if (!projectId) return;
    void load(projectId).catch((err: Error) => setError(err.message));
  }, [projectId]);

  if (!projectId) return <Alert severity="info">Select a project on the dashboard first.</Alert>;

  async function createSuite() {
    if (!name.trim()) {
      setError("Enter a suite name.");
      return;
    }
    setError("");
    try {
      await api(`/api/projects/${projectId}/suites`, {
        method: "POST",
        body: JSON.stringify({ name: name.trim(), description }),
      });
      setName("");
      setDescription("");
      await load(projectId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the suite");
    }
  }

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Test suites</Typography>
      {error && <Alert severity="error">{error}</Alert>}
      <Stack direction={{ xs: "column", md: "row" }} spacing={1}>
        <TextField label="Suite name" value={name} onChange={(event) => setName(event.target.value)} />
        <TextField label="Description" value={description} onChange={(event) => setDescription(event.target.value)} fullWidth />
        <Button variant="contained" onClick={() => void createSuite()}>
          Create suite
        </Button>
      </Stack>
      {suites.length === 0 && <Alert severity="info">No suites yet. A generation can create one, or you can add one here.</Alert>}
      {suites.map((suite) => {
        const members = cases.filter((item) => item.suite_id === suite.id);
        return (
          <Paper key={suite.id} variant="outlined" sx={{ p: 2 }}>
            <Typography variant="h6">{suite.name}</Typography>
            <Typography variant="body2" color="text.secondary">{suite.description || "No description."}</Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>{suite.case_count} stored cases</Typography>
            <List dense>
              {members.map((item) => (
                <ListItem key={item.id} disablePadding>
                  <ListItemButton component={Link} to={`/cases/${item.id}`}>
                    <ListItemText primary={`${item.case_key} · ${item.title}`} />
                  </ListItemButton>
                </ListItem>
              ))}
              {members.length === 0 && <ListItem><ListItemText primary="No cases are assigned to this suite." /></ListItem>}
            </List>
          </Paper>
        );
      })}
    </Stack>
  );
}
