import { useState, useCallback, useRef, useEffect } from 'react';
import { filesystemApi } from '../services/api';
import type { FileSystemItem, SearchResult, SearchParams } from '../types';
import { toast } from 'react-toastify';

interface SearchBarProps {
  currentFolderId: number | null;
  onSearchResults?: (results: FileSystemItem[]) => void;
  onClearSearch?: () => void;
}

export const SearchBar = ({
  currentFolderId,
  onSearchResults,
  onClearSearch,
}: SearchBarProps) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<FileSystemItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [searchType, setSearchType] = useState<'all' | 'file' | 'folder'>(
    'all'
  );
  const [currentPage, setCurrentPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const searchTimeoutRef = useRef<number | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const onSearchResultsRef = useRef(onSearchResults);
  const onClearSearchRef = useRef(onClearSearch);

  // Update refs when props change
  useEffect(() => {
    onSearchResultsRef.current = onSearchResults;
    onClearSearchRef.current = onClearSearch;
  }, [onSearchResults, onClearSearch]);

  const performSearch = useCallback(
    async (query: string, page = 1) => {
      if (!query.trim()) {
        setSearchResults([]);
        setShowResults(false);
        setTotalResults(0);
        onClearSearchRef.current?.();
        return;
      }

      setIsSearching(true);
      try {
        const searchParams: SearchParams = {
          q: query.trim(),
          page,
          limit: 10,
        };

        // Add type filter if not 'all'
        if (searchType !== 'all') {
          searchParams.type = searchType;
        }

        // Add folder scope if searching within a folder
        if (currentFolderId !== null) {
          searchParams.parent_id = currentFolderId;
        }

        const result: SearchResult = await filesystemApi.search(searchParams);

        setSearchResults(result.results);
        setTotalResults(result.pagination.total_items);
        setCurrentPage(result.pagination.current_page);
        setShowResults(true);

        // Notify parent component about search results
        onSearchResultsRef.current?.(result.results);
      } catch (error) {
        console.error('Search failed:', error);
        toast.error('Search failed. Please try again.');
        setSearchResults([]);
        setShowResults(false);
      } finally {
        setIsSearching(false);
      }
    },
    [searchType, currentFolderId]
  );

  // Debounced search
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = window.setTimeout(() => {
      performSearch(searchQuery);
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery, performSearch]);

  // Handle clicks outside search results
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        resultsRef.current &&
        !resultsRef.current.contains(event.target as Node)
      ) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleClearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setShowResults(false);
    setTotalResults(0);
    setCurrentPage(1);
    onClearSearchRef.current?.();
  };

  const handleLoadMore = () => {
    if (currentPage * 10 < totalResults) {
      performSearch(searchQuery, currentPage + 1);
    }
  };

  const formatFileSize = (bytes: number | null) => {
    if (bytes === null) return '';
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getItemIcon = (item: FileSystemItem) => {
    if (item.type === 'folder') {
      return (
        <svg
          className="h-5 w-5 text-yellow-500"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
        </svg>
      );
    } else {
      return (
        <svg
          className="h-5 w-5 text-blue-500"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z"
            clipRule="evenodd"
          />
        </svg>
      );
    }
  };

  return (
    <div className="relative" ref={resultsRef}>
      <div className="flex items-center space-x-2 mb-4">
        {/* Search Input */}
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg
              className="h-5 w-5 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={
              currentFolderId
                ? 'Search in this folder...'
                : 'Search all files and folders...'
            }
            className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
          />
          {searchQuery && (
            <button
              onClick={handleClearSearch}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              <svg
                className="h-5 w-5 text-gray-400 hover:text-gray-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>

        {/* Type Filter */}
        <select
          value={searchType}
          onChange={(e) =>
            setSearchType(e.target.value as 'all' | 'file' | 'folder')
          }
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="all">All Types</option>
          <option value="file">Files Only</option>
          <option value="folder">Folders Only</option>
        </select>
      </div>

      {/* Search Results Dropdown */}
      {showResults && searchResults.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-10 max-h-96 overflow-y-auto">
          <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
            <p className="text-sm text-gray-600">
              {totalResults} result{totalResults !== 1 ? 's' : ''} found
              {currentFolderId && ' in this folder'}
            </p>
          </div>

          {searchResults.map((item) => (
            <div
              key={item.id}
              className="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
            >
              <div className="flex items-center space-x-3">
                {getItemIcon(item)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {item.name}
                  </p>
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    <span className="capitalize">{item.type}</span>
                    {item.size && (
                      <>
                        <span>•</span>
                        <span>{formatFileSize(item.size)}</span>
                      </>
                    )}
                    <span>•</span>
                    <span>
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* Load More Button */}
          {currentPage * 10 < totalResults && (
            <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
              <button
                onClick={handleLoadMore}
                disabled={isSearching}
                className="w-full px-3 py-2 text-sm text-indigo-600 hover:text-indigo-800 disabled:opacity-50"
              >
                {isSearching
                  ? 'Loading...'
                  : `Load more (${totalResults - currentPage * 10} remaining)`}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Loading Indicator */}
      {isSearching && searchQuery && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-10 px-4 py-8">
          <div className="flex justify-center items-center">
            <svg
              className="animate-spin h-6 w-6 text-indigo-600"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <span className="ml-2 text-gray-600">Searching...</span>
          </div>
        </div>
      )}

      {/* No Results */}
      {showResults &&
        searchResults.length === 0 &&
        !isSearching &&
        searchQuery && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-10 px-4 py-8">
            <div className="text-center text-gray-500">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0118 12a8 8 0 01-8 8 8 8 0 01-8-8 8 8 0 018-8c2.3 0 4.377.901 5.936 2.364l2.828-2.828A8 8 0 0012 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10a9.956 9.956 0 00-2.864-7.064l-2.828 2.828z"
                />
              </svg>
              <p className="mt-2 text-sm">
                No results found for "{searchQuery}"
              </p>
              <p className="text-xs text-gray-400">
                Try a different search term or check your spelling
              </p>
            </div>
          </div>
        )}
    </div>
  );
};
