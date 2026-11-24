import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProjectProvider } from "../project";
import { GeneratePage } from "./Generate";

beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo) => {
      const url = String(input);
      if (url.endsWith("/api/projects")) {
        return { ok: true, status: 200, json: async () => [] };
      }
      if (url.endsWith("/api/examples")) {
        return { ok: true, status: 200, json: async () => ({ examples: {} }) };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    }),
  );
});

describe("Generate page", () => {
  it("blocks an empty submission", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ProjectProvider>
          <GeneratePage />
        </ProjectProvider>
      </MemoryRouter>,
    );
    await user.click(await screen.findByTestId("generate-submit"));
    expect(await screen.findByTestId("validation-error")).toHaveTextContent(
      "Enter a user story or requirements document.",
    );
    const fetchMock = vi.mocked(fetch);
    const posts = fetchMock.mock.calls.filter((call) => {
      const init = call[1] as RequestInit | undefined;
      return init?.method === "POST";
    });
    expect(posts).toHaveLength(0);
  });
});
