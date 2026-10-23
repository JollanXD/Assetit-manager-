import { useState } from 'react';
import { ChevronDown, Layers, Tag, Plus, X, PanelLeftClose, PanelLeftOpen, Settings } from 'lucide-react';
import { navItems, iconRegistry, iconPickerOptions } from '@/lib/nav';
import type { NavSection, Category, CategoryDef } from '@/types';
import Logo from './Logo';

interface SidebarProps {
  width: number;
  collapsed: boolean;
  onToggleCollapse: () => void;
  onOpenSettings: () => void;
  activeNav: NavSection;
  onNavChange: (nav: NavSection) => void;
  categories: CategoryDef[];
  selectedCategories: Set<Category>;
  onToggleCategory: (cat: Category) => void;
  onAddCategory: (name: string, iconName: string) => void;
  onRemoveCategory: (cat: Category) => void;
  tags: string[];
  selectedTags: Set<string>;
  onToggleTag: (tag: string) => void;
  onAddTag: (tag: string) => void;
  onRemoveTag: (tag: string) => void;
  onClearFilters: () => void;
  totalAssets: number;
  totalKits: number;
  totalModels: number;
  totalMaterials: number;
  totalFavorites: number;
  totalImported: number;
}

function Section({
  title, icon: Icon, children, defaultOpen = true, collapsed = false,
}: { title: string; icon: React.ElementType; children: React.ReactNode; defaultOpen?: boolean; collapsed?: boolean; }) {
  const [open, setOpen] = useState(defaultOpen);
  if (collapsed) return null;
  return (
    <div className="border-b border-surface-300">
      <button onClick={() => setOpen(!open)} className="flex w-full items-center gap-2 px-4 py-2.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 hover:text-slate-300 transition-colors">
        <Icon className="h-3 w-3" />
        <span className="flex-1 text-left">{title}</span>
        <ChevronDown className={`h-3 w-3 transition-transform duration-150 ${open ? '' : '-rotate-90'}`} />
      </button>
      {open && <div className="px-3 pb-3 pt-1 animate-fade-in">{children}</div>}
    </div>
  );
}

function SectionHeader({ title, collapsed, onClear }: { title: string; collapsed: boolean; onClear?: () => void; }) {
  if (collapsed) return null;
  return (
    <div className="flex items-center justify-between px-4 py-1.5 border-b border-surface-300">
      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600">{title}</span>
      {onClear && <button onClick={onClear} className="text-[10px] font-semibold uppercase tracking-wide text-accent hover:text-accent-300 transition-colors">Clear</button>}
    </div>
  );
}

