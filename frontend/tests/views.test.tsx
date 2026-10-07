import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Submit } from "../src/pages/Submit";
import { Dashboard } from "../src/pages/Dashboard";
import { Stats } from "../src/pages/Stats";
import { ErrorBoundary } from "../src/components/ErrorBoundary";
import { api, type Complaint } from "../src/api/client";
vi.mock("../src/api/client", () => ({
  api: {
    create: vi.fn(),
    list: vi.fn(),
    transition: vi.fn(),
    stats: vi.fn(),
    providers: vi.fn(),
  },
}));
const item: Complaint = {
  id: "123",
  text: "Water pipe is flooding the road",
  location: "G-9 Islamabad",
  reporter_contact: null,
  category: "water",
  priority: "high",
  status: "open",
  ai_summary: "Burst water pipe",
  triaged_by: "rules:fallback",
  triage_latency_ms: 8,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  allowed_transitions: ["in_progress"],
};
function fill() {
  fireEvent.change(screen.getByLabelText("What’s happening?"), {
    target: { value: item.text },
  });
  fireEvent.change(screen.getByLabelText("Location"), {
    target: { value: item.location },
  });
}
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.list).mockResolvedValue({
    items: [item],
    total: 1,
    page: 1,
    page_size: 10,
  });
});
describe("citizen submission", () => {
  it("rejects whitespace-only content without a network call", () => {
    render(<Submit />);
    fill();
    fireEvent.change(screen.getByLabelText("What’s happening?"), {
      target: { value: "          " },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: /Submit report/ }).closest("form")!,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("10–2000");
    expect(api.create).not.toHaveBeenCalled();
  });
  it("shows pending state then the category, priority, summary and provider", async () => {
    let resolve!: (v: Complaint) => void;
    vi.mocked(api.create).mockImplementation(
      () =>
        new Promise((r) => {
          resolve = r;
        }),
    );
    render(<Submit />);
    fill();
    fireEvent.click(screen.getByRole("button", { name: /Submit report/ }));
    expect(screen.getByRole("button", { name: /Classifying/ })).toBeDisabled();
    resolve(item);
    expect(await screen.findByText("Report received")).toBeInTheDocument();
    expect(screen.getByText("water")).toBeInTheDocument();
    expect(screen.getByText("high priority")).toBeInTheDocument();
    expect(screen.getByText("rules:fallback")).toBeInTheDocument();
    expect(screen.getByText("Burst water pipe")).toBeInTheDocument();
  });
  it("preserves the report after a failed submission", async () => {
    vi.mocked(api.create).mockRejectedValue(
      new Error("Rate limit exceeded — retry in 30s"),
    );
    render(<Submit />);
    fill();
    fireEvent.click(screen.getByRole("button", { name: /Submit report/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("retry in 30s");
    expect(screen.getByLabelText("What’s happening?")).toHaveValue(item.text);
  });
});
it("renders only server-provided transitions and surfaces a 409 message", async () => {
  vi.mocked(api.transition).mockRejectedValue(
    new Error("Invalid status transition: open → resolved"),
  );
  render(<Dashboard />);
  fireEvent.click(await screen.findByRole("button", { name: "in progress" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Invalid status transition: open → resolved",
  );
  expect(
    screen.queryByRole("button", { name: "resolved" }),
  ).not.toBeInTheDocument();
});
it("sends pagination and category filters to the API", async () => {
  vi.mocked(api.list).mockResolvedValue({
    items: [item],
    total: 21,
    page: 1,
    page_size: 10,
  });
  render(<Dashboard />);
  await screen.findByText("Burst water pipe");
  fireEvent.click(screen.getByRole("button", { name: /Next/ }));
  await waitFor(() =>
    expect(api.list).toHaveBeenLastCalledWith(
      expect.objectContaining({ page: 2 }),
      expect.any(AbortSignal),
    ),
  );
  fireEvent.change(screen.getByLabelText("Category"), {
    target: { value: "water" },
  });
  await waitFor(() =>
    expect(api.list).toHaveBeenLastCalledWith(
      expect.objectContaining({ page: 1, category: "water" }),
      expect.any(AbortSignal),
    ),
  );
});
it("displays server cache headers and provider hit rate", async () => {
  vi.mocked(api.stats).mockResolvedValue({
    data: {
      total: 4,
      by_category: { water: 4 },
      by_priority: { high: 4 },
      by_status: { open: 4 },
    },
    cache: "HIT",
  });
  vi.mocked(api.providers).mockResolvedValue({
    active_provider: "simulated",
    outcomes: [],
    triage_cache_hits: 2,
    triage_cache_requests: 4,
    triage_cache_hit_rate: 0.5,
  });
  render(<Stats />);
  expect(await screen.findByText("HIT")).toBeInTheDocument();
  expect(screen.getByText("50.0%")).toBeInTheDocument();
});
it("provides recovery when a component fails", () => {
  vi.spyOn(console, "error").mockImplementation(() => {});
  function Broken(): never {
    throw new Error("render failure");
  }
  render(
    <ErrorBoundary>
      <Broken />
    </ErrorBoundary>,
  );
  expect(screen.getByRole("button", { name: "Reload" })).toBeInTheDocument();
});
