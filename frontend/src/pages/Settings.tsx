import { Alert, Button, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { SettingsPayload } from "../types";

export function SettingsPage() {
  const [settings, setSettings] = useState<SettingsPayload | null>(null);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");

  useEffect(() => {
    void api<SettingsPayload>("/api/settings")
      .then(setSettings)
      .catch((err: Error) => setError(err.message));
  }, []);

  async function save() {
    if (!settings) return;
    setError("");
    setSaved("");
    try {
      const updated = await api<SettingsPayload>("/api/settings", {
        method: "PUT",
        body: JSON.stringify({
          provider: settings.provider,
          model: settings.model,
          temperature: Number(settings.temperature),
          max_tokens: Number(settings.max_tokens),
        }),
      });
      setSettings(updated);
      setSaved("Settings saved on this server.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save settings");
    }
  }

  if (!settings) return <Typography>Loading settings…</Typography>;
  return (
    <Stack spacing={2} maxWidth={720}>
      <Typography variant="h4">Settings</Typography>
      <Alert severity="info">
        API keys are read from the server environment. This screen cannot set or display them. The mock provider ignores temperature and does not call a model.
      </Alert>
      {error && <Alert severity="error">{error}</Alert>}
      {saved && <Alert severity="success">{saved}</Alert>}
      <TextField
        select
        label="Provider"
        value={settings.provider}
        onChange={(event) => setSettings({ ...settings, provider: event.target.value as SettingsPayload["provider"] })}
      >
        {settings.providers.map((provider) => (
          <MenuItem key={provider.id} value={provider.id}>
            {provider.id} {provider.configured ? "(ready)" : "(key not set)"}
          </MenuItem>
        ))}
      </TextField>
      {settings.providers.map((provider) => (
        <Typography key={provider.id} variant="body2" color="text.secondary">
          {provider.id}: {provider.description}
        </Typography>
      ))}
      <TextField
        label="Model override"
        value={settings.model}
        helperText={`Active model: ${settings.active_model}. Leave blank to use the server default.`}
        onChange={(event) => setSettings({ ...settings, model: event.target.value })}
      />
      <TextField
        label="Temperature"
        type="number"
        value={settings.temperature}
        onChange={(event) => setSettings({ ...settings, temperature: Number(event.target.value) })}
        inputProps={{ step: 0.1, min: 0, max: 2 }}
      />
      <TextField
        label="Max tokens"
        type="number"
        value={settings.max_tokens}
        onChange={(event) => setSettings({ ...settings, max_tokens: Number(event.target.value) })}
        inputProps={{ min: 64, max: 8000 }}
      />
      <Button variant="contained" onClick={() => void save()}>
        Save settings
      </Button>
    </Stack>
  );
}
