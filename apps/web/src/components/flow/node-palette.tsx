"use client";

import React, { useState, useMemo } from "react";
import { Search, Star, GripVertical } from "lucide-react";
import * as LucideIcons from "lucide-react";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { NODE_CATEGORIES, NODE_REGISTRY, NodeDefinition, searchNodes, getNodesByCategory } from "@/lib/node-registry";
import { NodeCategory } from "@/types";

function getIcon(iconName: string) {
  const icons = LucideIcons as any;
  return icons[iconName] || icons.Circle;
}

interface NodePaletteProps {
  onDragStart: (event: React.DragEvent, nodeDef: NodeDefinition) => void;
}

export function NodePalette({ onDragStart }: NodePaletteProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<NodeCategory | "all">("all");
  const [favorites, setFavorites] = useState<Set<string>>(new Set(["form_fill", "approval_single", "if_condition", "http_request"]));

  const filteredNodes = useMemo(() => {
    if (searchQuery) return searchNodes(searchQuery);
    if (activeCategory === "all") return NODE_REGISTRY;
    return getNodesByCategory(activeCategory);
  }, [searchQuery, activeCategory]);

  const favoriteNodes = useMemo(
    () => NODE_REGISTRY.filter((n) => favorites.has(n.type)),
    [favorites]
  );

  const toggleFavorite = (type: string) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  return (
    <div className="flex h-full flex-col bg-white">
      {/* Search */}
      <div className="p-3 border-b">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Node ara..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8 pl-8 text-xs bg-gray-50 border-0"
          />
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex flex-wrap gap-1 px-3 py-2 border-b">
        <button
          onClick={() => { setActiveCategory("all"); setSearchQuery(""); }}
          className={cn(
            "rounded-md px-2 py-1 text-[10px] font-medium transition-colors",
            activeCategory === "all"
              ? "bg-primary text-white"
              : "text-muted-foreground hover:bg-gray-100"
          )}
        >
          Tümü
        </button>
        {NODE_CATEGORIES.map((cat) => {
          const CatIcon = getIcon(cat.icon);
          return (
            <button
              key={cat.key}
              onClick={() => { setActiveCategory(cat.key); setSearchQuery(""); }}
              className={cn(
                "flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium transition-colors",
                activeCategory === cat.key
                  ? "bg-primary text-white"
                  : "text-muted-foreground hover:bg-gray-100"
              )}
            >
              <CatIcon className="h-3 w-3" />
              {cat.label}
            </button>
          );
        })}
      </div>

      {/* Favorites */}
      {!searchQuery && activeCategory === "all" && favoriteNodes.length > 0 && (
        <div className="px-3 py-2 border-b">
          <div className="flex items-center gap-1.5 mb-1.5">
            <Star className="h-3 w-3 text-amber-500 fill-amber-500" />
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Favoriler</span>
          </div>
          <div className="space-y-0.5">
            {favoriteNodes.map((node) => (
              <PaletteNodeItem
                key={node.type}
                node={node}
                isFavorite
                onDragStart={onDragStart}
                onToggleFavorite={toggleFavorite}
              />
            ))}
          </div>
        </div>
      )}

      {/* Node List */}
      <ScrollArea className="flex-1">
        <div className="px-3 py-2 space-y-0.5">
          {filteredNodes.map((node) => (
            <PaletteNodeItem
              key={node.type}
              node={node}
              isFavorite={favorites.has(node.type)}
              onDragStart={onDragStart}
              onToggleFavorite={toggleFavorite}
            />
          ))}
          {filteredNodes.length === 0 && (
            <div className="py-8 text-center text-xs text-muted-foreground">
              Sonuç bulunamadı
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

function PaletteNodeItem({
  node,
  isFavorite,
  onDragStart,
  onToggleFavorite,
}: {
  node: NodeDefinition;
  isFavorite: boolean;
  onDragStart: (event: React.DragEvent, nodeDef: NodeDefinition) => void;
  onToggleFavorite: (type: string) => void;
}) {
  const Icon = getIcon(node.icon);

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, node)}
      className="group flex items-center gap-2 rounded-lg px-2 py-1.5 cursor-grab active:cursor-grabbing hover:bg-gray-50 transition-colors"
    >
      <GripVertical className="h-3 w-3 text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
      <div
        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md"
        style={{ backgroundColor: node.bgColor }}
      >
        <Icon className="h-3.5 w-3.5" style={{ color: node.color }} strokeWidth={1.8} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[11px] font-medium text-gray-700 truncate">{node.label}</div>
      </div>
      <button
        onClick={(e) => { e.stopPropagation(); onToggleFavorite(node.type); }}
        className="opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <Star
          className={cn(
            "h-3 w-3",
            isFavorite ? "text-amber-500 fill-amber-500" : "text-gray-300"
          )}
        />
      </button>
    </div>
  );
}
