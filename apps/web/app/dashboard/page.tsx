import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DOMAIN_TEMPLATES } from "@/lib/templates";

const STATS = [
  { label: "Aktif Instance", value: "18", trend: "+6%" },
  { label: "Bekleyen Onay", value: "7", trend: "-2%" },
  { label: "SLA Risk", value: "2", trend: "-33%" },
  { label: "Bu Ay Tamamlanan", value: "124", trend: "+19%" },
];

export default function DashboardPage() {
  return (
    <AppShell
      title="İzleme"
      subtitle="Enterprise BPM görünümü · timeline / risk / throughput"
    >
      <div className="grid grid-cols-12 gap-4">
        {STATS.map((stat) => (
          <Card key={stat.label} className="col-span-3">
            <CardHeader className="pb-2">
              <CardDescription>{stat.label}</CardDescription>
              <CardTitle className="text-3xl">{stat.value}</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge variant="success">{stat.trend}</Badge>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-4 grid grid-cols-12 gap-4">
        <Card className="col-span-7">
          <CardHeader>
            <CardTitle>Domain Template Galerisi</CardTitle>
            <CardDescription>Seed edilen 4 akış, demo başlatmaya hazır.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {DOMAIN_TEMPLATES.map((template) => (
              <div
                key={template.code}
                className="rounded-xl border border-[#E8EDF3] bg-[#FBFCFE] px-4 py-3"
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{template.name}</h3>
                  <Badge>{template.domain}</Badge>
                </div>
                <p className="mt-1 text-sm text-[#5A6678]">{template.description}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="col-span-5">
          <CardHeader>
            <CardTitle>Policy Flags</CardTitle>
            <CardDescription>Mismatch/dispute/policy ihlali sinyalleri.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="rounded-xl border border-[#F0D0D0] bg-[#FDF2F2] p-3">
              Invoice #INV-3341 tolerance outside (+4.2%)
            </div>
            <div className="rounded-xl border border-[#F0E2C2] bg-[#FFF9ED] p-3">
              PR #PR-1029 requires offer count &gt;= 2
            </div>
            <div className="rounded-xl border border-[#D3E6F5] bg-[#EFF7FD] p-3">
              Contract #CTR-885 timer notify (end_date -30d)
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
