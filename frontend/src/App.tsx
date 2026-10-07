import { useState } from "react";
import { Submit } from "./pages/Submit";
import { Dashboard } from "./pages/Dashboard";
import { Stats } from "./pages/Stats";
export function App() {
  const [tab, setTab] = useState("Report an issue");
  return (
    <>
      <header>
        <a className="brand" href="#" onClick={() => setTab("Report an issue")}>
          <span className="brand-mark">c.</span>CivicPulse
        </a>
        <nav aria-label="Main navigation">
          {["Report an issue", "Dashboard", "City stats"].map((label) => (
            <button
              key={label}
              aria-current={tab === label ? "page" : undefined}
              onClick={() => setTab(label)}
            >
              {label}
            </button>
          ))}
        </nav>
        <span className="header-note">Better cities, together.</span>
      </header>
      <main className="shell">
        {tab === "Report an issue" ? (
          <Submit />
        ) : tab === "Dashboard" ? (
          <Dashboard />
        ) : (
          <Stats />
        )}
      </main>
      <footer>
        <span>CivicPulse / Islamabad</span>
        <span>Built for people. Powered by participation.</span>
      </footer>
    </>
  );
}
