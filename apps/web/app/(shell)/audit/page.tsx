import { AuditLogTable } from "@/components/audit/audit-log-table";
import { getAudit } from "@/lib/api";

export default async function AuditPage() {
  const audit = await getAudit();
  return <AuditLogTable events={audit} />;
}
