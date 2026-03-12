import { FlowDesigner } from "@/components/designer/flow-designer";
import { getApiBaseUrl, getDemoToken, getFlows, getForms } from "@/lib/api";

export default async function DesignPage() {
  const [flows, forms, token] = await Promise.all([
    getFlows(),
    getForms(),
    getDemoToken(),
  ]);

  return (
    <FlowDesigner
      initialFlows={flows}
      forms={forms}
      token={token}
      apiBaseUrl={getApiBaseUrl()}
    />
  );
}
