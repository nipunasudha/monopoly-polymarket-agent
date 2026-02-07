'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Bug } from 'lucide-react';
import { cn } from '@/lib/utils';
import { TradingModeBadge } from '@/components/TradingModeBadge';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';

const navItems = [
  { href: '/', label: 'Portfolio' },
  { href: '/agent', label: 'Agent' },
  { href: '/markets', label: 'Markets' },
  { href: '/trades', label: 'Trades' },
  { href: '/forecasts', label: 'Forecasts' },
  { href: '/news', label: 'News' },
  { href: '/tracking', label: 'Tracking' },
  { href: '/debug', label: 'Debug', iconOnly: true },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto flex h-16 items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center space-x-2">
            <h1 className="text-xl font-bold">🎲 Monopoly Agents</h1>
          </Link>
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href || 
                (item.href !== '/' && pathname?.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'inline-flex items-center justify-center rounded-md transition-colors',
                    item.iconOnly ? 'px-2 py-2' : 'px-4 py-2',
                    'text-sm font-medium',
                    'hover:bg-accent hover:text-accent-foreground',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                    'disabled:pointer-events-none disabled:opacity-50',
                    isActive && 'bg-accent text-accent-foreground'
                  )}
                  title={item.iconOnly ? item.label : undefined}
                >
                  {item.iconOnly ? (
                    <Bug className="h-4 w-4" />
                  ) : (
                    item.label
                  )}
                </Link>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <ThemeSwitcher />
          <TradingModeBadge />
        </div>
      </div>
    </nav>
  );
}
