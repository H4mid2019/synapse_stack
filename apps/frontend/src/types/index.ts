export interface FileSystemItem {
  id: number;
  name: string;
  type: 'folder' | 'file';
  parent_id: number | null;
  size: number | null;
  mime_type: string | null;
  created_at: string;
  updated_at: string;
  path: string;
}

export interface CreateFileSystemItemData {
  name: string;
  type: 'folder' | 'file';
  parent_id?: number | null;
  size?: number;
  mime_type?: string;
}

export interface UpdateFileSystemItemData {
  name?: string;
  parent_id?: number | null;
}

export interface UploadFileData {
  file: File;
  parent_id: number | null;
}

export interface SearchParams {
  q: string;
  type?: 'file' | 'folder';
  parent_id?: number;
  page?: number;
  limit?: number;
}

export interface SearchPagination {
  current_page: number;
  total_pages: number;
  total_items: number;
  items_per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface SearchFilters {
  type?: string;
  parent_id?: number;
}

export interface SearchResult {
  results: FileSystemItem[];
  pagination: SearchPagination;
  query: string;
  filters: SearchFilters;
}
