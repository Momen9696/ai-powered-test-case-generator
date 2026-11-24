import { Alert, Button, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { api, downloadExport, saveBlob } from "../api/client";
import { useProjectId } from "../project";
import type { Suite } from "../types";

export function ExportPage() {
  const { projectId } = useProjectId();
  const [format, setFormat] = useState("xlsx");
  const [suiteId, setSuiteId] = useState("");
  const [suites, setSuites] = useState<Suite[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!projectId) return;
    void api<Suite[]>(`/api/projects/${projectId}/suites`)
      .then(setSuites)
      .catch((err: Error) => setError(err.message));
  }, [projectId]);

  if (!projectId) return <Alert severity="info">Select a project on the dashboard first.</Alert>;

  async function runExport() {
    setError("");
    setMessage("");
    try {
      const file = await downloadExport(projectId, format, suiteId || undefined);
      saveBlob(file.blob, file.filename);
      setMessage(`Downloaded ${file.filename} (${file.blob.size} bytes).`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    }
  }

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Export center</Typography>
      <Alert severity="info">
        Excel, CSV, and JSON exports contain the stored cases. The About note in Excel, and the JSON note, state when rows came from the mock provider.
      </Alert>
      {error && <Alert severity="error">{error}</Alert>}
      {message && <Alert severity="success">{message}</Alert>}
      <Stack direction={{ xs: "column", md: "row" }} spacing={1}>
        <TextField select label="Format" value={format} onChange={(event) => setFormat(event.target.value)}>
          <MenuItem value="xlsx">Excel (.xlsx)</MenuItem>
          <MenuItem value="csv">CSV</MenuItem>
          <MenuItem value="json">JSON</MenuItem>
        </TextField>
        <TextField select label="Suite" value={suiteId} onChange={(event) => setSuiteId(event.target.value)} sx={{ minWidth: 240 }}>
          <MenuItem value="">All cases in the project</MenuItem>
          {suites.map((suite) => (
            <MenuItem key={suite.id} value={suite.id}>
              {suite.name}
            </MenuItem>
          ))}
        </TextField>
        <Button variant="contained" onClick={() => void runExport()}>
          Download
        </Button>
      </Stack>
    </Stack>
  );
}
