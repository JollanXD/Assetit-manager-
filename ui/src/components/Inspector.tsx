import { useState } from 'react';
import {
  X, Star, Download, Copy, FileBox, Cpu, HardDrive, Ruler, Weight,
  Tag, ChevronDown, Layers, Package, Palette, Plus, FileSearch,
  Boxes, Check, Monitor,
} from 'lucide-react';
import type { Asset, Software } from '@/types';
import { softwareVersions } from '@/data';
import { iconRegistry } from '@/lib/nav';

interface InspectorProps {
  width: number;
  asset: Asset;
  onClose: () => void;
  onImport: (asset: Asset, software: string) => void;
  onToggleFavorite: (asset: Asset) => void;
  onAddTagToAsset: (asset: Asset, tag: string) => void;
  onRemoveTagFromAsset: (asset: Asset, tag: string) => void;
}

const typeIcons = { Kit: Layers, Model: Package, Material: Palette };

// 3D model formats
const modelFormats = ['.fbx', '.obj', '.blend', '.gltf', '.usdc', '.max', '.ma'];
// Texture/image formats
const textureFormats = ['.png', '.jpg', '.exr', '.tga'];
// Project file formats
const projectFormats = ['.uproject'];

function getAssetKind(asset: Asset): 'model' | 'texture' | 'project' {
  if (textureFormats.includes(asset.fileFormat)) return 'texture';
  if (projectFormats.includes(asset.fileFormat)) return 'project';
  // .blend can be either a model or a project; treat Kit type as project
  if (asset.fileFormat === '.blend' && asset.type === 'Kit') return 'project';
  return 'model';
}

function DetailRow({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-surface-300 py-2 last:border-0">
      <div className="flex items-center gap-2 text-slate-500">
        <Icon className="h-3.5 w-3.5" />
        <span className="text-[12px]">{label}</span>
      </div>
      <span className="text-[12px] font-semibold text-slate-200 tabular-nums">{value}</span>
    </div>
  );
}

