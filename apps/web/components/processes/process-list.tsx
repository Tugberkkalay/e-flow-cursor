"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Play, Search } from "lucide-react";

import type { FlowDefinition, Instance } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input, Textarea } from "@/components/ui/input";
import { formatDate } from "@/lib/utils";

export function ProcessList({
  initialInstances,
  flows,
  token,
  apiBaseUrl,
}: {
  initialInstances: Instance[];
  flows: FlowDefinition[];
  token: string;
  apiBaseUrl: string;
}) {
  const router = useRouter();
  const [instances, setInstances] = useState(initialInstances);
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [selectedVersionId, setSelectedVersionId] = useState(
    flows.find((flow) => flow.status === "published")?.version_id ?? "",
  );
  const [jsonPayload, setJsonPayload] = useState(
    JSON.stringify(
      {
        request_title: "Enterprise laptop alimi",
        request_type: "Standart",
        department: "Operations",
        budget_type: "default",
        currency: "TRY",
        vat_rate: 20,
        line_items: [{ item_name: "MacBook Pro", quantity: 2, unit_price: 90000 }],
      },
      null,
      2,
    ),
  );

  const filtered = useMemo(() => {
    return instances.filter((instance) => {
      const matchesFilter =
        filter === "all" ? true : instance.status.toLowerCase().includes(filter);
      const matchesQuery = `${instance.title} ${instance.current_node_id ?? ""}`
        .toLowerCase()
        .includes(query.toLowerCase());
      return matchesFilter && matchesQuery;
    });
  }, [filter, instances, query]);

  const startInstance = async () => {
    const response = await fetch(`${apiBaseUrl}/instances/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        flow_version_id: selectedVersionId,
        initial_inputs: JSON.parse(jsonPayload),
      }),
    });
    const instance = (await response.json()) as Instance;
    setInstances((current) => [instance, ...current]);
    router.push(`/processes/${instance.id}`);
    router.refresh();
  };

  return (
    <Card>
      <CardHeader className="border-b border-slate-100">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <CardTitle>Process Instances</CardTitle>
            <CardDescription>
              Tumu / Islemde / Onaylandi / Reddedildi / Iptal filtreleri ile
              live operational view.
            </CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative min-w-[260px]">
              <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                className="pl-10"
                placeholder="Baslik veya aktif adim ara..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </div>
            <div className="flex rounded-2xl border border-slate-200 bg-white p-1">
              {["all", "waiting", "completed", "rejected", "cancelled"].map((key) => (
                <button
                  key={key}
                  className={`rounded-xl px-3 py-2 text-sm ${
                    filter === key
                      ? "bg-slate-950 text-white"
                      : "text-slate-500 transition hover:bg-slate-50"
                  }`}
                  onClick={() => setFilter(key)}
                >
                  {key}
                </button>
              ))}
            </div>
            <Dialog>
              <DialogTrigger asChild>
                <Button>
                  <Play className="h-4 w-4" />
                  Surec Baslat
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Published flow sec ve instance baslat</DialogTitle>
                  <DialogDescription>
                    Initial inputs JSON, form submit veya manual start trigger’i
                    icin demo payload olarak kullanilir.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <select
                    className="h-11 w-full rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-600 outline-none"
                    value={selectedVersionId}
                    onChange={(event) => setSelectedVersionId(event.target.value)}
                  >
                    {flows
                      .filter((flow) => flow.version_id && flow.status === "published")
                      .map((flow) => (
                        <option key={flow.id} value={flow.version_id ?? ""}>
                          {flow.name} v{flow.latest_version}
                        </option>
                      ))}
                  </select>
                  <Textarea
                    value={jsonPayload}
                    onChange={(event) => setJsonPayload(event.target.value)}
                  />
                  <Button className="w-full" onClick={startInstance}>
                    Start instance
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-6 py-4 font-medium">Baslik</th>
                <th className="px-6 py-4 font-medium">Talep Eden</th>
                <th className="px-6 py-4 font-medium">Durum</th>
                <th className="px-6 py-4 font-medium">Aktif Adim</th>
                <th className="px-6 py-4 font-medium">SLA</th>
                <th className="px-6 py-4 font-medium">Tarih</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((instance) => (
                <tr
                  key={instance.id}
                  className="cursor-pointer border-t border-slate-100 transition hover:bg-slate-50"
                  onClick={() => router.push(`/processes/${instance.id}`)}
                >
                  <td className="px-6 py-4 font-medium text-slate-900">
                    {instance.title}
                  </td>
                  <td className="px-6 py-4 text-slate-500">
                    {instance.requester?.full_name ?? "-"}
                  </td>
                  <td className="px-6 py-4">
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
                  </td>
                  <td className="px-6 py-4 text-slate-500">
                    {instance.current_node_id ?? "Ended"}
                  </td>
                  <td className="px-6 py-4 text-slate-500">
                    {instance.status.includes("waiting") ? "Action pending" : "Within SLA"}
                  </td>
                  <td className="px-6 py-4 text-slate-500">
                    {formatDate(instance.started_at)}
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
