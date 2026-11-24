import { describe, expect, it } from "vitest";
import type { TestCase } from "../types";
import { filterCases, sortCases } from "./filters";

function sample(partial: Partial<TestCase>): TestCase {
  return {
    id: partial.id || "1",
    project_id: "p",
    suite_id: null,
    source_id: null,
    case_key: partial.case_key || "TC-0001",
    title: partial.title || "Verify transfer",
    description: "",
    requirement_ref: partial.requirement_ref || "AC-1",
    preconditions: [],
    steps: ["Submit"],
    test_data: {},
    expected_result: partial.expected_result || "Accepted",
    test_type: partial.test_type || "functional",
    priority: partial.priority || "medium",
    risk_level: "medium",
    automation_suitability: "high",
    tags: partial.tags || ["functional"],
    generation_metadata: {},
    status: "draft",
    created_at: "",
    updated_at: "",
  };
}

describe("case filters", () => {
  const cases = [
    sample({ id: "1", case_key: "TC-0002", title: "Security checks around transfer", test_type: "security", priority: "high", tags: ["security"] }),
    sample({ id: "2", case_key: "TC-0001", title: "Accept the valid path", test_type: "positive", priority: "low" }),
  ];

  it("filters by query and type", () => {
    expect(filterCases(cases, "security", "").map((item) => item.id)).toEqual(["1"]);
    expect(filterCases(cases, "", "positive").map((item) => item.id)).toEqual(["2"]);
    expect(filterCases(cases, "missing", "")).toEqual([]);
  });

  it("sorts by priority and case id", () => {
    expect(sortCases(cases, "priority").map((item) => item.id)).toEqual(["1", "2"]);
    expect(sortCases(cases, "case_key").map((item) => item.case_key)).toEqual(["TC-0001", "TC-0002"]);
  });
});
