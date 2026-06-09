import type { Metadata } from "next";

import "../styles/globals.css";

export const metadata: Metadata = {
  title: "Visa Cabinet Mini App",
  description: "Клиентский Mini App для заполнения анкет заявителей"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
