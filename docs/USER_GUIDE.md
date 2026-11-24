# User guide

Screenshots from the local mock run are in `docs/screenshots/`: dashboard, analysis, test cases, generation, export, and a narrow dashboard view.

## 1. Open the dashboard

The dashboard lists saved projects. Counts, the type breakdown, and coverage are read from the database for the selected project. An empty workspace stays empty until you create a project or load the demo.

**Load demo project** stores a project named "Demo — Account transfer" and marks it as demo data. Running it again returns the same project.

## 2. Generate

1. Open **New generation**.
2. Choose a project or create one.
3. Paste a story, or use one of the example buttons. Examples only fill the form. They do not generate until you submit.
4. Choose scenario types. Leave the suite name blank if you do not want a new suite.
5. Click **Generate test cases**.

The stepper follows the real requests: save the source, analyze it, generate cases, then store them. If a request fails, the error from the API stays on the page.

## 3. Read the analysis

**Requirements analysis** shows the latest stored analysis.

- Green **extracted** chips quote the source.
- Amber **inferred** chips are gaps. They are not statements the author wrote.

The summary line states that the heuristic detector did not use a language model.

## 4. Review cases

**Test cases** supports search, type, priority, and sort. Select rows to delete them, mark them reviewed, or add them to the first suite.

A warning appears when two titles are close enough for the Jaccard check (threshold 0.8). That warning is a lexical comparison.

Open a case to edit the title, steps, data, expected result, priority, risk, automation suitability, and status. Saving sends a PATCH and keeps the generation metadata.

If the case came from the mock provider, the detail page says so.

## 5. Suites and export

Create a suite on **Test suites**, or pass a suite name during generation. The suite page lists the cases assigned to it.

**Export center** downloads every case in the project, or one suite, as Excel, CSV, or JSON. Excel includes an About sheet. JSON includes a note that mock rows were not returned by an external model.

## 6. Settings

Choose Mock, OpenAI, or Anthropic. A provider marked "key not set" will fail at generation time with a configuration error. Temperature and max tokens apply to the remote adapters. The mock provider records them and does not use them.

Keys are not entered in the browser.
