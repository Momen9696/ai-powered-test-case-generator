import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { CaseTable } from "../components/CaseTable";
import { filterCases } from "../lib/filters";
import { useProjectId } from "../project";
import { TEST_TYPES, type Suite, type TestCase } from "../types";

export function TestCasesPage() {
  const { projectId } = useProjectId();
  const [items, setItems] = useState<TestCase[]>([]);
  const [suites, setSuites] = useState<Suite[]>([]);
  const [query, setQuery] = useState("");
  const [testType, setTestType] = useState("");
  const [priority, setPriority] = useState("");
  const [sort, setSort] = useState("case_key");
  const [selected, setSelected] = useState<string[]>([]);
  const [duplicates, setDuplicates] = useState<{ score: number; cases: { case_key: string; title: string }[] }[]>([]);
  const [error, setError] = useState("");

  async function load(id: string) {
    const [caseBody, suiteBody, duplicateBody] = await Promise.all([
      api<{ items: TestCase[] }>(`/api/projects/${id}/test-cases?limit=500&sort=${sort}&priority=${priority}`),
      api<Suite[]>(`/api/projects/${id}/suites`),
      api<{ groups: { score: number; cases: { case_key: string; title: string }[] }[] }>(`/api/projects/${id}/duplicates`),
    ]);
    setItems(caseBody.items);
    setSuites(suiteBody);
    setDuplicates(duplicateBody.groups);
  }

  useEffect(() => {
    if (!projectId) return;
    void load(projectId).catch((err: Error) => setError(err.message));
  }, [projectId, sort, priority]);

  if (!projectId) return <Alert severity="info">Select a project on the dashboard first.</Alert>;
  const visible = filterCases(items, query, testType);

  async function bulk(action: "delete" | "assign_suite" | "update", extra: Record<string, unknown> = {}) {
    if (!selected.length) return;
    setError("");
    try {
      await api(`/api/projects/${projectId}/test-cases/bulk`, {
        method: "POST",
        body: JSON.stringify({ action, ids: selected, ...extra }),
      });
      setSelected([]);
      await load(projectId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bulk action failed");
    }
  }

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Generated test cases</Typography>
      {error && <Alert severity="error">{error}</Alert>}
      {duplicates.length > 0 && (
        <Alert severity="warning">
          {duplicates.length} possible duplicate group{duplicates.length === 1 ? "" : "s"} by title similarity (token Jaccard, threshold 0.8).
          {" "}
          {duplicates[0].cases.map((item) => item.case_key).join(", ")} score {duplicates[0].score}.
        </Alert>
      )}
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "2fr 1fr 1fr 1fr" }, gap: 1 }}>
        <TextField
          label="Search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          inputProps={{ "data-testid": "case-search" }}
        />
        <TextField select label="Type" value={testType} onChange={(event) => setTestType(event.target.value)}>
          <MenuItem value="">All types</MenuItem>
          {TEST_TYPES.map((type) => (
            <MenuItem key={type} value={type}>
              {type.replaceAll("_", " ")}
            </MenuItem>
          ))}
        </TextField>
        <TextField select label="Priority" value={priority} onChange={(event) => setPriority(event.target.value)}>
          <MenuItem value="">All priorities</MenuItem>
          {["critical", "high", "medium", "low"].map((item) => (
            <MenuItem key={item} value={item}>
              {item}
            </MenuItem>
          ))}
        </TextField>
        <TextField select label="Sort" value={sort} onChange={(event) => setSort(event.target.value)}>
          <MenuItem value="case_key">Case ID</MenuItem>
          <MenuItem value="priority">Priority</MenuItem>
          <MenuItem value="title">Title</MenuItem>
          <MenuItem value="risk_level">Risk</MenuItem>
        </TextField>
      </Box>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        <Button variant="outlined" color="error" disabled={!selected.length} onClick={() => void bulk("delete")}>
          Delete selected
        </Button>
        <Button
          variant="outlined"
          disabled={!selected.length}
          onClick={() => void bulk("update", { status: "reviewed" })}
        >
          Mark reviewed
        </Button>
        {suites[0] && (
          <Button variant="outlined" disabled={!selected.length} onClick={() => void bulk("assign_suite", { suite_id: suites[0].id })}>
            Add to {suites[0].name}
          </Button>
        )}
      </Stack>
      <CaseTable
        items={visible}
        selected={selected}
        onToggle={(id) => setSelected((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]))}
        onToggleAll={(checked) => setSelected(checked ? visible.map((item) => item.id) : [])}
      />
    </Stack>
  );
}