export default function Sidebar({
  width, collapsed, onToggleCollapse, onOpenSettings,
  activeNav, onNavChange,
  categories, selectedCategories, onToggleCategory, onAddCategory, onRemoveCategory,
  tags, selectedTags, onToggleTag, onAddTag, onRemoveTag,
  onClearFilters,
  totalAssets, totalKits, totalModels, totalMaterials, totalFavorites, totalImported,
}: SidebarProps) {
  const [newTag, setNewTag] = useState('');
  const [addingTag, setAddingTag] = useState(false);

  const [newCatName, setNewCatName] = useState('');
  const [newCatIcon, setNewCatIcon] = useState(iconPickerOptions[0]);
  const [addingCategory, setAddingCategory] = useState(false);

  const navCounts: Record<NavSection, number> = { all: totalAssets, kits: totalKits, models: totalModels, materials: totalMaterials, favorites: totalFavorites, imported: totalImported };
  const hasActiveFilters = selectedCategories.size > 0 || selectedTags.size > 0;

  const handleAddTag = () => {
    const trimmed = newTag.trim().toLowerCase();
    if (trimmed && !tags.includes(trimmed)) {
      onAddTag(trimmed); setNewTag(''); setAddingTag(false);
    }
  };

  const handleAddCategory = () => {
    const trimmed = newCatName.trim();
    if (trimmed && !categories.some((c) => c.name === trimmed)) {
      onAddCategory(trimmed, newCatIcon);
      setNewCatName(''); setNewCatIcon(iconPickerOptions[0]); setAddingCategory(false);
    }
  };

  const CollapseIcon = collapsed ? PanelLeftOpen : PanelLeftClose;

  return (
    <aside className="flex h-full flex-col border-r border-surface-300 bg-surface-100 flex-shrink-0 transition-[width] duration-150" style={{ width }}>
      {/* Logo header with collapse toggle */}
      <div className="flex items-center gap-2 border-b border-surface-300 px-2 py-3.5">
        <button onClick={onToggleCollapse} className="flex h-7 w-7 flex-shrink-0 items-center justify-center text-slate-500 transition-colors hover:bg-surface-300 hover:text-slate-200" title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
          <CollapseIcon className="h-4 w-4" />
        </button>
        {!collapsed && (
          <>
            <Logo size={26} className="flex-shrink-0" />
            <div>
              <div className="text-[15px] font-bold tracking-tight text-slate-100">Asset<span className="text-accent">It</span></div>
              <div className="text-[9px] font-medium uppercase tracking-wider text-slate-600">Offline Asset Manager</div>
            </div>
          </>
        )}
        {collapsed && <Logo size={26} className="mx-auto" />}
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <nav className="px-2 py-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeNav === item.id;
            return (
              <button key={item.id} onClick={() => onNavChange(item.id)}
                className={`group relative flex w-full items-center gap-3 px-3 py-1.5 text-[13px] font-medium transition-colors ${isActive ? 'bg-surface-300 text-slate-100' : 'text-slate-400 hover:bg-surface-200 hover:text-slate-200'} ${collapsed ? 'justify-center' : ''}`}
                title={collapsed ? item.label : undefined}>
                {isActive && <span className="absolute left-0 top-0 h-full w-[2px] bg-accent" />}
                <Icon className={`h-3.5 w-3.5 flex-shrink-0 ${isActive ? 'text-accent' : 'text-slate-500 group-hover:text-slate-400'}`} />
                {!collapsed && <span className="flex-1 text-left">{item.label}</span>}
                {!collapsed && <span className={`text-[11px] font-medium tabular-nums ${isActive ? 'text-accent' : 'text-slate-600'}`}>{navCounts[item.id]}</span>}
              </button>
            );
          })}
        </nav>

        {!collapsed && (
          <div className="mt-px">
            <SectionHeader title="Filters" collapsed={collapsed} onClear={hasActiveFilters ? onClearFilters : undefined} />

            {/* Categories — fully dynamic with icon picker */}
            <Section title="Categories" icon={Layers} collapsed={collapsed}>
              <div className="flex flex-wrap gap-1">
                {categories.map((cat) => {
                  const Icon = iconRegistry[cat.iconName] ?? Layers;
                  const isActive = selectedCategories.has(cat.name);
                  return (
                    <div key={cat.name} className="group/cat relative">
                      <button onClick={() => onToggleCategory(cat.name)}
                        className={`flex items-center gap-1.5 border px-2 py-1 text-[11px] font-medium transition-colors ${isActive ? 'border-accent/60 bg-accent/10 text-accent' : 'border-surface-400 text-slate-400 hover:border-surface-500 hover:text-slate-200'}`}>
                        <Icon className="h-2.5 w-2.5" /> {cat.name}
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); onRemoveCategory(cat.name); }}
                        className="absolute -right-1 -top-1 flex h-3 w-3 items-center justify-center bg-surface-400 text-slate-200 opacity-0 hover:bg-rose-500 transition-all group-hover/cat:opacity-100">
                        <X className="h-2 w-2" />
                      </button>
                    </div>
                  );
                })}
                {categories.length === 0 && !addingCategory && (
                  <span className="text-[10px] text-slate-600">No categories. Add one below.</span>
                )}
              </div>

              {addingCategory ? (
                <div className="mt-2 space-y-1.5">
                  <div className="flex items-center gap-1">
                    <input type="text" value={newCatName} onChange={(e) => setNewCatName(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') handleAddCategory(); if (e.key === 'Escape') { setAddingCategory(false); setNewCatName(''); } }}
                      autoFocus placeholder="Category name..."
                      className="flex-1 border border-surface-400 bg-surface-200 px-2 py-1 text-[12px] text-slate-200 placeholder:text-slate-600 focus:border-accent focus:outline-none" />
                    <button onClick={handleAddCategory} disabled={!newCatName.trim()}
                      className="flex h-6 w-6 items-center justify-center bg-accent text-surface-50 hover:bg-accent-600 disabled:opacity-40">
                      <Plus className="h-3 w-3" />
                    </button>
                  </div>
                  {/* Icon picker — horizontal scrollable */}
                  <div className="flex gap-1 overflow-x-auto scrollbar-thin pb-0.5">
                    {iconPickerOptions.map((iconName) => {
                      const Icon = iconRegistry[iconName] ?? Layers;
                      const isSelected = newCatIcon === iconName;
                      return (
                        <button key={iconName} onClick={() => setNewCatIcon(iconName)}
                          className={`flex h-7 w-7 flex-shrink-0 items-center justify-center border transition-colors ${isSelected ? 'border-accent/60 bg-accent/10 text-accent' : 'border-surface-400 text-slate-500 hover:border-surface-500 hover:text-slate-300'}`}
                          title={iconName}>
                          <Icon className="h-3.5 w-3.5" />
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <button onClick={() => setAddingCategory(true)} className="mt-2 flex w-full items-center gap-1.5 border border-dashed border-surface-400 px-2 py-1 text-[11px] font-medium text-slate-500 transition-colors hover:border-accent/50 hover:text-accent">
                  <Plus className="h-3 w-3" /> Add Category
                </button>
              )}
            </Section>

            {/* Tags — fully dynamic, all deletable */}
            <Section title="Tags" icon={Tag} collapsed={collapsed}>
              <div className="flex flex-wrap gap-1">
                {tags.map((tag) => {
                  const isActive = selectedTags.has(tag);
                  return (
                    <div key={tag} className="group/tag relative">
                      <button onClick={() => onToggleTag(tag)}
                        className={`flex items-center gap-1 border px-2 py-0.5 text-[11px] font-medium transition-colors ${isActive ? 'border-accent/60 bg-accent/10 text-accent' : 'border-surface-400 text-slate-400 hover:border-surface-500 hover:text-slate-200'}`}>
                        <span className={`h-1 w-1 rounded-full ${isActive ? 'bg-accent' : 'bg-slate-600'}`} /> {tag}
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); onRemoveTag(tag); }}
                        className="absolute -right-1 -top-1 flex h-3 w-3 items-center justify-center bg-surface-400 text-slate-200 opacity-0 hover:bg-rose-500 transition-all group-hover/tag:opacity-100">
                        <X className="h-2 w-2" />
                      </button>
                    </div>
                  );
                })}
                {tags.length === 0 && !addingTag && (
                  <span className="text-[10px] text-slate-600">No tags. Add one below.</span>
                )}
              </div>
              {addingTag ? (
                <div className="mt-2 flex items-center gap-1">
                  <input type="text" value={newTag} onChange={(e) => setNewTag(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleAddTag(); if (e.key === 'Escape') { setAddingTag(false); setNewTag(''); } }}
                    autoFocus placeholder="Tag name..." className="flex-1 border border-surface-400 bg-surface-200 px-2 py-1 text-[12px] text-slate-200 placeholder:text-slate-600 focus:border-accent focus:outline-none" />
                  <button onClick={handleAddTag} disabled={!newTag.trim()} className="flex h-6 w-6 items-center justify-center bg-accent text-surface-50 hover:bg-accent-600 disabled:opacity-40">
                    <Plus className="h-3 w-3" />
                  </button>
                </div>
              ) : (
                <button onClick={() => setAddingTag(true)} className="mt-2 flex w-full items-center gap-1.5 border border-dashed border-surface-400 px-2 py-1 text-[11px] font-medium text-slate-500 transition-colors hover:border-accent/50 hover:text-accent">
                  <Plus className="h-3 w-3" /> Add Custom Tag
                </button>
              )}
            </Section>
          </div>
        )}
      </div>

      {/* Settings gear at bottom — always visible */}
      <div className="border-t border-surface-300 px-2 py-2">
        <button onClick={onOpenSettings}
          className={`flex w-full items-center gap-3 px-3 py-1.5 text-[13px] font-medium text-slate-400 transition-colors hover:bg-surface-200 hover:text-slate-200 ${collapsed ? 'justify-center' : ''}`}
          title="Settings">
          <Settings className="h-3.5 w-3.5 flex-shrink-0" />
          {!collapsed && <span>Settings</span>}
        </button>
      </div>
    </aside>
  );
}
