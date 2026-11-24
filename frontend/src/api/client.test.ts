import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, api } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client", () => {
  it("posts JSON and returns the body", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({ id: "project-1" }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const body = await api<{ id: string }>("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name: "Billing", description: "" }),
    });
    expect(body.id).toBe("project-1");
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("POST");
    expect(new Headers(init.headers).get("Content-Type")).toBe("application/json");
  });

  it("surfaces validation errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        statusText: "Unprocessable",
        json: async () => ({ detail: "Enter a user story or requirements document." }),
      }),
    );
    await expect(api("/api/projects/p/sources", { method: "POST", body: "{}" })).rejects.toBeInstanceOf(ApiError);
  });
});
