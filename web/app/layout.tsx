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
    "Evidence-backed company activity and market climate-target alignment across sectors.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${mono.variable}`}>
      <body className="dark-app">
        <div className="shell">
          <header className="topbar">
            <Link href="/" className="wordmark">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img className="brand-logo" src="/planit-logo-white.png" alt="PLANiT Institute" height={22} />
              <span className="brand-lockup">
                Trade Impact
                <small>company activity × market targets</small>
              </span>
            </Link>
            <nav className="topnav" aria-label="Primary navigation">
              <Link href="/">Story</Link>
              <Link href="/analysis/toyota">Analysis</Link>
              <Link href="/#markets">Markets</Link>
              <Link href="/#sectors">Sectors</Link>
              <Link href="/#method">Method</Link>
              <Link href="/calculator" className="nav-cta">Research calculator</Link>
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
              <p>Company activity mapped to comparable market climate targets.</p>
            </div>
            <p>
              Direct arithmetic is published only when sector, metric definition, geography,
              and unit match. Contextual pathways remain context. Published under GNU GPL v3 ·
              © 2026 PLANiT Institute.
            </p>
          </footer>
        </div>
      </body>
    </html>
  );
}
