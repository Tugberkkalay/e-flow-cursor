export type FlowTemplate = {
  code: string;
  name: string;
  description: string;
  domain: string;
  highlights: string[];
};

export const DOMAIN_TEMPLATES: FlowTemplate[] = [
  {
    code: "tpl_pr_request",
    name: "Satın Alma Talebi (PR)",
    domain: "Procurement",
    description:
      "Form submit ile başlayan, teklif zorunluluğu ve policy check adımları olan PR akışı.",
    highlights: ["Offer threshold", "Policy check", "Exports contract"],
  },
  {
    code: "tpl_p2p",
    name: "Satın Alma Süreci (P2P)",
    domain: "Procurement",
    description:
      "Vendor selection + limit matrix approval + mock ERP/Email adımlarını içeren uçtan uca satın alma akışı.",
    highlights: ["Approval matrix", "PO generation", "ERP mock"],
  },
  {
    code: "tpl_contract",
    name: "Sözleşme Süreci",
    domain: "Legal & Finance",
    description:
      "Revizyon döngüsü, legal/finance approval ve e-sign/archive stub’ları olan sözleşme süreci.",
    highlights: ["Revision loop", "Signature stub", "Timer notify"],
  },
  {
    code: "tpl_invoice_payment",
    name: "Sipariş / Fatura / Ödeme",
    domain: "Finance",
    description:
      "Invoice extract + match switch + dispute/resume kurgusuyla ödeme hazırlayan finance akışı.",
    highlights: ["Match switch", "Dispute task", "Payment HTTP mock"],
  },
];