export default function Inspector({ width, asset, onClose, onImport, onToggleFavorite, onAddTagToAsset, onRemoveTagFromAsset }: InspectorProps) {
  const [selectedVersion, setSelectedVersion] = useState('Blender 4.2');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [tagInput, setTagInput] = useState('');
  const [tagInputOpen, setTagInputOpen] = useState(false);
  const [pathCopied, setPathCopied] = useState(false);
  const CatIcon = iconRegistry[asset.category] ?? Layers;
  const TypeIcon = typeIcons[asset.type];
  const assetKind = getAssetKind(asset);

  const handleImport = () => onImport(asset, selectedVersion);

  const handleCopy = async () => {
    try { await navigator.clipboard.writeText(`${asset.name} (${asset.fileFormat}) — ${selectedVersion} import ready`); } catch { /* ignore */ }
    onImport(asset, 'clipboard');
  };

  const handleCopyPath = async () => {
    try {
      await navigator.clipboard.writeText(asset.filePath);
      setPathCopied(true);
      setTimeout(() => setPathCopied(false), 1500);
    } catch { /* ignore */ }
  };

  const handleAddTag = () => {
    const trimmed = tagInput.trim().toLowerCase();
    if (trimmed && !asset.tags.includes(trimmed)) {
      onAddTagToAsset(asset, trimmed);
      setTagInput('');
      setTagInputOpen(false);
    }
  };

  return (
    <aside className="flex h-full flex-shrink-0 flex-col border-l border-surface-300 bg-surface-100 animate-slide-in-right" style={{ width }}>
      <div className="flex items-center justify-between border-b border-surface-300 px-4 py-2.5">
        <span className="text-[13px] font-bold text-slate-100">Asset Inspector</span>
        <button onClick={onClose} className="flex h-6 w-6 items-center justify-center text-slate-500 transition-colors hover:bg-surface-300 hover:text-slate-200">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {/* Preview */}
        <div className="relative aspect-[4/3] overflow-hidden bg-surface-200">
          <img src={asset.preview} alt={asset.name} className="h-full w-full object-cover" />
          <button onClick={() => onToggleFavorite(asset)} className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center bg-surface-0/70 backdrop-blur-sm transition-colors hover:bg-surface-0/90">
            <Star className={`h-3.5 w-3.5 ${asset.favorite ? 'fill-amber-400 text-amber-400' : 'text-slate-400'}`} />
          </button>
          <div className="absolute bottom-2 left-2 flex gap-1">
            <span className="flex items-center gap-1 bg-surface-0/80 px-2 py-0.5 text-[10px] font-semibold text-slate-200 backdrop-blur-sm"><CatIcon className="h-2.5 w-2.5" />{asset.category}</span>
            <span className="flex items-center gap-1 bg-surface-0/80 px-2 py-0.5 text-[10px] font-medium text-slate-300 backdrop-blur-sm"><TypeIcon className="h-2.5 w-2.5" />{asset.type}</span>
          </div>
        </div>

        {/* Title — no description */}
        <div className="px-4 pt-3">
          <h2 className="text-[16px] font-bold text-slate-100">{asset.name}</h2>
          <p className="mt-0.5 text-[12px] text-slate-500">{asset.kitName}</p>
        </div>

        {/* File path with copy button */}
        <div className="mx-4 mt-3 border border-surface-300 px-3 py-2">
          <div className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-wider text-slate-600 mb-1">
            <FileSearch className="h-3 w-3" /> File Path
          </div>
          <div className="flex items-center gap-1.5">
            <span className="min-w-0 flex-1 truncate text-[11px] font-mono text-slate-400">{asset.filePath}</span>
            <button onClick={handleCopyPath} className="relative flex h-5 w-5 flex-shrink-0 items-center justify-center text-slate-500 transition-colors hover:text-accent" title="Copy file path">
              {pathCopied ? (
                <Check className="h-3.5 w-3.5 text-emerald-400" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </button>
          </div>
          {pathCopied && (
            <div className="mt-1 text-[9px] font-medium text-emerald-400 animate-fade-in">Copied to clipboard</div>
          )}
        </div>

        {/* Dynamic Technical Details */}
        <div className="mx-4 mt-3 border border-surface-300 px-3 py-1">
          <h3 className="py-2 text-[9px] font-bold uppercase tracking-wider text-slate-600">Technical Details</h3>

          {assetKind === 'model' && (
            <>
              <DetailRow icon={FileBox} label="Format" value={asset.fileFormat} />
              <DetailRow icon={Ruler} label="Vertices" value={asset.vertices >= 0 ? asset.vertices.toLocaleString() : "—"} />
              <DetailRow icon={Boxes} label="Polygons" value={asset.polygons >= 0 ? asset.polygons.toLocaleString() : "—"} />
              <DetailRow icon={Cpu} label="Polycount" value={asset.polycount} />
              <DetailRow icon={Weight} label="File Size" value={`${asset.fileSizeMB.toFixed(1)} MB`} />
            </>
          )}

          {assetKind === 'texture' && (
            <>
              <DetailRow icon={FileBox} label="Format" value={asset.fileFormat} />
              <DetailRow icon={HardDrive} label="Resolution" value={asset.textureRes} />
              <DetailRow icon={Monitor} label="Color Space" value={asset.colorSpace} />
              <DetailRow icon={Weight} label="File Size" value={`${asset.fileSizeMB.toFixed(1)} MB`} />
            </>
          )}

          {assetKind === 'project' && (
            <>
              <DetailRow icon={Monitor} label="Target Software" value={asset.targetSoftwareVersion} />
              <DetailRow icon={Boxes} label="Associated Assets" value={asset.associatedAssetsCount.toString()} />
              <DetailRow icon={Weight} label="File Size" value={`${asset.fileSizeMB.toFixed(1)} MB`} />
            </>
          )}
        </div>

        {/* Interactive Tags */}
        <div className="mx-4 mt-3 border border-surface-300 px-3 py-2">
          <h3 className="mb-1.5 text-[9px] font-bold uppercase tracking-wider text-slate-600">Asset Tags</h3>
          <div className="flex flex-wrap gap-1">
            {asset.tags.map((tag) => (
              <span key={tag} className="group/tag flex items-center gap-1 border border-surface-400 bg-surface-200 px-1.5 py-0.5 text-[10px] font-medium text-slate-400">
                <Tag className="h-2 w-2 text-slate-500" />
                {tag}
                <button onClick={() => onRemoveTagFromAsset(asset, tag)} className="ml-0.5 text-slate-600 transition-colors hover:text-rose-400">
                  <X className="h-2.5 w-2.5" />
                </button>
              </span>
            ))}
            {asset.tags.length === 0 && !tagInputOpen && (
              <span className="text-[10px] text-slate-600">No tags assigned</span>
            )}
          </div>
          {tagInputOpen ? (
            <div className="mt-1.5 flex items-center gap-1">
              <input type="text" value={tagInput} onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleAddTag(); if (e.key === 'Escape') { setTagInputOpen(false); setTagInput(''); } }}
                autoFocus placeholder="Tag name..." className="flex-1 border border-surface-400 bg-surface-200 px-2 py-1 text-[11px] text-slate-200 placeholder:text-slate-600 focus:border-accent focus:outline-none" />
              <button onClick={handleAddTag} disabled={!tagInput.trim()} className="flex h-5 w-5 items-center justify-center bg-accent text-surface-50 hover:bg-accent-600 disabled:opacity-40">
                <Plus className="h-2.5 w-2.5" />
              </button>
            </div>
          ) : (
            <button onClick={() => setTagInputOpen(true)} className="mt-1.5 flex items-center gap-1 text-[10px] font-medium text-slate-500 transition-colors hover:text-accent">
              <Plus className="h-3 w-3" /> Add Tag to Asset
            </button>
          )}
        </div>

        {/* Software selector */}
        <div className="px-4 pt-3 pb-4">
          <label className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-600">Target Software</label>
          <div className="relative">
            <button onClick={() => setDropdownOpen(!dropdownOpen)} className="flex w-full items-center justify-between border border-surface-400 bg-surface-200 px-3 py-2 text-[13px] font-medium text-slate-200 transition-colors hover:border-surface-500">
              <span>{selectedVersion}</span>
              <ChevronDown className={`h-3.5 w-3.5 text-slate-500 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
            </button>
            {dropdownOpen && (
              <div className="absolute z-20 mt-px w-full border border-surface-400 bg-surface-200 shadow-xl shadow-black/40 animate-scale-in">
                {(Object.keys(softwareVersions) as Software[]).map((sw) => (
                  <div key={sw} className="border-b border-surface-300 last:border-0">
                    <div className="px-3 py-1 text-[9px] font-bold uppercase tracking-wider text-slate-600">{sw}</div>
                    {softwareVersions[sw].map((ver) => (
                      <button key={ver} onClick={() => { setSelectedVersion(ver); setDropdownOpen(false); }}
                        className={`flex w-full items-center px-3 py-1.5 text-[12px] transition-colors ${ver === selectedVersion ? 'bg-accent/10 text-accent' : 'text-slate-400 hover:bg-surface-300'}`}>
                        {ver}
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>

          <button onClick={handleImport} className="mt-2.5 flex w-full items-center justify-center gap-2 bg-accent py-2.5 text-[13px] font-bold text-surface-50 transition-colors hover:bg-accent-600 active:scale-[0.98]">
            <Download className="h-4 w-4" /> Import into {selectedVersion}
          </button>
          <button onClick={handleCopy} className="mt-1.5 flex w-full items-center justify-center gap-2 border border-surface-400 py-2 text-[12px] font-medium text-slate-400 transition-colors hover:bg-surface-200 hover:text-slate-200">
            <Copy className="h-3.5 w-3.5" /> Copy Files to Clipboard
          </button>
        </div>
      </div>
    </aside>
  );
}
