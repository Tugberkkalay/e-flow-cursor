import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const INBOX_TASKS = [
  { id: "task_1", title: "Vendor Selection", type: "task", requiredComment: false },
  { id: "app_9", title: "PR Approval #1029", type: "approval", requiredComment: true },
];

export default function InboxPage() {
  return (
    <AppShell
      title="Onaylarım"
      subtitle="Bekleyen onaylar ve görevler · comment required senaryoları"
    >
      <div className="space-y-3">
        {INBOX_TASKS.map((item) => (
          <Card key={item.id} className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">{item.title}</p>
                <div className="mt-1 flex items-center gap-2">
                  <Badge>{item.type}</Badge>
                  {item.requiredComment ? (
                    <Badge variant="warning">Comment required</Badge>
                  ) : null}
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="secondary" size="sm">
                  Revision
                </Button>
                <Button variant="secondary" size="sm">
                  Info request
                </Button>
                <Button variant="destructive" size="sm">
                  Reject
                </Button>
                <Button size="sm">Approve</Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </AppShell>
  );
}
