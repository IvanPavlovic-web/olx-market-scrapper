import "@/styles/globals.css";
import type { Metadata } from "next";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "OLX Monitor BiH",
  description: "Real-time praćenje cijena i oglasa",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="bs">
      <body>
        {children}
        <Toaster position="top-right" theme="dark" />
      </body>
    </html>
  );
}
