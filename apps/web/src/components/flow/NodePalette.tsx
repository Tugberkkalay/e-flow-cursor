"use client";
import { useState } from "react";
import { NODE_REGISTRY, NODE_CATEGORIES } from "@/lib/nodeRegistry";
import { Search } from "lucide-react";
import { nodeTypeColor } from "@/lib/utils";

interface Props {
  onDragStart: (event: React.DragEvent, engineType: string, label: string) => void;
}

export function NodePalette({ onDragStart }: Props) {
  const [activeCategory, setActiveCategory] = useState("all");
  const [search, setSearch] = useState("");

  const filtered = NODE_REGISTRY.filter(n => {
    const matchCat = activeCategory === "all" || n.category === activeCategory;
    const matchSearch = !search || n.label.toLowerCase().includes(search.toLowerCase()) || n.engineType.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchSearch;
  });

  const grouped = NODE_CATEGORIES.filter(c => c.id !== "all").map(cat => ({
    ...cat,
    items: filtered.filter(n => n.category === cat.id),
  })).filter(g => g.items.length > 0);

  return (
    <div className="w-[220px] flex-shrink-0 bg-surface border-r border-border flex flex-col h-full">
      <div className="px-3 pt-3 pb-2 border-b border-border">
        <div className="relative">
          <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-accent-muted" />
          <input
            type="text"
            className="input pl-7 text-xs py-1.5"
            placeholder="Node ara..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="flex flex-wrap gap-1 mt-2">
          {NODE_CATEGORIES.slice(0, 5).map(cat => (
            <button
              key={cat.id}
              className={`text-[10px] font-medium px-2 py-1 rounded-md transition-colors ${
                activeCategory === cat.id
                  ? "bg-accent text-white"
                  : "bg-secondary text-accent-muted hover:bg-surface-hover"
              }`}
              onClick={() => setActiveCategory(cat.id)}
            >
              {cat.label}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-1 mt-1">
          {NODE_CATEGORIES.slice(5).map(cat => (
            <button
              key={cat.id}
              className={`text-[10px] font-medium px-2 py-1 rounded-md transition-colors ${
                activeCategory === cat.id
                  ? "bg-accent text-white"
                  : "bg-secondary text-accent-muted hover:bg-surface-hover"
              }`}
              onClick={() => setActiveCategory(cat.id)}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2">
        {activeCategory === "all" ? (
          grouped.map(group => (
            <div key={group.id} className="mb-3">
              <div className="text-[10px] font-semibold text-accent-muted uppercase tracking-wider mb-1.5 px-0.5">
                {group.label}
              </div>
              <div className="space-y-1">
                {group.items.map(n => (
                  <PaletteItem key={n.engineType} node={n} onDragStart={onDragStart} />
                ))}
              </div>
            </div>
          ))
        ) : (
          <div className="space-y-1 pt-1">
            {filtered.map(n => (
              <PaletteItem key={n.engineType} node={n} onDragStart={onDragStart} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function PaletteItem({ node, onDragStart }: {
  node: typeof NODE_REGISTRY[0];
  onDragStart: (e: React.DragEvent, et: string, l: string) => void;
}) {
  const colors = nodeTypeColor(node.engineType);
  return (
    <div
      draggable
      onDragStart={e => onDragStart(e, node.engineType, node.label)}
      className={`
        flex items-center gap-2.5 px-2.5 py-2 rounded-lg cursor-grab active:cursor-grabbing
        border ${colors.border} ${colors.bg}
        hover:shadow-sm transition-all duration-100
        select-none
      `}
      title={node.description}
    >
      <span className="text-sm leading-none flex-shrink-0">{node.icon}</span>
      <div className="min-w-0">
        <div className={`text-xs font-medium ${colors.text} truncate`}>{node.label}</div>
      </div>
    </div>
  );
}
