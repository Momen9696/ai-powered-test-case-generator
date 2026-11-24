import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#0E4D5C", contrastText: "#F7FBFC" },
    secondary: { main: "#B86E2A" },
    background: { default: "#F4F7F8", paper: "#FFFFFF" },
    text: { primary: "#1C2B33", secondary: "#52656E" },
    success: { main: "#1F7A4D" },
    warning: { main: "#A15C07" },
    error: { main: "#9F2D2D" },
    divider: "#E1E8EB",
  },
  typography: {
    fontFamily: '"Source Sans 3", "Segoe UI", "Helvetica Neue", Arial, sans-serif',
    h4: { fontWeight: 700, letterSpacing: "-0.02em" },
    h5: { fontWeight: 700 },
    h6: { fontWeight: 700 },
    button: { textTransform: "none", fontWeight: 600 },
  },
  shape: { borderRadius: 10 },
  components: {
    MuiButton: { styleOverrides: { root: { borderRadius: 8 } } },
    MuiPaper: { styleOverrides: { root: { backgroundImage: "none" } } },
    MuiTableCell: {
      styleOverrides: {
        head: { fontWeight: 700, color: "#3E555F", backgroundColor: "#F7FAFB" },
      },
    },
  },
});
