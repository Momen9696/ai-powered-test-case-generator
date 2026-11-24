import { describe, expect, it } from "vitest";
import { validateGenerationInput, validateProjectName } from "./validation";

describe("generation validation", () => {
  it("rejects empty input", () => {
    expect(validateGenerationInput("   ")).toBe("Enter a user story or requirements document.");
  });

  it("rejects oversized input", () => {
    expect(validateGenerationInput("a".repeat(100_001))).toMatch(/100,000/);
  });

  it("accepts a story", () => {
    expect(validateGenerationInput("As a user, I want to export.")).toBeNull();
  });

  it("requires a name only when creating a project", () => {
    expect(validateProjectName("  ", true)).toBe("Enter a project name.");
    expect(validateProjectName("", false)).toBeNull();
  });
});
