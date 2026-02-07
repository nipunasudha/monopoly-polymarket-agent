'use client';

import { useState } from 'react';
import { newsAPI } from '@/lib/api';
import type { NewsArticle } from '@/lib/types';
import { toast } from 'sonner';

export default function NewsPage() {
  const [keywords, setKeywords] = useState('');
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [isDryRun, setIsDryRun] = useState(false);

  const handleSearch = async () => {
    if (!keywords.trim()) {
      toast.error('Please enter keywords to search');
      return;
    }

    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await newsAPI.search(keywords.trim());
      setArticles(response.articles);
      setIsDryRun(response.dry_run || false);
      
      if (response.articles.length === 0) {
        toast.info('No articles found', {
          description: 'Try different keywords',
        });
      } else {
        toast.success(`Found ${response.articles.length} articles`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to search news';
      setError(errorMessage);
      toast.error('Failed to search news', {
        description: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown date';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold text-gray-900">News Search</h1>
          {isDryRun && (
            <span className="px-2 py-1 text-xs font-medium text-yellow-800 bg-yellow-100 rounded-md">
              Mock Data
            </span>
          )}
        </div>
        <p className="mt-2 text-sm text-gray-600">
          Search for relevant news articles using NewsAPI
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex gap-3">
          <input
            type="text"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter keywords (comma-separated, e.g., bitcoin, crypto, market)"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            onClick={handleSearch}
            disabled={loading || !keywords.trim()}
            className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Searching...
              </>
            ) : (
              'Search'
            )}
          </button>
        </div>
        <p className="mt-2 text-xs text-gray-500">
          Tip: Use comma-separated keywords for multiple search terms (e.g., "bitcoin, crypto, market")
        </p>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">Error: {error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      )}

      {/* Results */}
      {!loading && hasSearched && articles.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              Results ({articles.length})
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {articles.map((article, index) => (
              <div
                key={index}
                className="bg-white shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {article.source?.name && (
                          <span className="text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
                            {article.source.name}
                          </span>
                        )}
                        {article.publishedAt && (
                          <span className="text-xs text-gray-500">
                            {formatDate(article.publishedAt)}
                          </span>
                        )}
                      </div>
                      
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {article.title || 'No title'}
                      </h3>
                      
                      {article.description && (
                        <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                          {article.description}
                        </p>
                      )}
                      
                      {article.author && (
                        <p className="text-xs text-gray-500 mb-3">
                          By {article.author}
                        </p>
                      )}
                      
                      {article.url && (
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center text-sm text-indigo-600 hover:text-indigo-700"
                        >
                          Read full article
                          <svg className="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </a>
                      )}
                    </div>
                    
                    {article.urlToImage && (
                      <div className="ml-4 flex-shrink-0">
                        <img
                          src={article.urlToImage}
                          alt={article.title || 'Article image'}
                          className="w-32 h-32 object-cover rounded-lg"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && hasSearched && articles.length === 0 && (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No articles found</h3>
          <p className="mt-2 text-sm text-gray-500">
            Try different keywords or check your NewsAPI configuration.
          </p>
        </div>
      )}

      {/* Initial State */}
      {!hasSearched && !loading && (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">Search for news articles</h3>
          <p className="mt-2 text-sm text-gray-500">
            Enter keywords above to search for relevant news articles using NewsAPI.
          </p>
        </div>
      )}
    </div>
  );
}
