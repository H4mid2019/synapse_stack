import axios from 'axios';
import type {
  FileSystemItem,
  CreateFileSystemItemData,
  UpdateFileSystemItemData,
  SearchParams,
  SearchResult,
} from '../types';

const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

let getAccessToken: (() => Promise<string>) | null = null;

export const setAuthToken = (getTokenFn: () => Promise<string>) => {
  getAccessToken = getTokenFn;
};

api.interceptors.request.use(
  async (config) => {
    if (getAccessToken) {
      const token = await getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const filesystemApi = {
  getAll: async (
    parent_id: number | null = null
  ): Promise<{ items: FileSystemItem[]; breadcrumb: FileSystemItem[] }> => {
    const response = await api.get<{
      items: FileSystemItem[];
      breadcrumb: FileSystemItem[];
    }>('/filesystem', {
      params: { parent_id },
    });
    return response.data;
  },

  getById: async (id: number): Promise<FileSystemItem> => {
    const response = await api.get<FileSystemItem>(`/filesystem/${id}`);
    return response.data;
  },

  create: async (data: CreateFileSystemItemData): Promise<FileSystemItem> => {
    const response = await api.post<FileSystemItem>('/filesystem', data);
    return response.data;
  },

  update: async (
    id: number,
    data: UpdateFileSystemItemData
  ): Promise<FileSystemItem> => {
    const response = await api.put<FileSystemItem>(`/filesystem/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/filesystem/${id}`);
  },

  uploadFile: async (data: FormData): Promise<FileSystemItem> => {
    const response = await api.post<FileSystemItem>(
      '/filesystem/upload',
      data,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  downloadFile: async (id: number): Promise<Blob> => {
    const response = await api.get(`/filesystem/${id}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  search: async (params: SearchParams): Promise<SearchResult> => {
    const searchParams = new URLSearchParams();
    searchParams.append('q', params.q);

    if (params.type) {
      searchParams.append('type', params.type);
    }

    if (params.parent_id !== undefined) {
      searchParams.append('parent_id', params.parent_id.toString());
    }

    if (params.page !== undefined) {
      searchParams.append('page', params.page.toString());
    }

    if (params.limit !== undefined) {
      searchParams.append('limit', params.limit.toString());
    }

    const response = await api.get<SearchResult>(
      `/filesystem/search?${searchParams.toString()}`
    );
    return response.data;
  },

  healthCheck: async (): Promise<{ status: string }> => {
    const response = await api.get<{ status: string }>('/health');
    return response.data;
  },
};

export default api;
