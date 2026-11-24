import type { TestCase } from "../types";

export function filterCases(cases: TestCase[], query: string, testType: string): TestCase[] {
  const needle = query.trim().toLowerCase();
  return cases.filter((item) => {
    if (testType && item.test_type !== testType) return false;
    if (!needle) return true;
    const haystack = [item.title, item.case_key, item.requirement_ref, item.expected_result, ...(item.tags || [])]
      .join(" ")
      .toLowerCase();
    return haystack.includes(needle);
  });
}

export function sortCases(cases: TestCase[], sort: "case_key" | "priority" | "title"): TestCase[] {
  const priorityRank: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
  return [...cases].sort((left, right) => {
    if (sort === "priority") return (priorityRank[left.priority] ?? 9) - (priorityRank[right.priority] ?? 9);
    if (sort === "title") return left.title.localeCompare(right.title);
    return left.case_key.localeCompare(right.case_key);
  });
}
