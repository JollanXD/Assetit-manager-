import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import TopBar from '@/components/TopBar';
import AssetGrid from '@/components/AssetGrid';
import Inspector from '@/components/Inspector';
import ToastContainer, { type ToastData } from '@/components/Toast';
import SettingsModal from '@/components/SettingsModal';
import { useResizablePanes } from '@/hooks/useResizablePanes';
import type { Asset, NavSection, Category, CategoryDef, ViewMode, LocalFolder } from '@/types';
import { navItems } from '@/lib/nav';

declare global { interface Window { QWebChannel?: any; qt?: any; assetItBridge?: any } }\n\nconst COLLAPSED_WIDTH = 52;
const EXPANDED_WIDTH = 240;

let toastId = 0;

export default function App() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [folders, setFolders] = useState<LocalFolder[]>([]);\n  const bridge = useRef<any>(null);
  const [activeNav, setActiveNav] = useState<NavSection>('all');
  const [search, setSearch] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [toasts, setToasts] = useState<ToastData[]>([]);
  const [thumbnailSize, setThumbnailSize] = useState(40);
  const [uiScale, setUiScale] = useState(100);
  const [language, setLanguage] = useState<'English' | 'Russian'>('English');

  const [categories, setCategories] = useState<CategoryDef[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<Set<Category>>(new Set());
  const [tags, setTags] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());

  const { leftWidth, rightWidth, activeHandle, startLeftResize, startRightResize, setRightWidth } = useResizablePanes(EXPANDED_WIDTH, 360);
  const toastRef = useRef(toastId);

  const currentLeftWidth = sidebarCollapsed ? COLLAPSED_WIDTH : leftWidth;
  const refreshLocalData = useCallback(() => {
    const api = bridge.current;
    if (!api) return;
    try {
      api.getLibraries((json: string) => setFolders(JSON.parse(json || '[]')));
      api.getAssets((json: string) => setAssets(JSON.parse(json || '[]')));
    } catch (e) { console.error('AssetIt local bridge error', e); }
  }, []);

  useEffect(() => {
    if (!window.QWebChannel || !window.qt?.webChannelTransport) return;
    new window.QWebChannel(window.qt.webChannelTransport, (channel: any) => {
      bridge.current = channel.objects.assetItBridge;
      refreshLocalData();
    });
  }, [refreshLocalData]);


  const addToast = useCallback((message: string, subtitle: string) => {
    const id = ++toastRef.current;
    setToasts((prev) => [...prev, { id, message, subtitle }]);
  }, []);

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toggleSet = <T,>(set: Set<T>, value: T): Set<T> => {
    const next = new Set(set);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    return next;
  };

  const handleToggleCategory = (cat: Category) => setSelectedCategories((prev) => toggleSet(prev, cat));
  const handleToggleTag = (tag: string) => setSelectedTags((prev) => toggleSet(prev, tag));

  const handleAddCategory = useCallback((name: string, iconName: string) => {
    setCategories((prev) => [...prev, { name, iconName }]);
  }, []);

  const handleRemoveCategory = useCallback((cat: Category) => {
    setCategories((prev) => prev.filter((c) => c.name !== cat));
    setSelectedCategories((prev) => { const next = new Set(prev); next.delete(cat); return next; });
  }, []);

  const handleAddTag = useCallback((tag: string) => {
    setTags((prev) => [...prev, tag]);
  }, []);

  const handleRemoveTag = useCallback((tag: string) => {
    setTags((prev) => prev.filter((t) => t !== tag));
    setSelectedTags((prev) => { const next = new Set(prev); next.delete(tag); return next; });
    // Also remove from all assets
    setAssets((prev) => prev.map((a) => ({ ...a, tags: a.tags.filter((t) => t !== tag) })));
    setSelectedAsset((prev) => prev ? { ...prev, tags: prev.tags.filter((t) => t !== tag) } : prev);
  }, []);

  const handleClearFilters = () => {
    setSelectedCategories(new Set());
    setSelectedTags(new Set());
  };

  const handleToggleFavorite = useCallback((asset: Asset) => {
    bridge.current?.toggleFavorite(asset.filePath);
    setAssets((prev) => prev.map((a) => (a.id === asset.id ? { ...a, favorite: !a.favorite } : a)));
    setSelectedAsset((prev) => (prev && prev.id === asset.id ? { ...prev, favorite: !prev.favorite } : prev));
  }, []);

  const handleAddTagToAsset = useCallback((asset: Asset, tag: string) => {
    setAssets((prev) => prev.map((a) => (a.id === asset.id && !a.tags.includes(tag) ? { ...a, tags: [...a.tags, tag] } : a)));
    setSelectedAsset((prev) => (prev && prev.id === asset.id && !prev.tags.includes(tag) ? { ...prev, tags: [...prev.tags, tag] } : prev));
  }, []);

  const handleRemoveTagFromAsset = useCallback((asset: Asset, tag: string) => {
    setAssets((prev) => prev.map((a) => (a.id === asset.id ? { ...a, tags: a.tags.filter((t) => t !== tag) } : a)));
    setSelectedAsset((prev) => (prev && prev.id === asset.id ? { ...prev, tags: prev.tags.filter((t) => t !== tag) } : prev));
  }, []);

  const handleImport = useCallback((asset: Asset, target: string) => {
    if (target === 'clipboard') {
      addToast('Copied to Clipboard', `${asset.name} (${asset.fileFormat}) files ready to paste`);
    } else {
      addToast('Asset successfully transferred', `${asset.name} → ${target} via Local Port`);
      setAssets((prev) => prev.map((a) => (a.id === asset.id ? { ...a, imported: true } : a)));
      setSelectedAsset((prev) => (prev && prev.id === asset.id ? { ...prev, imported: true } : prev));
    }
  }, [addToast]);

  const handleQuickImport = useCallback((asset: Asset) => {
    addToast('Asset successfully transferred', `${asset.name} → Blender 4.2 via Local Port`);
    setAssets((prev) => prev.map((a) => (a.id === asset.id ? { ...a, imported: true } : a)));
  }, [addToast]);

  const handleAddFolder = useCallback((path: string) => {
    const api = bridge.current;
    if (!api) { addToast('Desktop bridge unavailable', 'Restart the packaged AssetIt application.'); return; }
    api.addLibrary(path, (raw: string) => {
      const result = JSON.parse(raw || '{}');
      if (result.error) { addToast('Folder not added', result.error); return; }
      refreshLocalData();
      addToast('Local folder added', result.path);
    });
  }, [addToast, refreshLocalData]);

  const handleRemoveFolder = useCallback((id: string) => {
    bridge.current?.removeLibrary(id, () => refreshLocalData());
  }, [refreshLocalData]);

  const handleRescan = useCallback((_id: string) => {
    refreshLocalData();
    addToast('Library refreshed', 'Asset list updated from disk.');
  }, [addToast, refreshLocalData]);

  const counts = useMemo(() => ({
    all: assets.length,
    kits: assets.filter((a) => a.type === 'Kit').length,
    models: assets.filter((a) => a.type === 'Model').length,
    materials: assets.filter((a) => a.type === 'Material').length,
    favorites: assets.filter((a) => a.favorite).length,
    imported: assets.filter((a) => a.imported).length,
  }), [assets]);

  const filteredAssets = useMemo(() => {
    let result = assets;
    switch (activeNav) {
      case 'kits': result = result.filter((a) => a.type === 'Kit'); break;
      case 'models': result = result.filter((a) => a.type === 'Model'); break;
      case 'materials': result = result.filter((a) => a.type === 'Material'); break;
      case 'favorites': result = result.filter((a) => a.favorite); break;
      case 'imported': result = result.filter((a) => a.imported); break;
    }
    if (selectedCategories.size > 0) result = result.filter((a) => selectedCategories.has(a.category));
    if (selectedTags.size > 0) result = result.filter((a) => a.tags.some((t) => selectedTags.has(t)));
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter((a) => a.name.toLowerCase().includes(q) || a.kitName.toLowerCase().includes(q) || a.category.toLowerCase().includes(q) || a.tags.some((t) => t.toLowerCase().includes(q)));
    }
    return result;
  }, [assets, activeNav, selectedCategories, selectedTags, search]);

  const hasActiveFilters = selectedCategories.size > 0 || selectedTags.size > 0;
  const activeNavLabel = navItems.find((n) => n.id === activeNav)?.label ?? 'All Assets';

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-surface-50" style={{ fontSize: `${uiScale}%` }}>
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          width={currentLeftWidth}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed((prev) => !prev)}
          onOpenSettings={() => setShowSettings(true)}
          activeNav={activeNav}
          onNavChange={(nav) => { setActiveNav(nav); setSelectedAsset(null); }}
          categories={categories}
          selectedCategories={selectedCategories}
          onToggleCategory={handleToggleCategory}
          onAddCategory={handleAddCategory}
          onRemoveCategory={handleRemoveCategory}
          tags={tags}
          selectedTags={selectedTags}
          onToggleTag={handleToggleTag}
          onAddTag={handleAddTag}
          onRemoveTag={handleRemoveTag}
          onClearFilters={handleClearFilters}
          totalAssets={counts.all}
          totalKits={counts.kits}
          totalModels={counts.models}
          totalMaterials={counts.materials}
          totalFavorites={counts.favorites}
          totalImported={counts.imported}
        />

        {!sidebarCollapsed && (
          <div onMouseDown={startLeftResize} className={`resize-handle w-px flex-shrink-0 bg-surface-300 ${activeHandle === 'left' ? 'active' : ''}`} />
        )}

        <main className="flex flex-1 flex-col overflow-hidden">
          <TopBar
            search={search}
            onSearchChange={setSearch}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            resultCount={filteredAssets.length}
            totalCount={assets.length}
            hasActiveFilters={hasActiveFilters}
            activeNavLabel={activeNavLabel}
          />
          <div className="flex-1 overflow-hidden">
            <AssetGrid
              assets={filteredAssets}
              viewMode={viewMode}
              selectedAssetId={selectedAsset?.id ?? null}
              onSelect={setSelectedAsset}
              onQuickImport={handleQuickImport}
              onToggleFavorite={handleToggleFavorite}
              thumbnailSize={thumbnailSize}
              onThumbnailSizeChange={setThumbnailSize}
            />
          </div>
        </main>

        {selectedAsset && rightWidth !== null && (
          <>
            <div onMouseDown={startRightResize} className={`resize-handle w-px flex-shrink-0 bg-surface-300 ${activeHandle === 'right' ? 'active' : ''}`} />
            <Inspector
              width={rightWidth}
              asset={selectedAsset}
              onClose={() => { setSelectedAsset(null); setRightWidth(null); }}
              onImport={handleImport}
              onToggleFavorite={handleToggleFavorite}
              onAddTagToAsset={handleAddTagToAsset}
              onRemoveTagFromAsset={handleRemoveTagFromAsset}
            />
          </>
        )}
      </div>

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      <SettingsModal
        open={showSettings}
        onClose={() => setShowSettings(false)}
        folders={folders}
        onAddFolder={handleAddFolder}
        onRemoveFolder={handleRemoveFolder}
        onRescan={handleRescan}
        uiScale={uiScale}
        onUiScaleChange={setUiScale}
        language={language}
        onLanguageChange={setLanguage}
      />
    </div>
  );
}
