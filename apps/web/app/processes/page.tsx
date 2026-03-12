"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { DOMAIN_TEMPLATES } from "@/lib/templates";

type StatusFilter = "all" | "running" | "approved" | "rejected" | "cancelled";

const INSTANCES = [
  {
    id: "ins_1001",
    title: "PR - Office Equipment",
    requester: "Mert Demir",
    status: "running",
    activeStep: "Approval by Matrix",
    sla: "3h",
    date: "2026-03-11",
  },
  {
    id: "ins_1002",
    title: "Contract - Vendor A",
    requester: "Selin Kaya",
    status: "approved",
    activeStep: "Completed",
    sla: "-",
    date: "2026-03-10",
  },
  {
    id: "ins_1003",
    title: "Invoice 2026/344",
    requester: "Can Yılmaz",
    status: "rejected",
    activeStep: "Dispute Task",
    sla: "overdue",
    date: "2026-03-09",
  },
];

export default function ProcessesPage() {
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("Yeni Süreç");
  const [template, setTemplate] = useState(DOMAIN_TEMPLATES[0]?.code);

  const filtered = useMemo(
    () =>
      INSTANCES.filter((item) =>
        filter === "all" ? true : item.status === filter,
      ),
    [filter],
  );

  return (
    <AppShell
      title="Süreçler"
      subtitle="Process Instances · lazy runtime snapshots"
      actionSlot={
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>Süreç Başlat</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Süreç Başlat</DialogTitle>
              <DialogDescription>
                Published flow seçin ve initial input değerlerini girin.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3">
              <label className="text-sm font-medium">Başlık</label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} />
              <label className="text-sm font-medium">Template</label>
              <select
                value={template}
                onChange={(e) => setTemplate(e.target.value)}
                className="h-10 w-full rounded-xl border border-[#DEE3EA] px-3 text-sm"
              >
                {DOMAIN_TEMPLATES.map((tpl) => (
                  <option key={tpl.code} value={tpl.code}>
                    {tpl.name}
                  </option>
                ))}
              </select>
              <Button onClick={() => setOpen(false)} className="w-full">
                Başlat (MVP)
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      }
    >
      <div className="mb-4 flex flex-wrap gap-2">
        {[
          ["all", "Tümü"],
          ["running", "İşlemde"],
          ["approved", "Onaylandı"],
          ["rejected", "Reddedildi"],
          ["cancelled", "İptal"],
        ].map(([value, label]) => (
          <Button
            key={value}
            variant={filter === value ? "default" : "secondary"}
            size="sm"
            onClick={() => setFilter(value as StatusFilter)}
          >
            {label}
          </Button>
        ))}
      </div>
      <div className="overflow-hidden rounded-2xl border border-[#E7EBF0]">
        <table className="w-full text-sm">
          <thead className="bg-[#FAFBFD] text-left text-[#5A6678]">
            <tr>
              <th className="px-4 py-3">Başlık</th>
              <th className="px-4 py-3">Talep Eden</th>
              <th className="px-4 py-3">Durum</th>
              <th className="px-4 py-3">Aktif Adım</th>
              <th className="px-4 py-3">SLA</th>
              <th className="px-4 py-3">Tarih</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={row.id} className="border-t border-[#EEF2F7] hover:bg-[#FBFCFE]">
                <td className="px-4 py-3">
                  <Link href={`/processes/${row.id}`} className="font-medium hover:underline">
                    {row.title}
                  </Link>
                </td>
                <td className="px-4 py-3">{row.requester}</td>
                <td className="px-4 py-3">
                  <Badge
                    variant={
                      row.status === "approved"
                        ? "success"
                        : row.status === "rejected"
                          ? "destructive"
                          : "default"
                    }
                  >
                    {row.status}
                  </Badge>
                </td>
                <td className="px-4 py-3">{row.activeStep}</td>
                <td className="px-4 py-3">{row.sla}</td>
                <td className="px-4 py-3">{row.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
