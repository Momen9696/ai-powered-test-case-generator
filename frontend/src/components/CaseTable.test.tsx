import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { CaseTable } from "./CaseTable";
import type { TestCase } from "../types";

const row: TestCase = {
  id: "case-1",
  project_id: "p",
  suite_id: null,
  source_id: null,
  case_key: "TC-0001",
  title: "Accept the valid path for a transfer",
  description: "",
  requirement_ref: "AC-1",
  preconditions: [],
  steps: ["Submit"],
  test_data: {},
  expected_result: "Accepted",
  test_type: "positive",
  priority: "high",
  risk_level: "medium",
  automation_suitability: "high",
  tags: [],
  generation_metadata: { scenario_origin: "extracted", provider: "mock" },
  status: "draft",
  created_at: "",
  updated_at: "",
};

describe("CaseTable", () => {
  it("selects a row and shows the case id", async () => {
    const user = userEvent.setup();
    const onToggle = vi.fn();
    render(
      <MemoryRouter>
        <CaseTable items={[row]} selected={[]} onToggle={onToggle} onToggleAll={vi.fn()} />
      </MemoryRouter>,
    );
    expect(screen.getByText("TC-0001")).toBeInTheDocument();
    await user.click(screen.getByLabelText("Select TC-0001"));
    expect(onToggle).toHaveBeenCalledWith("case-1");
  });
});
