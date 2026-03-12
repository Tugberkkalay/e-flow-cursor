"use client";

import { useState } from "react";
import { useParams } from "next/navigation";

import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const TIMELINE = [
  { at: "10:01", event: "instance.started", payload: "requester: Mert Demir" },
  { at: "10:04", event: "task.completed", payload: "form.total_amount: 72,000" },
  { at: "10:08", event: "approval.created", payload: "role: director" },
];

export default function ProcessDetailPage() {
  const params = useParams<{ id: string }>();
  const [tab, setTab] = useState("timeline");

  return (
    <AppShell
      title={`Süreç Detay · ${params.id}`}
      subtitle="Immutable timeline + tasks + approvals + documents"
      actionSlot={
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm">
            Reassign
          </Button>
          <Button variant="secondary" size="sm">
            Retry failed node
          </Button>
          <Button variant="destructive" size="sm">
            Cancel instance
          </Button>
        </div>
      }
    >
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="tasks">Tasks</TabsTrigger>
          <TabsTrigger value="approvals">Approvals</TabsTrigger>
          <TabsTrigger value="form">Form snapshot</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="controls">Controls/Flags</TabsTrigger>
        </TabsList>

        <TabsContent value="timeline">
          <Card className="p-4">
            <div className="space-y-2">
              {TIMELINE.map((item) => (
                <div
                  key={`${item.at}-${item.event}`}
                  className="flex items-center gap-3 rounded-xl border border-[#E7EBF0] px-3 py-2"
                >
                  <Badge>{item.at}</Badge>
                  <span className="font-medium">{item.event}</span>
                  <span className="text-sm text-[#5A6678]">{item.payload}</span>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="tasks">
          <Card className="p-4 text-sm">Pending task: Vendor Selection (procurement)</Card>
        </TabsContent>

        <TabsContent value="approvals">
          <Card className="p-4 text-sm">Approval route: manager → director → CFO fallback</Card>
        </TabsContent>

        <TabsContent value="form">
          <Card className="p-4">
            <pre className="rounded-xl bg-[#F8FAFD] p-3 text-xs">
              {JSON.stringify(
                { request_type: "Normal", total_amount: 72000, currency: "TRY" },
                null,
                2,
              )}
            </pre>
          </Card>
        </TabsContent>

        <TabsContent value="documents">
          <Card className="p-4 text-sm">
            invoice_v1.pdf · extracted_json: {'{'}&quot;supplier_vkn&quot;:&quot;1234567890&quot;{'}'}
          </Card>
        </TabsContent>

        <TabsContent value="controls">
          <Card className="p-4 text-sm">
            Flags: mismatch=false, policy_risk=true, dispute_open=false
          </Card>
        </TabsContent>
      </Tabs>
    </AppShell>
  );
}
