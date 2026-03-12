import { InboxBoard } from "@/components/inbox/inbox-board";
import { getApiBaseUrl, getDemoToken, getInbox } from "@/lib/api";

export default async function InboxPage() {
  const [inbox, token] = await Promise.all([getInbox(), getDemoToken()]);

  return (
    <InboxBoard
      initialInbox={inbox}
      token={token}
      apiBaseUrl={getApiBaseUrl()}
    />
  );
}
