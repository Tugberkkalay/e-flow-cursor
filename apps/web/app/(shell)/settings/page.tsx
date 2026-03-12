import { SystemSettings } from "@/components/settings/system-settings";
import { getApiBaseUrl, getContextSchema, getDemoToken } from "@/lib/api";

export default async function SettingsPage() {
  const [contextSchema, token] = await Promise.all([
    getContextSchema(),
    getDemoToken(),
  ]);

  return (
    <SystemSettings
      contextSchema={contextSchema}
      token={token}
      apiBaseUrl={getApiBaseUrl()}
    />
  );
}
