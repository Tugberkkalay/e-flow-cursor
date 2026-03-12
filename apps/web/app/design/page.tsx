"use client";

import { useState } from "react";

import { DesignerStudio } from "@/components/design/designer-studio";
import { FormBuilder } from "@/components/design/form-builder";
import { AppShell } from "@/components/shell/app-shell";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function DesignPage() {
  const [tab, setTab] = useState("flow");

  return (
    <AppShell
      title="Tasarım"
      subtitle="Flow Designer + Dynamic Form Builder"
      actionSlot={
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="flow">Flow Designer</TabsTrigger>
            <TabsTrigger value="form">Form Builder</TabsTrigger>
          </TabsList>
        </Tabs>
      }
    >
      {tab === "flow" ? <DesignerStudio /> : <FormBuilder />}
    </AppShell>
  );
}
