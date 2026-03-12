import { AppShell } from "@/components/shell/app-shell";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function SettingsPage() {
  return (
    <AppShell title="Ayarlar" subtitle="Org-level sistem ayarları">
      <div className="grid grid-cols-12 gap-4">
        <Card className="col-span-6 p-4">
          <h3 className="mb-3 text-lg font-semibold">Genel</h3>
          <div className="space-y-2">
            <Input placeholder="Organization Name" defaultValue="e-Flow Demo Org" />
            <Input placeholder="Default Currency" defaultValue="TRY" />
            <Input placeholder="Timezone" defaultValue="Europe/Istanbul" />
          </div>
        </Card>
        <Card className="col-span-6 p-4">
          <h3 className="mb-3 text-lg font-semibold">Integration</h3>
          <div className="space-y-2">
            <Input placeholder="MinIO Endpoint" defaultValue="http://localhost:9000" />
            <Input placeholder="Webhook Secret" defaultValue="********" />
            <Input placeholder="HTTP Retry Policy" defaultValue="retries=3, backoff=2s" />
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
