import type { Asset, LocalFolder } from './types';

// Production starts empty: all assets and libraries must come from folders the user selects.
export const assets: Asset[] = [];
export const localFolders: LocalFolder[] = [];

export const softwareVersions: Record<string, string[]> = {
  Blender: ['Installed application', 'Choose application…'],
  'Unreal Engine': ['Installed application', 'Choose application…'],
  Unity: ['Installed application', 'Choose application…'],
  '3ds Max': ['Installed application', 'Choose application…'],
  Maya: ['Installed application', 'Choose application…'],
};
