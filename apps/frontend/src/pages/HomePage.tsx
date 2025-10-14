import { useState, useEffect } from 'react';
import { filesystemApi } from '../services/api';
import { FileExplorer } from '../components/FileExplorer';
import { ConfirmModal } from '../components/ConfirmModal';
import { toast } from 'react-toastify';
import { items, currentFolderId, breadcrumb, loading, error, itemsActions } from '../store/itemsStore';

export const HomePage = () => {
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [localFolderId, setLocalFolderId] = useState(currentFolderId.value);

  // Fetch items whenever localFolderId changes
  useEffect(() => {
    const fetchItems = async () => {
      itemsActions.setLoading(true);
      try {
        const response = await filesystemApi.getAll(localFolderId);
        itemsActions.setItems(response.items);
        itemsActions.setBreadcrumb(response.breadcrumb);
      } catch {
        itemsActions.setError('Failed to fetch items');
      }
    };

    fetchItems();
  }, [localFolderId]);

  const handleDelete = async (id: number) => {
    setItemToDelete(id);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    if (itemToDelete === null || isDeleting) return;

    setIsDeleting(true);
    
    try {
      await filesystemApi.delete(itemToDelete);
      itemsActions.deleteItem(itemToDelete);
      toast.success('Item deleted successfully!');
      setDeleteModalOpen(false);
      setItemToDelete(null);
    } catch (err: unknown) {
      const errorMessage = (err as { response?: { data?: { error?: string } } })?.response?.data?.error || 'Failed to delete item';
      toast.error(errorMessage);
      console.error('Failed to delete item:', err);
    } finally {
      setIsDeleting(false);
    }
  };

  const cancelDelete = () => {
    setDeleteModalOpen(false);
    setItemToDelete(null);
  };

  const handleNavigate = (folderId: number | null) => {
    setLocalFolderId(folderId);
    itemsActions.setCurrentFolder(folderId);
  };

  if (error.value) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-800">{error.value}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <>
      <ConfirmModal
        isOpen={deleteModalOpen}
        title="Delete Item"
        message="Are you sure you want to delete this item? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        type="danger"
        isLoading={isDeleting}
        onConfirm={confirmDelete}
        onCancel={cancelDelete}
      />
      
      <FileExplorer
        items={items.value}
        currentFolderId={currentFolderId.value}
        breadcrumb={breadcrumb.value}
        onDelete={handleDelete}
        onNavigate={handleNavigate}
        isLoading={loading.value}
      />
    </>
  );
};
