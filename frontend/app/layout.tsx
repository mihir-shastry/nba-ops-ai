import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "NBA Operations AI",
  description: "Basketball analytics dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-court-bg min-h-screen">
        <Providers>
          <div className="flex">
            <Sidebar />
            <main className="flex-1 p-8 overflow-auto">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
