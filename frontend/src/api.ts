export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
  ) {
    super(message);
  }
}
export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      credentials: "same-origin",
      ...options,
      headers: { "Content-Type": "application/json", ...options?.headers },
      signal: AbortSignal.timeout(15000),
    });
  } catch {
    throw new ApiError(
      "The server could not be reached. Check the connection and retry.",
      "network",
      0,
    );
  }
  let body;
  try {
    body = await response.json();
  } catch {
    throw new ApiError(
      "The server is starting or returned an unexpected response. Please retry.",
      "startup",
      response.status,
    );
  }
  if (!response.ok)
    throw new ApiError(
      body.error?.message ?? "Request failed.",
      body.error?.code ?? "request_failed",
      response.status,
    );
  return body as T;
}
export const post = <T>(path: string, body: unknown = {}) =>
  api<T>(path, { method: "POST", body: JSON.stringify(body) });
