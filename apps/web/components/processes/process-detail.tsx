"use client";

import { useState } from "react";
import { RefreshCcw, SkipForward, StopCircle, UserRoundCog } from "lucide-react";

import type { Instance } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { formatDate } from "@/lib/utils";

export function ProcessDetail({
  initialInstance,
  token,
  apiBaseUrl,
}: {
  initialInstance: Instance;
  token: string;
  apiBaseUrl: string;
}) {
  const [instance, setInstance] = useState(initialInstance);

  const triggerAction = async (action: string) => {
    const response = await fetch(`${apiBaseUrl}/instances/${instance.id}/actions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ action }),
    });
    const next = (await response.json()) as Instance;
    setInstance(next);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="border-b border-slate-100">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div>
              <CardTitle>{instance.title}</CardTitle>
              <CardDescription>
                Immutable timeline, approvals, form snapshot, docs ve control
                flags tek detay ekraninda.
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Badge
                tone={
                  instance.status === "completed"
                    ? "success"
                    : instance.status === "rejected"
                      ? "danger"
                      : "warning"
                }
              >
                {instance.status}
              </Badge>
              <Badge tone="muted">Current: {instance.current_node_id ?? "None"}</Badge>
              <Button variant="secondary" onClick={() => triggerAction("reassign")}>
                <UserRoundCog className="h-4 w-4" />
                Reassign
              </Button>
              <Button variant="secondary" onClick={() => triggerAction("skip")}>
                <SkipForward className="h-4 w-4" />
                Skip Step
              </Button>
              <Button variant="secondary" onClick={() => triggerAction("retry")}>
                <RefreshCcw className="h-4 w-4" />
                Retry failed node
              </Button>
              <Button variant="destructive" onClick={() => triggerAction("cancel")}>
                <StopCircle className="h-4 w-4" />
                Cancel instance
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="grid gap-4 p-6 xl:grid-cols-4">
          <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
              Requester
            </div>
            <div className="mt-2 text-sm font-semibold text-slate-900">
              {instance.requester?.full_name ?? "System"}
            </div>
          </div>
          <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
              Started
            </div>
            <div className="mt-2 text-sm font-semibold text-slate-900">
              {formatDate(instance.started_at)}
            </div>
          </div>
          <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
              Exports
            </div>
            <div className="mt-2 truncate text-sm font-semibold text-slate-900">
              {Object.keys(instance.exports_json ?? {}).length} outputs
            </div>
          </div>
          <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-400">
              Flags
            </div>
            <div className="mt-2 truncate text-sm font-semibold text-slate-900">
              {JSON.stringify(instance.variables_json?.flags ?? {})}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <Tabs defaultValue="timeline">
            <TabsList>
              <TabsTrigger value="timeline">Timeline</TabsTrigger>
              <TabsTrigger value="tasks">Tasks</TabsTrigger>
              <TabsTrigger value="approvals">Approvals</TabsTrigger>
              <TabsTrigger value="form">Form snapshot</TabsTrigger>
              <TabsTrigger value="documents">Documents</TabsTrigger>
              <TabsTrigger value="flags">Controls / Flags</TabsTrigger>
            </TabsList>

            <TabsContent value="timeline">
              <div className="space-y-3">
                {(instance.timeline ?? []).map((event) => (
                  <div
                    key={event.id}
                    className="rounded-[24px] border border-slate-200 bg-slate-50 p-4"
                  >
                    <div className="flex flex-col justify-between gap-3 md:flex-row">
                      <div>
                        <div className="text-sm font-semibold text-slate-900">
                          {event.event_type}
                        </div>
                        <div className="mt-1 text-sm text-slate-500">
                          {JSON.stringify(event.payload_json)}
                        </div>
                      </div>
                      <div className="text-xs text-slate-400">
                        {formatDate(event.created_at)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="tasks">
              <div className="grid gap-4">
                {(instance.tasks ?? []).map((task) => (
                  <div
                    key={task.id}
                    className="rounded-[24px] border border-slate-200 bg-slate-50 p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-semibold text-slate-900">
                          {task.title}
                        </div>
                        <div className="mt-1 text-sm text-slate-500">
                          Node: {task.node_id}
                        </div>
                      </div>
                      <Badge
                        tone={task.status === "completed" ? "success" : "warning"}
                      >
                        {task.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="approvals">
              <div className="grid gap-4">
                {(instance.approvals ?? []).map((approval) => (
                  <div
                    key={approval.id}
                    className="rounded-[24px] border border-slate-200 bg-slate-50 p-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-slate-900">
                          {approval.approver_role ?? "Approver"}
                        </div>
                        <div className="mt-1 text-sm text-slate-500">
                          Decision: {approval.decision ?? "pending"}
                        </div>
                      </div>
                      <Badge
                        tone={
                          approval.decision === "approved"
                            ? "success"
                            : approval.decision === "rejected"
                              ? "danger"
                              : "warning"
                        }
                      >
                        {approval.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="form">
              <pre className="overflow-x-auto rounded-[24px] border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                {JSON.stringify(instance.variables_json?.form ?? {}, null, 2)}
              </pre>
            </TabsContent>

            <TabsContent value="documents">
              <div className="grid gap-4 lg:grid-cols-2">
                {(instance.documents ?? []).map((document) => (
                  <div
                    key={document.id}
                    className="rounded-[24px] border border-slate-200 bg-slate-50 p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-semibold text-slate-900">
                          {document.file_name}
                        </div>
                        <div className="mt-1 text-sm text-slate-500">
                          {document.document_type} · v{document.version}
                        </div>
                      </div>
                      <Badge tone="default">Extracted JSON</Badge>
                    </div>
                    <pre className="mt-4 overflow-x-auto rounded-2xl bg-white p-3 text-xs text-slate-600">
                      {JSON.stringify(document.extracted_json, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="flags">
              <div className="grid gap-4 lg:grid-cols-2">
                <pre className="overflow-x-auto rounded-[24px] border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                  {JSON.stringify(instance.variables_json?.flags ?? {}, null, 2)}
                </pre>
                <pre className="overflow-x-auto rounded-[24px] border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                  {JSON.stringify(instance.exports_json ?? {}, null, 2)}
                </pre>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
