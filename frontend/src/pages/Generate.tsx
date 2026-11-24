import {
  Alert,
  Box,
  Button,
  Checkbox,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Step,
  StepLabel,
  Stepper,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { validateGenerationInput, validateProjectName } from "../lib/validation";
import { useProjectId } from "../project";
import { TEST_TYPES, type ExampleItem, type Project, type TestCase } from "../types";

const STAGES = ["Save input", "Analyze requirements", "Generate test cases", "Store results"];

export function GeneratePage() {
  const navigate = useNavigate();
  const { projectId, setProjectId } = useProjectId();
  const [projects, setProjects] = useState<Project[]>([]);
  const [examples, setExamples] = useState<Record<string, ExampleItem>>({});
  const [creating, setCreating] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [kind, setKind] = useState<"user_story" | "requirements_document">("user_story");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [suiteName, setSuiteName] = useState("");
  const [types, setTypes] = useState<string[]>([...TEST_TYPES]);
  const [stage, setStage] = useState(-1);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState(0);

  useEffect(() => {
    void api<Project[]>("/api/projects").then(setProjects).catch((err: Error) => setError(err.message));
    void api<{ examples: Record<string, ExampleItem> }>("/api/examples")
      .then((body) => setExamples(body.examples))
      .catch((err: Error) => setError(err.message));
  }, []);

  function toggleType(type: string) {
    setTypes((current) => (current.includes(type) ? current.filter((item) => item !== type) : [...current, type]));
  }

  async function submit() {
    const contentError = validateGenerationInput(content);
    const nameError = validateProjectName(projectName, creating || projects.length === 0);
    setError(contentError || nameError || (types.length === 0 ? "Select at least one test type." : ""));
    if (contentError || nameError || types.length === 0) return;
    setBusy(true);
    setCreated(0);
    try {
      setStage(0);
      let activeProject = projectId;
      if (creating || projects.length === 0) {
        const project = await api<Project>("/api/projects", {
          method: "POST",
          body: JSON.stringify({ name: projectName.trim(), description: "" }),
        });
        activeProject = project.id;
        setProjectId(project.id);
      }
      if (!activeProject) {
        setError("Select a project.");
        setBusy(false);
        return;
      }
      const source = await api<{ id: string }>(`/api/projects/${activeProject}/sources`, {
        method: "POST",
        body: JSON.stringify({
          kind,
          title: title.trim() || "Untitled requirement",
          content: content.trim(),
        }),
      });
      setStage(1);
      const analysis = await api<{ id: string }>(`/api/projects/${activeProject}/analyze`, {
        method: "POST",
        body: JSON.stringify({ source_id: source.id }),
      });
      setStage(2);
      const generated = await api<{ test_cases: TestCase[] }>(`/api/projects/${activeProject}/generate`, {
        method: "POST",
        body: JSON.stringify({
          source_id: source.id,
          analysis_id: analysis.id,
          types,
          suite_name: suiteName.trim() || null,
        }),
      });
      setStage(3);
      setCreated(generated.test_cases.length);
      setProjectId(activeProject);
      navigate("/cases");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
      setStage(-1);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Stack spacing={2}>
      <Typography variant="h4">New test generation</Typography>
      <Typography color="text.secondary">
        The running provider is chosen in Settings. The default is the deterministic mock, which does not call an external model.
      </Typography>
      {error && (
        <Alert severity="error" data-testid="validation-error">
          {error}
        </Alert>
      )}
      <Stepper activeStep={stage < 0 ? 0 : stage} alternativeLabel>
        {STAGES.map((label) => (
          <Step key={label} completed={stage >= STAGES.indexOf(label) && !busy && created > 0}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      {busy && <Alert severity="info">Working through the current step. This stays on screen until the API responds.</Alert>}
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" }, gap: 2 }}>
        <FormControl>
          <InputLabel id="project-label">Project</InputLabel>
          <Select
            labelId="project-label"
            label="Project"
            value={creating ? "__new__" : projectId}
            onChange={(event) => {
              if (event.target.value === "__new__") setCreating(true);
              else {
                setCreating(false);
                setProjectId(String(event.target.value));
              }
            }}
          >
            {projects.map((project) => (
              <MenuItem key={project.id} value={project.id}>
                {project.name}
                {project.is_demo ? " (demo)" : ""}
              </MenuItem>
            ))}
            <MenuItem value="__new__">Create a new project</MenuItem>
          </Select>
        </FormControl>
        {(creating || projects.length === 0) && (
          <TextField label="New project name" value={projectName} onChange={(event) => setProjectName(event.target.value)} />
        )}
        <TextField label="Title" value={title} onChange={(event) => setTitle(event.target.value)} />
        <FormControl>
          <InputLabel id="kind-label">Input type</InputLabel>
          <Select
            labelId="kind-label"
            label="Input type"
            value={kind}
            onChange={(event) => setKind(event.target.value as typeof kind)}
          >
            <MenuItem value="user_story">User story</MenuItem>
            <MenuItem value="requirements_document">Requirements document</MenuItem>
          </Select>
        </FormControl>
      </Box>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        {Object.entries(examples).map(([key, example]) => (
          <Button
            key={key}
            size="small"
            variant="outlined"
            onClick={() => {
              setKind(example.kind);
              setTitle(example.title);
              setContent(example.content);
            }}
          >
            Use example: {example.title}
          </Button>
        ))}
      </Stack>
      <TextField
        label="User story or requirements"
        value={content}
        onChange={(event) => setContent(event.target.value)}
        multiline
        minRows={10}
        inputProps={{ "data-testid": "content-input" }}
      />
      <TextField
        label="Suite name (optional)"
        value={suiteName}
        onChange={(event) => setSuiteName(event.target.value)}
        helperText="Leave blank to store cases without a new suite."
      />
      <Box>
        <Typography variant="subtitle2">Scenario types</Typography>
        <Box sx={{ display: "flex", flexWrap: "wrap" }}>
          {TEST_TYPES.map((type) => (
            <FormControlLabel
              key={type}
              control={<Checkbox checked={types.includes(type)} onChange={() => toggleType(type)} />}
              label={type.replaceAll("_", " ")}
            />
          ))}
        </Box>
      </Box>
      <Button variant="contained" onClick={() => void submit()} disabled={busy} data-testid="generate-submit">
        {busy ? "Generating…" : "Generate test cases"}
      </Button>
    </Stack>
  );
}
