import type { Metadata } from "next";
import "./globals.css";
import { DemoStoreProvider } from "@/lib/demo-store";
import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";

export const metadata: Metadata = {
  title: "Visa Atelier",
  description: "Frontend MVP для помощи с подготовкой к подаче на шенгенскую визу."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body>
        <DemoStoreProvider>
          <SiteHeader />
          <main>{children}</main>
          <SiteFooter />
        </DemoStoreProvider>
      </body>
    </html>
  );
}
