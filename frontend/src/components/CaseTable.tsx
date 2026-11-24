import { Chip, Checkbox, Link as MuiLink, Table, TableBody, TableCell, TableHead, TableRow } from "@mui/material";
import { Link } from "react-router-dom";
import type { TestCase } from "../types";

const RISK_COLOR: Record<string, "error" | "warning" | "success" | "default"> = {
  critical: "error",
  high: "warning",
  medium: "default",
  low: "success",
};

export function CaseTable({
  items,
  selected,
  onToggle,
  onToggleAll,
}: {
  items: TestCase[];
  selected: string[];
  onToggle: (id: string) => void;
  onToggleAll: (checked: boolean) => void;
}) {
  const allChecked = items.length > 0 && items.every((item) => selected.includes(item.id));
  return (
    <Table size="small" aria-label="Test cases">
      <TableHead>
        <TableRow>
          <TableCell padding="checkbox">
            <Checkbox
              inputProps={{ "aria-label": "Select all test cases" }}
              checked={allChecked}
              onChange={(event) => onToggleAll(event.target.checked)}
            />
          </TableCell>
          <TableCell>ID</TableCell>
          <TableCell>Title</TableCell>
          <TableCell>Type</TableCell>
          <TableCell>Priority</TableCell>
          <TableCell>Risk</TableCell>
          <TableCell>Ref</TableCell>
          <TableCell>Origin</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {items.map((item) => (
          <TableRow key={item.id} hover selected={selected.includes(item.id)}>
            <TableCell padding="checkbox">
              <Checkbox
                inputProps={{ "aria-label": `Select ${item.case_key}` }}
                checked={selected.includes(item.id)}
                onChange={() => onToggle(item.id)}
              />
            </TableCell>
            <TableCell>{item.case_key}</TableCell>
            <TableCell>
              <MuiLink component={Link} to={`/cases/${item.id}`} underline="hover">
                {item.title}
              </MuiLink>
            </TableCell>
            <TableCell>{item.test_type.replaceAll("_", " ")}</TableCell>
            <TableCell>{item.priority}</TableCell>
            <TableCell>
              <Chip size="small" label={item.risk_level} color={RISK_COLOR[item.risk_level] || "default"} />
            </TableCell>
            <TableCell>{item.requirement_ref}</TableCell>
            <TableCell>{item.generation_metadata?.scenario_origin || "—"}</TableCell>
          </TableRow>
        ))}
        {items.length === 0 && (
          <TableRow>
            <TableCell colSpan={8}>No test cases match the current filters.</TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
