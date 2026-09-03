import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Razorpay RecoveryAI — Autonomous AI Revenue Recovery Dashboard',
  description: 'Next.js & Three.js 3D Interactive Revenue Recovery Platform for Razorpay Buildathon (Track 03)',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-brand-dark text-slate-100 min-h-screen font-sans antialiased selection:bg-brand-blue selection:text-white">
        {children}
      </body>
    </html>
  );
}
