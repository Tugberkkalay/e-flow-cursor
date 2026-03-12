import { notFound } from "next/navigation";

import { ProcessDetail } from "@/components/processes/process-detail";
import { getApiBaseUrl, getDemoToken, getInstance } from "@/lib/api";

export default async function ProcessDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [instance, token] = await Promise.all([
    getInstance(id).catch(() => null),
    getDemoToken(),
  ]);

  if (!instance) {
    notFound();
  }

  return (
    <ProcessDetail
      initialInstance={instance}
      token={token}
      apiBaseUrl={getApiBaseUrl()}
    />
  );
}
