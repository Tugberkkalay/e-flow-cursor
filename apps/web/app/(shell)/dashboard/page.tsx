import { DashboardOverview } from "@/components/dashboard/dashboard-overview";
import { getAudit, getFlows, getInbox, getInstances } from "@/lib/api";

export default async function DashboardPage() {
  const [flows, instances, inbox, audit] = await Promise.all([
    getFlows(),
    getInstances(),
    getInbox(),
    getAudit(),
  ]);

  return (
    <DashboardOverview
      flows={flows}
      instances={instances}
      inbox={inbox}
      auditCount={audit.length}
    />
  );
}
