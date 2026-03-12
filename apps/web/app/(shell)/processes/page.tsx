import { ProcessList } from "@/components/processes/process-list";
import { getApiBaseUrl, getDemoToken, getFlows, getInstances } from "@/lib/api";

export default async function ProcessesPage() {
  const [instances, flows, token] = await Promise.all([
    getInstances(),
    getFlows(),
    getDemoToken(),
  ]);

  return (
    <ProcessList
      initialInstances={instances}
      flows={flows}
      token={token}
      apiBaseUrl={getApiBaseUrl()}
    />
  );
}
