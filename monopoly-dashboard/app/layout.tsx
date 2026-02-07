import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { WebSocketProvider } from "@/providers/WebSocketProvider";
import { Toaster } from "sonner";
import { Navigation } from "@/components/Navigation";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Monopoly Agents - Polymarket Trading Dashboard",
  description: "Real-time dashboard for Polymarket prediction agent system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <WebSocketProvider>
          <Toaster position="top-right" richColors />
          <div className="min-h-screen bg-background">
            <Navigation />

            {/* Main Content */}
            <main className="container py-8">
              {children}
            </main>

            {/* Footer */}
            <footer className="border-t bg-background mt-12">
              <div className="container py-4">
                <p className="text-center text-sm text-muted-foreground">
                  Monopoly Agents v0.1.0 | Polymarket Prediction Agent System
                </p>
              </div>
            </footer>
          </div>
        </WebSocketProvider>
      </body>
    </html>
  );
}
