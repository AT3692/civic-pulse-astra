import { useState, type FormEvent } from "react";
import { api, type Complaint } from "../api/client";
export function Submit() {
  const [text, setText] = useState("");
  const [location, setLocation] = useState("");
  const [contact, setContact] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Complaint | null>(null);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setResult(null);
    if (
      text.trim().length < 10 ||
      text.trim().length > 2000 ||
      location.trim().length < 3 ||
      location.trim().length > 200
    ) {
      setError(
        "Describe the issue in 10–2000 characters and its location in 3–200 characters.",
      );
      return;
    }
    setBusy(true);
    try {
      setResult(
        await api.create({
          text: text.trim(),
          location: location.trim(),
          reporter_contact: contact.trim() || null,
        }),
      );
      setText("");
      setLocation("");
      setContact("");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="submit-grid">
      <section>
        <span className="eyebrow">MAKE YOUR NEIGHBOURHOOD BETTER</span>
        <h1>
          A small report.
          <br />A better city.
        </h1>
        <p className="lead">
          Tell us what needs attention. CivicPulse classifies your report and
          sends it to the city’s operations queue.
        </p>
        <div className="note">
          <strong>Describe what you see.</strong>
          <p>
            You don’t need to choose a category or urgency. Include when it
            started and who is affected. Avoid names, phone numbers, or other
            personal details in your description.
          </p>
        </div>
        <p className="muted">
          This is a university demonstration, not an emergency dispatch service.
        </p>
      </section>
      <section className="panel">
        <h2>Report an issue</h2>
        <form onSubmit={submit}>
          <label htmlFor="text">What’s happening?</label>
          <textarea
            id="text"
            required
            minLength={10}
            maxLength={2000}
            rows={6}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Water pipe burst near the market since fajr, flooding the road…"
          />
          <span className="counter">{text.length} / 2000</span>
          <label htmlFor="location">Location</label>
          <input
            id="location"
            required
            minLength={3}
            maxLength={200}
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Sector, street, and a nearby landmark"
          />
          <label htmlFor="contact">
            Contact <span className="muted">(optional, kept private)</span>
          </label>
          <input
            id="contact"
            maxLength={254}
            value={contact}
            onChange={(e) => setContact(e.target.value)}
            placeholder="Email or phone number"
          />
          <p className="muted small">
            Descriptions and locations appear on the public dashboard. With
            hosted AI enabled, the description is sent to the AI provider after
            basic email and phone redaction.
          </p>
          <button className="primary" disabled={busy}>
            {busy ? "Classifying your report…" : "Submit report ↗"}
          </button>
          {busy && (
            <p role="status">
              AI triage can take up to 25 seconds. Please keep this page open.
            </p>
          )}
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </form>
        {result && (
          <div className="receipt" role="status">
            <h3>Report received</h3>
            <p>{result.ai_summary}</p>
            <div className="tags">
              <span>{result.category}</span>
              <span className={result.priority}>
                {result.priority} priority
              </span>
            </div>
            <p className="small">
              Triaged by <strong>{result.triaged_by}</strong> ·{" "}
              {result.triage_latency_ms} ms
            </p>
            <p className="muted small">Reference: {result.id}</p>
          </div>
        )}
      </section>
    </div>
  );
}
