"use client";
import { useParams } from "next/navigation";
import { FlowDesigner } from "@/components/flow/FlowDesigner";

export default function FlowDesignerPage() {
  const params = useParams();
  const flowId = params.flowId as string;
  return <FlowDesigner flowId={flowId} />;
}
