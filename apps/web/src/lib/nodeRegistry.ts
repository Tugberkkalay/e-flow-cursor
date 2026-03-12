export interface NodeDef {
  engineType: string;
  label: string;
  category: string;
  categoryLabel: string;
  icon: string;
  description: string;
  defaultConfig: Record<string, unknown>;
  outputs: { id: string; label: string }[];
  isBranching?: boolean;
}

export const NODE_REGISTRY: NodeDef[] = [
  // Triggers
  { engineType: "ManualStart", label: "Manuel Başlat", category: "triggers", categoryLabel: "Tetikleyiciler", icon: "▶", description: "Süreci manuel başlatır", defaultConfig: {}, outputs: [{ id: "out", label: "Çıkış" }] },
  { engineType: "FormSubmitTrigger", label: "Form Gönder", category: "triggers", categoryLabel: "Tetikleyiciler", icon: "📋", description: "Form gönderiminde tetiklenir", defaultConfig: {}, outputs: [{ id: "out", label: "Çıkış" }] },
  { engineType: "APITrigger", label: "API Tetikleyici", category: "triggers", categoryLabel: "Tetikleyiciler", icon: "🔌", description: "Webhook/API çağrısında başlar", defaultConfig: { path: "/webhook/start" }, outputs: [{ id: "out", label: "Çıkış" }] },
  { engineType: "ScheduledTrigger", label: "Zamanlanmış", category: "triggers", categoryLabel: "Tetikleyiciler", icon: "⏰", description: "Cron ifadesiyle tetiklenir", defaultConfig: { cron: "0 9 * * *" }, outputs: [{ id: "out", label: "Çıkış" }] },

  // Human Tasks
  { engineType: "FormFill", label: "Form Doldur", category: "human", categoryLabel: "Görevler", icon: "📝", description: "Kullanıcıya form doldurma görevi", defaultConfig: { title: "Form Doldur", assignee_role: "" }, outputs: [{ id: "out", label: "Tamamlandı" }] },
  { engineType: "DataEntry", label: "Veri Girişi", category: "human", categoryLabel: "Görevler", icon: "⌨", description: "Manuel veri girişi", defaultConfig: { title: "Veri Girişi", assignee_role: "" }, outputs: [{ id: "out", label: "Tamamlandı" }] },
  { engineType: "DocumentUpload", label: "Belge Yükle", category: "human", categoryLabel: "Görevler", icon: "📎", description: "Belge yükleme görevi", defaultConfig: { title: "Belge Yükleyin", doc_type: "generic", min_count: 1, assignee_role: "" }, outputs: [{ id: "out", label: "Yüklendi" }] },
  { engineType: "ReviewComment", label: "İncele & Yorum", category: "human", categoryLabel: "Görevler", icon: "💬", description: "İnceleme ve yorum görevi", defaultConfig: { title: "İnceleyin ve Yorum Yapın", assignee_role: "" }, outputs: [{ id: "out", label: "Tamamlandı" }] },
  { engineType: "VendorSelection", label: "Tedarikçi Seçimi", category: "human", categoryLabel: "Görevler", icon: "🏪", description: "Teklifler arasından seçim", defaultConfig: { title: "Tedarikçi Seçin", assignee_role: "procurement" }, outputs: [{ id: "out", label: "Seçildi" }] },
  { engineType: "DeliveryAcceptance", label: "Teslimat Kabulü", category: "human", categoryLabel: "Görevler", icon: "📦", description: "Teslimat kontrolü ve kabulü", defaultConfig: { title: "Teslimatı Onaylayın", assignee_role: "" }, outputs: [{ id: "out", label: "Onaylandı" }] },
  { engineType: "ReworkTask", label: "Yeniden Çalışma", category: "human", categoryLabel: "Görevler", icon: "🔄", description: "Düzeltme / revizyon görevi", defaultConfig: { title: "Revizyon Yapın", assignee_role: "" }, outputs: [{ id: "out", label: "Tamamlandı" }] },
  { engineType: "ManualCompensation", label: "Manuel Telafi", category: "human", categoryLabel: "Görevler", icon: "↩", description: "Hata telafi görevi", defaultConfig: { title: "Telafi İşlemi Yapın", assignee_role: "" }, outputs: [{ id: "out", label: "Tamamlandı" }] },

  // Approval
  { engineType: "ApprovalTask", label: "Onay", category: "approval", categoryLabel: "Onaylar", icon: "✅", description: "Tek onay adımı", defaultConfig: { title: "Onay Bekliyor", approver_role: "approver" }, outputs: [{ id: "approved", label: "Onaylandı" }, { id: "rejected", label: "Reddedildi" }], isBranching: true },
  { engineType: "MultiApproval", label: "Çoklu Onay", category: "approval", categoryLabel: "Onaylar", icon: "✅✅", description: "Birden fazla onaylayıcı", defaultConfig: { strategy: "all", approver_roles: [] }, outputs: [{ id: "approved", label: "Onaylandı" }, { id: "rejected", label: "Reddedildi" }], isBranching: true },
  { engineType: "ApprovalByLimitMatrix", label: "Limit Matrisli Onay", category: "approval", categoryLabel: "Onaylar", icon: "💰✅", description: "Onay limiti matrisine göre yönlendir", defaultConfig: { amount_expr: "{{ form.total_amount }}" }, outputs: [{ id: "approved", label: "Onaylandı" }, { id: "rejected", label: "Reddedildi" }], isBranching: true },

  // Logic
  { engineType: "IF", label: "Koşul (IF)", category: "logic", categoryLabel: "Mantık", icon: "⚡", description: "Koşullu dallanma", defaultConfig: { branches: [{ label: "Evet", handle: "true", condition: {} }, { label: "Hayır", handle: "false", condition: {} }] }, outputs: [{ id: "true", label: "Evet" }, { id: "false", label: "Hayır" }], isBranching: true },
  { engineType: "Switch", label: "Çoklu Koşul", category: "logic", categoryLabel: "Mantık", icon: "🔀", description: "Çok yönlü dallanma", defaultConfig: { branches: [] }, outputs: [], isBranching: true },
  { engineType: "ParallelSplit", label: "Paralel Ayrım", category: "logic", categoryLabel: "Mantık", icon: "⫸", description: "Eş zamanlı çalıştırma", defaultConfig: {}, outputs: [] },
  { engineType: "ParallelJoin", label: "Paralel Birleşim", category: "logic", categoryLabel: "Mantık", icon: "⫷", description: "Eş zamanlı akışları birleştir", defaultConfig: { strategy: "all" }, outputs: [{ id: "out", label: "Tamamlandı" }] },

  // Data
  { engineType: "Calculate", label: "Hesapla", category: "data", categoryLabel: "Veri", icon: "🧮", description: "Hesaplama ve formüller", defaultConfig: { calculations: [] }, outputs: [{ id: "out", label: "Çıkış" }] },
  { engineType: "SetFields", label: "Alan Ata", category: "data", categoryLabel: "Veri", icon: "📋→", description: "Context alanı ata/güncelle", defaultConfig: { mappings: [] }, outputs: [{ id: "out", label: "Çıkış" }] },
  { engineType: "Transform", label: "Dönüştür", category: "data", categoryLabel: "Veri", icon: "🔄", description: "Veri dönüşümü ve eşleme", defaultConfig: { mappings: [] }, outputs: [{ id: "out", label: "Çıkış" }] },
  { engineType: "NormalizeMoney", label: "Para Normalize", category: "data", categoryLabel: "Veri", icon: "💱", description: "Kur dönüşümü ve normalizasyon", defaultConfig: { amount_field: "form.total_amount", currency_field: "form.currency" }, outputs: [{ id: "out", label: "Çıkış" }] },
  { engineType: "ThreeWayMatch", label: "3-Yön Eşleştir", category: "data", categoryLabel: "Veri", icon: "🔗", description: "PO-Teslim-Fatura eşleştirmesi", defaultConfig: { po_amount: "", invoice_amount: "", tolerance_pct: 5 }, outputs: [{ id: "out", label: "Çıkış" }] },
  { engineType: "PolicyCheck", label: "Politika Kontrolü", category: "compliance", categoryLabel: "Uyum", icon: "🛡", description: "Kural ve politika kontrolü", defaultConfig: { rules: [] }, outputs: [{ id: "out", label: "Çıkış" }] },

  // Integrations
  { engineType: "HTTPRequest", label: "HTTP İsteği", category: "integrations", categoryLabel: "Entegrasyonlar", icon: "🌐", description: "REST API çağrısı", defaultConfig: { url: "", method: "POST", mock: true }, outputs: [{ id: "out", label: "Yanıt" }] },
  { engineType: "EmailSend", label: "E-posta Gönder", category: "integrations", categoryLabel: "Entegrasyonlar", icon: "📧", description: "E-posta bildirimi", defaultConfig: { to: "", subject: "", body: "", mock: true }, outputs: [{ id: "out", label: "Gönderildi" }] },
  { engineType: "ERPAdapter", label: "ERP Adaptörü", category: "integrations", categoryLabel: "Entegrasyonlar", icon: "🏭", description: "ERP sistem entegrasyonu (Mock)", defaultConfig: { erp_type: "mock", action: "" }, outputs: [{ id: "out", label: "Yanıt" }] },
  { engineType: "SubprocessCall", label: "Alt Süreç Çağır", category: "integrations", categoryLabel: "Entegrasyonlar", icon: "📦", description: "Başka bir süreci çağır", defaultConfig: { subprocess_flow_id: "", input_mapping: {}, output_mapping: {} }, outputs: [{ id: "out", label: "Tamamlandı" }] },

  // Compliance
  { engineType: "AuditEmit", label: "Denetim Kaydet", category: "compliance", categoryLabel: "Uyum", icon: "📓", description: "Özel denetim olayı yayınla", defaultConfig: { event_type: "custom", message: "" }, outputs: [{ id: "out", label: "Çıkış" }] },
  { engineType: "StopError", label: "Hata ile Dur", category: "compliance", categoryLabel: "Uyum", icon: "🛑", description: "Kontrollü hata durumu", defaultConfig: { error_message: "Süreç hatayla durduruldu" }, outputs: [] },

  // Events
  { engineType: "End", label: "Bitiş", category: "events", categoryLabel: "Olaylar", icon: "⏹", description: "Akışı sonlandır", defaultConfig: { status: "completed", exports: [] }, outputs: [] },
];

export const NODE_CATEGORIES = [
  { id: "all", label: "Tümü" },
  { id: "triggers", label: "Tetikleyiciler" },
  { id: "human", label: "Görevler" },
  { id: "approval", label: "Onaylar" },
  { id: "logic", label: "Mantık" },
  { id: "data", label: "Veri" },
  { id: "integrations", label: "Entegrasyonlar" },
  { id: "compliance", label: "Uyum" },
  { id: "events", label: "Olaylar" },
];

export function getNodeDef(engineType: string): NodeDef | undefined {
  return NODE_REGISTRY.find(n => n.engineType === engineType);
}
