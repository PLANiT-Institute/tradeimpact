import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, IBM_Plex_Serif } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const display = IBM_Plex_Serif({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-display",
});
const body = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-body",
});
const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "Trade Impact Framework — PLANiT Institute",
  description:
    "Firm-level climate direction: does a company's product portfolio contribute to or undermine each operating country's NDC-committed decarbonisation path?",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${mono.variable}`}>
      <body>
        <div className="shell">
          <header className="topbar">
            <Link href="/" className="wordmark">
              Trade Impact <span>· PLANiT Institute</span>
            </Link>
            <nav className="topnav">
              <Link href="/">Assessments</Link>
              <Link href="/calculator">Assumptions</Link>
              <a href="https://transitionarc.climatearc.org">Methodology</a>
            </nav>
          </header>
          {children}
          <footer className="site">
            TI is a separate additional disclosure alongside Scope 3 Category 11 — never
            netted against it. All results report the full S1/S2/S3 scenario triplet.
            Published under GNU GPL v3 · © 2026 PLANiT Institute.
          </footer>
        </div>
      </body>
    </html>
  );
}
