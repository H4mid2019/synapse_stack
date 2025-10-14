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
