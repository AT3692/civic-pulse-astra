import createClient from "openapi-fetch";
import type { components, paths } from "./schema";
const client = createClient<paths>({ baseUrl: window.location.origin });
export type Complaint = components["schemas"]["Complaint"];
export type ComplaintCreate = components["schemas"]["ComplaintCreate"];
export type ComplaintPage = components["schemas"]["ComplaintPage"];
export type Stats = components["schemas"]["Stats"];
export type ProviderMeta = components["schemas"]["ProviderMeta"];
export type Status = components["schemas"]["Status"];
export type Filters = {
  page: number;
  page_size: number;
  category?: components["schemas"]["Category"];
  priority?: components["schemas"]["Priority"];
  status?: Status;
};

async function unwrap<T>(result: {
  data?: T;
  response: Response;
  error?: unknown;
}): Promise<T> {
  if (!result.response.ok) {
    let message = `Request failed (${result.response.status})`;
    try {
      const body = (result.error || {}) as {
        detail?: string;
        errors?: { field: string; message: string }[];
      };
      message =
        body.errors
          ?.map(
            (e: { field: string; message: string }) =>
              `${e.field}: ${e.message}`,
          )
          .join("; ") ||
        body.detail ||
        message;
    } catch {
      /* Non-JSON gateway errors still get a readable message. */
    }
    const retry = result.response.headers.get("Retry-After");
    throw new Error(message + (retry ? ` — retry in ${retry}s` : ""));
  }
  return result.data as T;
}
export const api = {
  create: async (body: ComplaintCreate) =>
    unwrap<Complaint>(await client.POST("/api/complaints", { body })),
  list: async (query: Filters, signal?: AbortSignal) =>
    unwrap<ComplaintPage>(
      await client.GET("/api/complaints", { params: { query }, signal }),
    ),
  transition: async (id: string, status: Status, key: string) =>
    unwrap<Complaint>(
      await client.PATCH("/api/complaints/{complaint_id}/status", {
        params: { path: { complaint_id: id } },
        body: { status },
        headers: { "X-Operator-Key": key },
      }),
    ),
  stats: async (signal?: AbortSignal) => {
    const result = await client.GET("/api/stats", { signal });
    return {
      data: await unwrap<Stats>(result),
      cache: result.response.headers.get("X-Cache") || "UNKNOWN",
    };
  },
  providers: async (signal?: AbortSignal) =>
    unwrap<ProviderMeta>(await client.GET("/api/meta/providers", { signal })),
};
