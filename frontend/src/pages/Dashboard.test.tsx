import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProjectProvider } from "../project";
import { DashboardPage } from "./Dashboard";

beforeEach(() => {
  localStorage.clear();
});

describe("Dashboard", () => {
  it("shows a demo project returned by the API", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.endsWith("/api/projects")) {
          return {
            ok: true,
            status: 200,
            json: async () => [
              {
                id: "demo-1",
                name: "Demo — Account transfer",
                description: "Sample project",
                is_demo: true,
                created_at: "2026-11-24T00:00:00Z",
                updated_at: "2026-11-24T00:00:00Z",
              },
            ],
          };
        }
        if (url.includes("/summary")) {
          return {
            ok: true,
            status: 200,
            json: async () => ({
              project: {
                id: "demo-1",
                name: "Demo — Account transfer",
                description: "Sample project",
                is_demo: true,
                created_at: "",
                updated_at: "",
              },
              counts: { test_cases: 12, suites: 1, sources: 1, analyses: 1 },
              by_type: { functional: 4 },
              by_priority: { high: 4 },
              by_risk: { medium: 4 },
              coverage: {
                basis: "reference mapping",
                total_acceptance_criteria: 4,
                covered: 4,
                coverage_percent: 100,
                items: [],
                uncovered: [],
                note: null,
                llm_used: false,
              },
              latest_run: {
                provider: "mock",
                model: "deterministic-rules-v1",
                status: "completed",
                stats: { deterministic: true, case_count: 12 },
                created_at: "2026-11-24T00:00:00Z",
              },
            }),
          };
        }
        throw new Error(`Unexpected ${url}`);
      }),
    );
    render(
      <MemoryRouter>
        <ProjectProvider>
          <DashboardPage />
        </ProjectProvider>
      </MemoryRouter>,
    );
    expect(await screen.findByText("Demo — Account transfer")).toBeInTheDocument();
    expect(await screen.findByText("Demo data")).toBeInTheDocument();
    expect(await screen.findByText("12")).toBeInTheDocument();
  });
});
