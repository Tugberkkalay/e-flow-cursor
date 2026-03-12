import { Activity, CheckCheck, Clock3, Layers3, Shield } from "lucide-react";

import type { FlowDefinition, Instance, InboxPayload } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatDate } from "@/lib/utils";

export function DashboardOverview({
  flows,
  instances,
  inbox,
  auditCount,
}: {
  flows: FlowDefinition[];
  instances: Instance[];
  inbox: InboxPayload;
  auditCount: number;
}) {
  const stats = [
    {
      label: "Published flows",
      value: flows.filter((flow) => flow.status === "published").length,
      icon: Layers3,
    },
    {
      label: "Running instances",
      value: instances.filter((instance) => instance.status.includes("running") || instance.status.includes("waiting")).length,
      icon: Activity,
    },
    {
      label: "Pending inbox",
      value: inbox.tasks.length + inbox.approvals.length,
      icon: Clock3,
    },
    {
      label: "Immutable audit events",
      value: auditCount,
      icon: Shield,
    },
  ];

  return (
    <div className="space-y-6">
      <section className="grid gap-4 xl:grid-cols-4">
        {stats.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.label}>
              <CardContent className="flex items-start justify-between p-6">
                <div>
                  <div className="text-sm text-slate-500">{item.label}</div>
                  <div className="mt-3 text-3xl font-semibold text-slate-950">
                    {item.value}
                  </div>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-white">
                  <Icon className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Runtime pulse</CardTitle>
            <CardDescription>
              Latest process instances with live current step and export signals.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {instances.slice(0, 6).map((instance) => (
              <div
                key={instance.id}
                className="flex flex-col gap-3 rounded-[24px] border border-slate-200 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between"
              >
                <div>
                  <div className="text-sm font-semibold text-slate-900">
                    {instance.title}
                  </div>
                  <div className="mt-1 text-sm text-slate-500">
                    Active step: {instance.current_node_id ?? "Completed"}
                  </div>
                </div>
                <div className="flex items-center gap-3">
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
                  <div className="text-xs text-slate-400">
                    {formatDate(instance.updated_at)}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Design + compliance snapshot</CardTitle>
            <CardDescription>
              System seeds four domain templates and keeps flow versions pinned.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {flows.slice(0, 4).map((flow) => (
              <div
                key={flow.id}
                className="rounded-[24px] border border-slate-200 bg-slate-50 p-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-slate-900">
                      {flow.name}
                    </div>
                    <div className="mt-1 text-sm text-slate-500">
                      {flow.description}
                    </div>
                  </div>
                  <CheckCheck className="h-5 w-5 text-slate-400" />
                </div>
                <div className="mt-4 flex gap-2">
                  <Badge tone={flow.is_template ? "default" : "muted"}>
                    {flow.is_template ? "Template" : "Custom"}
                  </Badge>
                  <Badge tone="success">v{flow.latest_version}</Badge>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
