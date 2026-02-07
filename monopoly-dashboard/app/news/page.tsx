'use client';

import { useState } from 'react';
import { newsAPI } from '@/lib/api';
import type { NewsArticle } from '@/lib/types';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { RotateCw, ExternalLink, Search } from 'lucide-react';

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
          <h1 className="text-3xl font-bold">News Search</h1>
          {isDryRun && (
            <Badge variant="secondary">Mock Data</Badge>
          )}
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          Search for relevant news articles using NewsAPI
        </p>
      </div>

      {/* Search Form */}
      <Card>
        <CardContent className="p-6">
          <div className="flex gap-3">
            <Input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter keywords (comma-separated, e.g., bitcoin, crypto, market)"
              disabled={loading}
              className="flex-1"
            />
            <Button
              onClick={handleSearch}
              disabled={loading || !keywords.trim()}
            >
              {loading ? (
                <>
                  <RotateCw className="animate-spin mr-2 h-4 w-4" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Search
                </>
              )}
            </Button>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Tip: Use comma-separated keywords for multiple search terms (e.g., "bitcoin, crypto, market")
          </p>
        </CardContent>
      </Card>

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>Error: {error}</AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {loading && (
        <div className="space-y-4">
          <Skeleton className="h-8 w-48" />
          <div className="grid grid-cols-1 gap-6">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-full" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-3/4" />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {!loading && hasSearched && articles.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              Results ({articles.length})
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {articles.map((article, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {article.source?.name && (
                          <Badge variant="secondary">{article.source.name}</Badge>
                        )}
                        {article.publishedAt && (
                          <span className="text-xs text-muted-foreground">
                            {formatDate(article.publishedAt)}
                          </span>
                        )}
                      </div>
                      
                      <h3 className="text-lg font-semibold mb-2">
                        {article.title || 'No title'}
                      </h3>
                      
                      {article.description && (
                        <p className="text-sm text-muted-foreground mb-3 line-clamp-3">
                          {article.description}
                        </p>
                      )}
                      
                      {article.author && (
                        <p className="text-xs text-muted-foreground mb-3">
                          By {article.author}
                        </p>
                      )}
                      
                      {article.url && (
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center text-sm text-primary hover:underline"
                        >
                          Read full article
                          <ExternalLink className="ml-1 h-4 w-4" />
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
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && hasSearched && articles.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <Search className="mx-auto h-12 w-12 text-muted-foreground/50" />
            <h3 className="mt-4 text-lg font-medium">No articles found</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Try different keywords or check your NewsAPI configuration.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Initial State */}
      {!hasSearched && !loading && (
        <Card>
          <CardContent className="p-12 text-center">
            <Search className="mx-auto h-12 w-12 text-muted-foreground/50" />
            <h3 className="mt-4 text-lg font-medium">Search for news articles</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Enter keywords above to search for relevant news articles using NewsAPI.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
