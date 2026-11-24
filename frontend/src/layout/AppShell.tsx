import DashboardOutlinedIcon from "@mui/icons-material/DashboardOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import FolderOutlinedIcon from "@mui/icons-material/FolderOutlined";
import ListAltOutlinedIcon from "@mui/icons-material/ListAltOutlined";
import MenuIcon from "@mui/icons-material/Menu";
import PlaylistAddOutlinedIcon from "@mui/icons-material/PlaylistAddOutlined";
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";
import { AppBar, Box, Drawer, IconButton, List, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography, useMediaQuery } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

const NAV = [
  { to: "/", label: "Dashboard", icon: <DashboardOutlinedIcon /> },
  { to: "/generate", label: "New generation", icon: <PlaylistAddOutlinedIcon /> },
  { to: "/analysis", label: "Requirements analysis", icon: <FactCheckOutlinedIcon /> },
  { to: "/cases", label: "Test cases", icon: <ListAltOutlinedIcon /> },
  { to: "/suites", label: "Test suites", icon: <FolderOutlinedIcon /> },
  { to: "/export", label: "Export center", icon: <DownloadOutlinedIcon /> },
  { to: "/settings", label: "Settings", icon: <SettingsOutlinedIcon /> },
];

export function AppShell() {
  const theme = useTheme();
  const mobile = useMediaQuery(theme.breakpoints.down("md"));
  const [open, setOpen] = useState(false);
  const drawer = (
    <Box sx={{ width: 248, pt: 1 }}>
      <Typography sx={{ px: 2, py: 1.5, fontWeight: 700, color: "primary.main" }}>Test Case Generator</Typography>
      <List>
        {NAV.map((item) => (
          <ListItemButton
            key={item.to}
            component={NavLink}
            to={item.to}
            end={item.to === "/"}
            onClick={() => setOpen(false)}
            sx={{
              mx: 1,
              borderRadius: 1,
              "&.active": { bgcolor: "rgba(14, 77, 92, 0.1)", color: "primary.main" },
            }}
          >
            <ListItemIcon sx={{ minWidth: 36, color: "inherit" }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
  return (
    <Box sx={{ display: "flex", minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar position="fixed" elevation={0} sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Toolbar>
          {mobile && (
            <IconButton color="inherit" edge="start" onClick={() => setOpen(true)} aria-label="Open navigation">
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Requirements to test cases
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.85 }}>
            Default mode is a local mock
          </Typography>
        </Toolbar>
      </AppBar>
      <Drawer
        variant={mobile ? "temporary" : "permanent"}
        open={mobile ? open : true}
        onClose={() => setOpen(false)}
        sx={{ "& .MuiDrawer-paper": { top: 64, height: "calc(100% - 64px)", borderRight: "1px solid #E1E8EB" } }}
      >
        {drawer}
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, mt: "64px", ml: { md: "248px" }, p: { xs: 2, md: 3 } }}>
        <Box sx={{ maxWidth: 1180, mx: "auto" }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
