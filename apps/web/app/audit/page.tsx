import { AppShell } from "@/components/shell/app-shell";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function AuditPage() {
  return (
    <AppShell
      title="Denetim"
      subtitle="Immutable audit event stream · silinemez kayıtlar"
      actionSlot={<Button variant="secondary">Export CSV</Button>}
    >
      <Card className="p-4">
        <div className="mb-4 grid grid-cols-4 gap-2">
          <Input placeholder="instance" />
          <Input placeholder="user" />
          <Input placeholder="flow" />
          <Input placeholder="form" />
        </div>
        <div className="space-y-2 text-sm">
          {[
            "instance.started · user=admin · id=ins_1001",
            "task.created · user=system · id=task_009",
            "approval.decided · user=finance · decision=approve",
          ].map((line) => (
            <div
              key={line}
              className="rounded-xl border border-[#E8EDF3] bg-[#FBFCFE] px-3 py-2"
            >
              {line}
            </div>
          ))}
        </div>
      </Card>
    </AppShell>
  );
}
