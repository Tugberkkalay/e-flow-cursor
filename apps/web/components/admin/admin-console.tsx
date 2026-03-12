import type { User } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function AdminConsole({
  users,
  delegations,
  approvalLimits,
}: {
  users: User[];
  delegations: Array<{
    id: string;
    delegator_id: string;
    delegate_id: string;
    role_scope: string[];
    start_date: string;
    end_date: string;
    is_active: boolean;
  }>;
  approvalLimits: Array<{
    id: string;
    department: string;
    budget_type: string;
    currency: string;
    min_amount: number;
    max_amount: number;
    approver_role: string;
    approver_user_id?: string | null;
  }>;
}) {
  return (
    <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <Card>
        <CardHeader>
          <CardTitle>Users CRUD</CardTitle>
          <CardDescription>
            Roles: admin, approver, viewer · org metadata: department, cost
            center, manager.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {users.map((user) => (
            <div
              key={user.id}
              className="flex flex-col gap-3 rounded-[24px] border border-slate-200 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between"
            >
              <div>
                <div className="text-sm font-semibold text-slate-900">
                  {user.full_name}
                </div>
                <div className="mt-1 text-sm text-slate-500">
                  {user.email} · {user.department ?? "No department"}
                </div>
              </div>
              <div className="flex gap-2">
                <Badge tone="default">{user.role}</Badge>
                <Badge tone="muted">{user.cost_center ?? "-"}</Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Delegation / Vekalet</CardTitle>
            <CardDescription>
              Date range + role scope based delegation fallback.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {delegations.length === 0 ? (
              <div className="rounded-[24px] border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                Demo seed currently has no active delegation.
              </div>
            ) : (
              delegations.map((item) => (
                <div
                  key={item.id}
                  className="rounded-[24px] border border-slate-200 bg-slate-50 p-4"
                >
                  <div className="text-sm font-semibold text-slate-900">
                    {item.delegator_id} → {item.delegate_id}
                  </div>
                  <div className="mt-2 text-sm text-slate-500">
                    {item.start_date} - {item.end_date}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Approval Limit Matrix</CardTitle>
            <CardDescription>
              dept + budget_type + currency + min/max → approver route
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {approvalLimits.map((item) => (
              <div
                key={item.id}
                className="rounded-[24px] border border-slate-200 bg-slate-50 p-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-slate-900">
                    {item.department} / {item.budget_type}
                  </div>
                  <Badge tone="success">{item.approver_role}</Badge>
                </div>
                <div className="mt-2 text-sm text-slate-500">
                  {item.min_amount} - {item.max_amount} {item.currency}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
