import { useState, useRef } from 'react';
import type { FileSystemItem } from '../types';
import { filesystemApi } from '../services/api';
import { toast } from 'react-toastify';
import { itemsActions } from '../store/itemsStore';

interface FileExplorerProps {
  items: FileSystemItem[];
  currentFolderId: number | null;
  breadcrumb: FileSystemItem[];
  onDelete: (id: number) => void;
  onNavigate: (folderId: number | null) => void;
  isLoading?: boolean;
}

export const FileExplorer = ({ 
  items, 
  currentFolderId,
  breadcrumb,
  onDelete, 
  onNavigate,
  isLoading = false 
}: FileExplorerProps) => {
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [renamingItemId, setRenamingItemId] = useState<number | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;
    
    try {
      const newFolder = await filesystemApi.create({
        name: newFolderName.trim(),
        type: 'folder',
        parent_id: currentFolderId
      });
      
      itemsActions.addItem(newFolder);
      setNewFolderName('');
      setIsCreatingFolder(false);
      toast.success(`Folder "${newFolder.name}" created successfully!`);
    } catch (err: unknown) {
      const errorMessage = (err as { response?: { data?: { error?: string } } })?.response?.data?.error || 'Failed to create folder';
      toast.error(errorMessage);
      console.error('Failed to create folder:', err);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    setIsUploading(true);
    let successCount = 0;
    
    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const formData = new FormData();
        formData.append('file', file);
        if (currentFolderId !== null) {
          formData.append('parent_id', currentFolderId.toString());
        }
        
        try {
          const uploadedFile = await filesystemApi.uploadFile(formData);
          itemsActions.addItem(uploadedFile);
          successCount++;
        } catch (err: unknown) {
          const errorMessage = (err as { response?: { data?: { error?: string } } })?.response?.data?.error || 'Failed to upload file';
          toast.error(`${file.name}: ${errorMessage}`);
          console.error(`Failed to upload ${file.name}:`, err);
        }
      }
      
      // Show success message
      if (successCount > 0) {
        toast.success(`Successfully uploaded ${successCount} file${successCount > 1 ? 's' : ''}!`);
      }
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownload = async (item: FileSystemItem) => {
    if (item.type !== 'file') return;
    
    try {
      const blob = await filesystemApi.downloadFile(item.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = item.name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success(`Downloaded "${item.name}"`);
    } catch (err: unknown) {
      const errorMessage = (err as { response?: { data?: { error?: string } } })?.response?.data?.error || 'Failed to download file';
      toast.error(errorMessage);
      console.error('Failed to download file:', err);
    }
  };

  const startRename = (item: FileSystemItem) => {
    setRenamingItemId(item.id);
    setRenameValue(item.name);
  };

  const handleRename = async (itemId: number) => {
    if (!renameValue.trim()) {
      setRenamingItemId(null);
      return;
    }

    try {
      const updatedItem = await filesystemApi.update(itemId, { name: renameValue.trim() });
      itemsActions.updateItem(updatedItem);
      setRenamingItemId(null);
      setRenameValue('');
      toast.success(`Renamed to "${updatedItem.name}"`);
    } catch (err: unknown) {
      const errorMessage = (err as { response?: { data?: { error?: string } } })?.response?.data?.error || 'Failed to rename item';
      toast.error(errorMessage);
      console.error('Failed to rename item:', err);
    }
  };

  const cancelRename = () => {
    setRenamingItemId(null);
    setRenameValue('');
  };

  const formatFileSize = (bytes: number | null) => {
    if (bytes === null) return '';
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  // Filter items by current folder
  const folderItems = items.filter(item => item.type === 'folder');
  const fileItems = items.filter(item => item.type === 'file');

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-5">
        <h1 className="text-2xl font-bold text-gray-900">File Explorer</h1>
        <p className="mt-1 text-sm text-gray-500">Manage your files and folders</p>
      </div>
      
      <nav className="flex items-center space-x-2 text-sm text-gray-600">
        <button 
          onClick={() => onNavigate(null)}
          className="text-sky-600 hover:text-sky-800 font-medium"
        >
          Home
        </button>
        {breadcrumb.map((folder) => (
          <div key={folder.id} className="flex items-center space-x-2">
            <span>/</span>
            <button
              onClick={() => onNavigate(folder.id)}
              className="text-sky-600 hover:text-sky-800 font-medium"
            >
              {folder.name}
            </button>
          </div>
        ))}
      </nav>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setIsCreatingFolder(true)}
          className="px-4 py-2 bg-sky-500 hover:bg-sky-700 text-white rounded-md flex items-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
            <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
          </svg>
          New Folder
        </button>
        
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="px-4 py-2 bg-sky-500 hover:bg-sky-700 text-white rounded-md flex items-center disabled:opacity-50"
        >
          {isUploading ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Uploading...
            </>
          ) : (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
              Upload Files
            </>
          )}
        </button>
        
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          multiple
          className="hidden"
        />
      </div>

      {isCreatingFolder && (
        <div className="bg-white rounded-lg shadow-md p-4 mb-4">
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder="Folder name"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleCreateFolder();
                if (e.key === 'Escape') {
                  setIsCreatingFolder(false);
                  setNewFolderName('');
                }
              }}
              autoFocus
            />
            <button
              onClick={handleCreateFolder}
              className="px-3 py-2 bg-sky-500 hover:bg-sky-700 text-white rounded-md"
            >
              Create
            </button>
            <button
              onClick={() => {
                setIsCreatingFolder(false);
                setNewFolderName('');
              }}
              className="px-3 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {folderItems.map((item) => (
          <div key={item.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
            <div className="p-4">
              <div className="flex items-center mb-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-yellow-500" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                </svg>
              </div>
              
              {renamingItemId === item.id ? (
                <div className="mb-2">
                  <input
                    type="text"
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleRename(item.id);
                      if (e.key === 'Escape') cancelRename();
                    }}
                    autoFocus
                  />
                </div>
              ) : (
                <h3 className="font-medium text-gray-900 truncate">{item.name}</h3>
              )}
              
              <div className="text-xs text-gray-500 mt-1">
                Folder
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Created: {formatDate(item.created_at)}
              </div>
              
              {renamingItemId === item.id ? (
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => handleRename(item.id)}
                    className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded hover:bg-green-200"
                  >
                    Save
                  </button>
                  <button
                    onClick={cancelRename}
                    className="text-xs px-2 py-1 bg-gray-100 text-gray-800 rounded hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => onNavigate(item.id)}
                    className="text-xs px-2 py-1 bg-sky-100 text-sky-800 rounded hover:bg-sky-200"
                  >
                    Open
                  </button>
                  <button
                    onClick={() => startRename(item)}
                    className="text-xs px-2 py-1 bg-amber-100 text-amber-800 rounded hover:bg-amber-200"
                  >
                    Rename
                  </button>
                  <button
                    onClick={() => onDelete(item.id)}
                    className="text-xs px-2 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {fileItems.map((item) => (
          <div key={item.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
            <div className="p-4">
              <div className="flex items-center mb-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                </svg>
              </div>
              
              {renamingItemId === item.id ? (
                <div className="mb-2">
                  <input
                    type="text"
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleRename(item.id);
                      if (e.key === 'Escape') cancelRename();
                    }}
                    autoFocus
                  />
                </div>
              ) : (
                <h3 className="font-medium text-gray-900 truncate">{item.name}</h3>
              )}
              
              <div className="text-xs text-gray-500 mt-1">
                {item.mime_type}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {formatFileSize(item.size)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Created: {formatDate(item.created_at)}
              </div>
              
              {renamingItemId === item.id ? (
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => handleRename(item.id)}
                    className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded hover:bg-green-200"
                  >
                    Save
                  </button>
                  <button
                    onClick={cancelRename}
                    className="text-xs px-2 py-1 bg-gray-100 text-gray-800 rounded hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => handleDownload(item)}
                    className="text-xs px-2 py-1 bg-sky-100 text-sky-800 rounded hover:bg-sky-200"
                  >
                    Download
                  </button>
                  <button
                    onClick={() => startRename(item)}
                    className="text-xs px-2 py-1 bg-amber-100 text-amber-800 rounded hover:bg-amber-200"
                  >
                    Rename
                  </button>
                  <button
                    onClick={() => onDelete(item.id)}
                    className="text-xs px-2 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {items.length === 0 && !isCreatingFolder && (
        <div className="text-center py-12">
          <svg xmlns="http://www.w3.org/2000/svg" className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No items</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by uploading a file or creating a folder.</p>
        </div>
      )}
    </div>
  );
};
