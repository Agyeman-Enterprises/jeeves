import type { Metadata } from "next";
import "./globals.css";
import { JarvisThemeProvider } from "@/components/theme/JarvisThemeProvider";
import { JarvisWorkspaceProvider } from "@/components/jarvis/JarvisWorkspaceContext";
import { AuthProvider } from '@/auth-template/components/AuthProvider';

export const metadata: Metadata = {
  title: "JARVIS",
  description: "Your personal AI operating system.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "JARVIS",
  },
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
    viewportFit: "cover",
  },
  themeColor: "#0a0a0f",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 antialiased">
        <AuthProvider>
          <JarvisThemeProvider>
            <JarvisWorkspaceProvider>{children}</JarvisWorkspaceProvider>
          </JarvisThemeProvider>
        </AuthProvider>
      </body>
    </html>
  );
}

