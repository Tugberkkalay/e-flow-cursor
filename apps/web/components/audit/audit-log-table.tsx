"use client";

import { useMemo } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatDate } from "@/lib/utils";

export function AuditLogTable({
  events,
}: {
  events: Array<{
    id: string;
    event_type: string;
    entity_type: string;
    entity_id: string;
    actor_user_id?: string | null;
    process_instance_id?: string | null;
    payload_json: Record<string, unknown>;
    created_at: string;
  }>;
}) {
  const downloadCsv = () => {
    const header = [
      "id",
      "event_type",
      "entity_type",
      "entity_id",
      "actor_user_id",
      "process_instance_id",
      "created_at",
      "payload_json",
    ];
    const rows = events.map((event) =>
      [
        event.id,
        event.event_type,
        event.entity_type,
        event.entity_id,
        event.actor_user_id ?? "",
        event.process_instance_id ?? "",
        event.created_at,
        JSON.stringify(event.payload_json),
      ]
        .map((value) => `"${String(value).replaceAll('"', '""')}"`)
        .join(","),
    );
    const blob = new Blob([[header.join(","), ...rows].join("\n")], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "audit-events.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const filtered = useMemo(() => events, [events]);

  return (
    <Card>
      <CardHeader className="border-b border-slate-100">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <CardTitle>Audit</CardTitle>
            <CardDescription>
              Eventler silinemez. CSV export ile disari alinabilir.
            </CardDescription>
          </div>
          <Button variant="secondary" onClick={downloadCsv}>
            Export CSV
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-6 py-4 font-medium">Event</th>
                <th className="px-6 py-4 font-medium">Entity</th>
                <th className="px-6 py-4 font-medium">Instance</th>
                <th className="px-6 py-4 font-medium">Payload</th>
                <th className="px-6 py-4 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((event) => (
                <tr key={event.id} className="border-t border-slate-100">
                  <td className="px-6 py-4 font-medium text-slate-900">
                    {event.event_type}
                  </td>
                  <td className="px-6 py-4 text-slate-500">
                    {event.entity_type} / {event.entity_id.slice(0, 8)}
                  </td>
                  <td className="px-6 py-4 text-slate-500">
                    {event.process_instance_id?.slice(0, 8) ?? "-"}
                  </td>
                  <td className="px-6 py-4 text-slate-500">
                    <pre className="max-w-[520px] overflow-x-auto whitespace-pre-wrap rounded-2xl bg-slate-50 p-2 text-xs">
                      {JSON.stringify(event.payload_json, null, 2)}
                    </pre>
                  </td>
                  <td className="px-6 py-4 text-slate-500">
                    {formatDate(event.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
