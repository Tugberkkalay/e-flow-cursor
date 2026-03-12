import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function UsersPage() {
  return (
    <AppShell title="Kullanıcılar" subtitle="Users CRUD · Delegation · Approval Limit Matrix">
      <div className="grid grid-cols-12 gap-4">
        <Card className="col-span-7 p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-lg font-semibold">Users</h3>
            <Button size="sm">Yeni Kullanıcı</Button>
          </div>
          <table className="w-full text-sm">
            <thead className="text-left text-[#5A6678]">
              <tr>
                <th className="py-2">Ad</th>
                <th className="py-2">Role</th>
                <th className="py-2">Department</th>
                <th className="py-2">Cost Center</th>
              </tr>
            </thead>
            <tbody>
              {[
                ["System Admin", "admin", "management", "ADM"],
                ["Procurement Approver", "approver", "procurement", "PRC"],
                ["Finance Approver", "approver", "finance", "FIN"],
                ["Legal Reviewer", "viewer", "legal", "LGL"],
              ].map((row) => (
                <tr key={row[0]} className="border-t border-[#EEF2F7]">
                  <td className="py-2">{row[0]}</td>
                  <td className="py-2">
                    <Badge>{row[1]}</Badge>
                  </td>
                  <td className="py-2">{row[2]}</td>
                  <td className="py-2">{row[3]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
        <Card className="col-span-5 p-4">
          <h3 className="mb-2 text-lg font-semibold">Delegation (Vekalet)</h3>
          <div className="space-y-2">
            <Input placeholder="from_user_id" />
            <Input placeholder="to_user_id" />
            <div className="grid grid-cols-2 gap-2">
              <Input type="date" />
              <Input type="date" />
            </div>
            <Button className="w-full" variant="secondary">
              Vekalet Kaydet
            </Button>
          </div>
          <h3 className="mb-2 mt-6 text-lg font-semibold">Approval Limit Matrix</h3>
          <div className="space-y-2 text-sm">
            <div className="rounded-xl border border-[#E8EDF3] bg-[#FAFBFD] p-3">
              0 - 50k → dept manager
            </div>
            <div className="rounded-xl border border-[#E8EDF3] bg-[#FAFBFD] p-3">
              50k - 250k → director
            </div>
            <div className="rounded-xl border border-[#E8EDF3] bg-[#FAFBFD] p-3">
              250k+ → CFO
            </div>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
