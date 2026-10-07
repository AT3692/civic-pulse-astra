import { afterEach, expect, it, vi } from "vitest";
// These tests exercise the real typed HTTP adapter, not the component-level mock.
afterEach(() => {
  vi.unstubAllGlobals();
  vi.resetModules();
});
async function clientWith(response: Response) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
  const { api } = await import("../src/api/client");
  return api;
}
it("preserves the server conflict message after openapi-fetch consumes the body", async () => {
  const api = await clientWith(
    new Response(
      JSON.stringify({ detail: "Invalid status transition: resolved → open" }),
      { status: 409, headers: { "Content-Type": "application/json" } },
    ),
  );
  await expect(api.transition("123", "open", "key")).rejects.toThrow(
    "Invalid status transition: resolved → open",
  );
});
it("renders field-level validation messages", async () => {
  const api = await clientWith(
    new Response(
      JSON.stringify({
        detail: "Validation failed",
        errors: [{ field: "body.text", message: "Too short" }],
      }),
      { status: 400, headers: { "Content-Type": "application/json" } },
    ),
  );
  await expect(api.create({ text: "short", location: "G9" })).rejects.toThrow(
    "body.text: Too short",
  );
});
it("includes Retry-After in rate-limit errors", async () => {
  const api = await clientWith(
    new Response(JSON.stringify({ detail: "Submission rate limit exceeded" }), {
      status: 429,
      headers: { "Content-Type": "application/json", "Retry-After": "24" },
    }),
  );
  await expect(
    api.create({ text: "Burst water pipe", location: "G9" }),
  ).rejects.toThrow("retry in 24s");
});
