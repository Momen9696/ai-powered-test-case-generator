export function validateGenerationInput(content: string): string | null {
  if (!content.trim()) {
    return "Enter a user story or requirements document.";
  }
  if (content.length > 100_000) {
    return "Input exceeds 100,000 characters.";
  }
  return null;
}

export function validateProjectName(name: string, creating: boolean): string | null {
  if (creating && !name.trim()) {
    return "Enter a project name.";
  }
  return null;
}
