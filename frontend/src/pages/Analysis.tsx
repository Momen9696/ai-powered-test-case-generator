import { Alert, Box, Chip, Paper, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useProjectId } from "../project";
import type { AnalysisPayload, AnalysisRecord, Finding } from "../types";

const SECTIONS: { key: keyof AnalysisPayload; label: string }[] = [
  { key: "functional_requirements", label: "Functional requirements" },
  { key: "business_rules", label: "Business rules" },
  { key: "actors", label: "Actors and roles" },
  { key: "preconditions", label: "Preconditions" },
  { key: "expected_outcomes", label: "Expected outcomes" },
  { key: "constraints", label: "Constraints" },
  { key: "acceptance_criteria", label: "Acceptance criteria" },
  { key: "dependencies", label: "Dependencies" },
  { key: "ambiguities", label: "Ambiguous statements" },
  { key: "missing_information", label: "Missing information" },
];

function FindingList({ items }: { items: Finding[] }) {
  if (!items.length) return <Typography color="text.secondary">None found.</Typography>;
  return (
    <Stack spacing={1}>
      {items.map((item) => (
        <Paper key={item.id} variant="outlined" sx={{ p: 1.5 }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography fontWeight={700}>{item.id}</Typography>
            <Chip
              size="small"
              label={item.origin}
              color={item.origin === "extracted" ? "success" : "warning"}
              variant="outlined"
            />
          </Stack>
          <Typography sx={{ mt: 0.5 }}>{item.statement}</Typography>
          {item.evidence && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Evidence: {item.evidence}
            </Typography>
          )}
          {item.rationale && (
            <Typography variant="body2" color="text.secondary">
              {item.rationale}
            </Typography>
          )}
        </Paper>
      ))}
    </Stack>
  );
}

export function AnalysisPage() {
  const { projectId } = useProjectId();
  const [record, setRecord] = useState<AnalysisRecord | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!projectId) return;
    void api<{ items: AnalysisRecord[] }>(`/api/projects/${projectId}/analyses`)
      .then((body) => setRecord(body.items[0] || null))
      .catch((err: Error) => setError(err.message));
  }, [projectId]);

  if (!projectId) return <Alert severity="info">Select a project on the dashboard first.</Alert>;
  return (
    <Stack spacing={2}>
      <Typography variant="h4">Requirements analysis</Typography>
      <Alert severity="info">
        Extracted items quote the source. Inferred items are gaps from deterministic rules. This page does not show a model quality score.
      </Alert>
      {error && <Alert severity="error">{error}</Alert>}
      {!record && !error && <Alert severity="warning">No analysis is stored for this project yet. Generate tests or analyze a source first.</Alert>}
      {record && (
        <>
          <Typography variant="body2" color="text.secondary">
            Detector {record.payload.summary.detector}. Language model used: {record.payload.summary.llm_used ? "yes" : "no"}.
          </Typography>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" }, gap: 2 }}>
            {SECTIONS.map((section) => (
              <Stack key={section.key} spacing={1}>
                <Typography variant="h6">{section.label}</Typography>
                <FindingList items={(record.payload[section.key] as Finding[]) || []} />
              </Stack>
            ))}
          </Box>
        </>
      )}
    </Stack>
  );
}
