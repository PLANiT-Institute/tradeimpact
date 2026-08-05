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
    "Company sold-product cohorts mapped to lifetime use-phase emissions and destination climate pathways.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${body.variable} ${mono.variable}`}
      data-scroll-behavior="smooth"
    >
      <body className="dark-app">
        <div className="shell">
          <header className="topbar">
            <Link href="/" className="wordmark">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img className="brand-logo" src="/planit-logo-white.png" alt="PLANiT Institute" height={22} />
              <span className="brand-lockup">
                Trade Impact
                <small>sold products × destination NDCs</small>
              </span>
            </Link>
            <nav className="topnav" aria-label="Primary navigation">
              <Link href="/#purpose">Purpose</Link>
              <Link href="/analysis/toyota">Toyota pilot</Link>
              <Link href="/#sectors">Sectors</Link>
              <Link href="/#method">Method</Link>
            </nav>
          </header>
          {children}
          <footer className="site">
            <div>
              <a className="planit-mark" href="https://planit.institute" aria-label="PLANiT Institute">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/planit-logo-white.png" alt="PLANiT Institute" height={20} />
              </a>
              <strong>Trade Impact</strong>
              <p>Sold-product lifetime emissions mapped to destination climate pathways.</p>
            </div>
            <p>
              Observed activity, sourced scenarios, and derived results remain separate. Missing
              lifetime inputs never become zero or an invented estimate. Published under GNU GPL
              v3 · © 2026 PLANiT Institute.
            </p>
          </footer>
        </div>
      </body>
    </html>
  );
}
