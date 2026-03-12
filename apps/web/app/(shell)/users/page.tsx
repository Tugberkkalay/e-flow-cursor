import { AdminConsole } from "@/components/admin/admin-console";
import {
  getApprovalLimits,
  getDelegations,
  getUsers,
} from "@/lib/api";

export default async function UsersPage() {
  const [users, delegations, approvalLimits] = await Promise.all([
    getUsers(),
    getDelegations(),
    getApprovalLimits(),
  ]);

  return (
    <AdminConsole
      users={users}
      delegations={delegations}
      approvalLimits={approvalLimits}
    />
  );
}
