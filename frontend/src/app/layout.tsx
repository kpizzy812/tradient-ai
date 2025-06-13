// src/app/layout.tsx
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Tradient AI Mini App',
  description: 'Your Tradient AI dashboard',
};

const geistSans = Geist({ variable: '--font-geist-sans', subsets: ['latin'] });
const geistMono = Geist_Mono({ variable: '--font-geist-mono', subsets: ['latin'] });

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
