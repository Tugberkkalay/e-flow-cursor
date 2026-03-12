"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, RotateCcw, X } from "lucide-react";

import type { InboxPayload } from "@/lib/types";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatDate } from "@/lib/utils";

export function InboxBoard({
  initialInbox,
  token,
  apiBaseUrl,
}: {
  initialInbox: InboxPayload;
  token: string;
  apiBaseUrl: string;
}) {
  const router = useRouter();
  const [inbox, setInbox] = useState(initialInbox);

  const refreshInbox = async () => {
    const response = await fetch(`${apiBaseUrl}/inbox`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const next = (await response.json()) as InboxPayload;
    setInbox(next);
  };

  const decideApproval = async (id: string, decision: string) => {
    await fetch(`${apiBaseUrl}/approvals/${id}/decide`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ decision }),
    });
    await refreshInbox();
    router.refresh();
  };

  const completeTask = async (id: string, outcome: string) => {
    await fetch(`${apiBaseUrl}/tasks/${id}/complete`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ payload: {}, outcome }),
    });
    await refreshInbox();
    router.refresh();
  };

  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Bekleyen gorevler</CardTitle>
          <CardDescription>
            Complete, revision veya info request akislari task outcome ile
            ilerler.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {inbox.tasks.map((task) => (
            <div
              key={task.id}
              className="rounded-[24px] border border-slate-200 bg-slate-50 p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-900">
                    {task.title}
                  </div>
                  <div className="mt-1 text-sm text-slate-500">
                    {task.node_id} · {formatDate(task.created_at)}
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => router.push(`/processes/${task.process_instance_id}`)}
                >
                  Open
                </Button>
              </div>
              <div className="mt-4 flex gap-2">
                <Button size="sm" onClick={() => completeTask(task.id, "completed")}>
                  <Check className="h-4 w-4" />
                  Complete
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => completeTask(task.id, "revision_requested")}
                >
                  <RotateCcw className="h-4 w-4" />
                  Revision
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Bekleyen onaylar</CardTitle>
          <CardDescription>
            Approval matrix ve delegation fallback bu kuyrugu doldurur.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {inbox.approvals.map((approval) => (
            <div
              key={approval.id}
              className="rounded-[24px] border border-slate-200 bg-slate-50 p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-900">
                    {approval.approver_role ?? "Approver"}
                  </div>
                  <div className="mt-1 text-sm text-slate-500">
                    {approval.node_id} · {formatDate(approval.created_at)}
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => router.push(`/processes/${approval.process_instance_id}`)}
                >
                  Open
                </Button>
              </div>
              <div className="mt-4 flex gap-2">
                <Button size="sm" onClick={() => decideApproval(approval.id, "approved")}>
                  <Check className="h-4 w-4" />
                  Approve
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => decideApproval(approval.id, "rejected")}
                >
                  <X className="h-4 w-4" />
                  Reject
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
