"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Workflow } from "lucide-react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@eflow.io");
  const [password, setPassword] = useState("admin123");

  const handleLogin = () => {
    localStorage.setItem("eflow_token", "demo_token");
    router.push("/dashboard");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F7F8FA]">
      <Card className="w-full max-w-sm border-0 shadow-lg">
        <CardContent className="p-8">
          <div className="flex flex-col items-center mb-8">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary mb-3">
              <Workflow className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-xl font-semibold tracking-tight">e-Flow Enterprise</h1>
            <p className="text-sm text-muted-foreground mt-1">BPM & Workflow Platform</p>
          </div>
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">E-posta</label>
              <Input value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Şifre</label>
              <Input value={password} onChange={(e) => setPassword(e.target.value)} type="password" />
            </div>
            <Button className="w-full" onClick={handleLogin}>Giriş Yap</Button>
          </div>
          <p className="text-xs text-center text-muted-foreground mt-6">
            Demo: admin@eflow.io / admin123
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
