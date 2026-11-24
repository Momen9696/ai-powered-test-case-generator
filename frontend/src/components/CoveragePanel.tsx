import { Alert, Box, Chip, LinearProgress, Paper, Typography } from "@mui/material";
import type { Coverage } from "../types";

export function CoveragePanel({ coverage }: { coverage: Coverage | null }) {
  if (!coverage) {
    return <Alert severity="info">Run requirements analysis to map coverage.</Alert>;
  }
  const percent = coverage.coverage_percent;
  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle1">Requirement coverage</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {coverage.basis}
      </Typography>
      {percent === null ? (
        <Alert severity="warning">{coverage.note || "No acceptance criteria were extracted."}</Alert>
      ) : (
        <>
          <Typography variant="body2" sx={{ mb: 0.5 }}>
            {coverage.covered} of {coverage.total_acceptance_criteria} acceptance criteria referenced ({percent}%)
          </Typography>
          <LinearProgress variant="determinate" value={percent} aria-label="Acceptance criteria coverage" />
        </>
      )}
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 1.5 }}>
        {coverage.uncovered.map((item) => (
          <Chip key={item.id} label={`${item.id} uncovered`} color="warning" variant="outlined" size="small" />
        ))}
        {coverage.uncovered.length === 0 && percent !== null && (
          <Chip label="Every extracted criterion has a case" color="success" size="small" />
        )}
      </Box>
    </Paper>
  );
}
