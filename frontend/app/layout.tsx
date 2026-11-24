import type { Metadata, Viewport } from "next";
import { Bricolage_Grotesque, Hanken_Grotesk } from "next/font/google";
import "./globals.css";

// Two typefaces: Bricolage Grotesque for headings and big numbers, Hanken Grotesk for text.
const displayFace = Bricolage_Grotesque({
  variable: "--font-display-face",
  subsets: ["latin"],
});

const bodyFace = Hanken_Grotesk({
  variable: "--font-body-face",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Hostel Splitwise",
  description:
    "Split group expenses and settle up with the fewest payments. Each payment comes with a UPI link.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${displayFace.variable} ${bodyFace.variable} h-full antialiased`}>
      <body className="min-h-full">
        <div className="mx-auto flex min-h-screen w-full max-w-xl flex-col px-4 pb-10 pt-5">{children}</div>
      </body>
    </html>
  );
}
