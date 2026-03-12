"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";

export function SystemSettings({
  contextSchema,
  token,
  apiBaseUrl,
}: {
  contextSchema: Record<string, unknown>;
  token: string;
  apiBaseUrl: string;
}) {
  const [expression, setExpression] = useState("{{ calc.total_amount >= 50000 }}");
  const [preview, setPreview] = useState<string>("");

  const testExpression = async () => {
    const response = await fetch(`${apiBaseUrl}/expressions/preview`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ expr: expression, context_sample: {} }),
    });
    const payload = (await response.json()) as { result: unknown };
    setPreview(JSON.stringify(payload.result, null, 2));
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <Card>
        <CardHeader>
          <CardTitle>Expression preview</CardTitle>
          <CardDescription>
            {"{{ }}"} runtime expression’lari icin autocomplete-ready context
            schema.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            value={expression}
            onChange={(event) => setExpression(event.target.value)}
          />
          <Button onClick={testExpression}>Preview expression</Button>
          <Textarea readOnly value={preview || "Preview sonucu burada"} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Context schema</CardTitle>
          <CardDescription>
            form.*, docs.*, extract.*, selection.*, approval.*, gen.*, calc.*,
            flags.*, system.*
          </CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="overflow-x-auto rounded-[24px] border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
            {JSON.stringify(contextSchema, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
