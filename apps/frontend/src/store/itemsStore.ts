import { signal, computed } from '@preact/signals-react';
import type { FileSystemItem } from '../types';

// Signals - each is independently reactive
export const items = signal<FileSystemItem[]>([]);
export const currentFolderId = signal<number | null>(null);
export const breadcrumb = signal<FileSystemItem[]>([]);
export const loading = signal<boolean>(false);
export const error = signal<string | null>(null);

// Computed values (optional - derived state)
export const currentFolderItems = computed(() => {
  return items.value.filter(item => item.parent_id === currentFolderId.value);
});

export const hasItems = computed(() => items.value.length > 0);

// Actions - clean, simple functions to update signals
export const itemsActions = {
  setLoading: (value: boolean) => {
    loading.value = value;
  },

  setError: (errorMessage: string | null) => {
    error.value = errorMessage;
    loading.value = false;
  },

  setItems: (newItems: FileSystemItem[]) => {
    items.value = newItems;
    loading.value = false;
    error.value = null;
  },

  addItem: (item: FileSystemItem) => {
    items.value = [...items.value, item];
  },

  updateItem: (updatedItem: FileSystemItem) => {
    items.value = items.value.map(item =>
      item.id === updatedItem.id ? updatedItem : item
    );
  },

  deleteItem: (itemId: number) => {
    items.value = items.value.filter(item => item.id !== itemId);
  },

  setCurrentFolder: (folderId: number | null) => {
    currentFolderId.value = folderId;
  },

  setBreadcrumb: (newBreadcrumb: FileSystemItem[]) => {
    breadcrumb.value = newBreadcrumb;
  },

  // Bonus: Reset everything
  reset: () => {
    items.value = [];
    currentFolderId.value = null;
    breadcrumb.value = [];
    loading.value = false;
    error.value = null;
  },
};
