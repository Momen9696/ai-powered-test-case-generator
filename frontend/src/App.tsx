import { CssBaseline, ThemeProvider } from "@mui/material";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./layout/AppShell";
import { AnalysisPage } from "./pages/Analysis";
import { DashboardPage } from "./pages/Dashboard";
import { ExportPage } from "./pages/ExportCenter";
import { GeneratePage } from "./pages/Generate";
import { SettingsPage } from "./pages/Settings";
import { SuitesPage } from "./pages/Suites";
import { TestCaseDetailPage } from "./pages/TestCaseDetail";
import { TestCasesPage } from "./pages/TestCases";
import { ProjectProvider } from "./project";
import { theme } from "./theme";

export function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ProjectProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/generate" element={<GeneratePage />} />
              <Route path="/analysis" element={<AnalysisPage />} />
              <Route path="/cases" element={<TestCasesPage />} />
              <Route path="/cases/:caseId" element={<TestCaseDetailPage />} />
              <Route path="/suites" element={<SuitesPage />} />
              <Route path="/export" element={<ExportPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ProjectProvider>
    </ThemeProvider>
  );
}
