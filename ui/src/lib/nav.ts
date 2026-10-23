import {
  Boxes, Layers, Package, Palette, Star, History,
  Rocket, Ghost, Castle, Building2, Factory, Blocks,
  Shield, Hexagon, Cylinder, Sparkles, Cog, Box,
  type LucideIcon,
} from 'lucide-react';
import type { NavSection } from '@/types';
import type { CategoryDef } from '@/types';

export const navItems: { id: NavSection; label: string; icon: LucideIcon }[] = [
  { id: 'all', label: 'All Assets', icon: Boxes },
  { id: 'kits', label: 'Kits / Collections', icon: Layers },
  { id: 'models', label: 'Models', icon: Package },
  { id: 'materials', label: 'Materials', icon: Palette },
  { id: 'favorites', label: 'Favorites', icon: Star },
  { id: 'imported', label: 'Imported History', icon: History },
];

/** Full icon registry — maps string names to Lucide components */
export const iconRegistry: Record<string, LucideIcon> = {
  Rocket, Ghost, Castle, Building2, Factory, Blocks,
  Shield, Hexagon, Cylinder, Layers, Sparkles, Cog, Box,
};

/** Icons available in the category icon picker */
export const iconPickerOptions: string[] = [
  'Rocket', 'Building2', 'Shield', 'Hexagon', 'Cylinder', 'Layers',
  'Sparkles', 'Cog', 'Box', 'Ghost', 'Castle', 'Factory', 'Blocks',
];

/** Default category definitions (name + iconName) */
export const defaultCategories: CategoryDef[] = [
  { name: 'Sci-Fi', iconName: 'Rocket' },
  { name: 'Cyberpunk', iconName: 'Ghost' },
  { name: 'Fantasy', iconName: 'Castle' },
  { name: 'Industrial', iconName: 'Factory' },
  { name: 'Modular', iconName: 'Blocks' },
  { name: 'Modern', iconName: 'Building2' },
];

export const defaultTags: string[] = [
  'modular', 'PBR', 'rigged', 'animated', 'destructible',
  'interior', 'exterior', 'hero prop', 'environment',
  'vehicle', 'character', 'weapon',
  'low-poly', 'mid-poly', 'high-poly',
];
