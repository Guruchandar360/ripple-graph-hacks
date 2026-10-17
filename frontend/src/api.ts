export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
  ) {
    super(message);
  }
}
export const isShowcase = import.meta.env.VITE_STATIC_SHOWCASE === "true";
export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  if (isShowcase && options?.method && options.method !== "GET") {
    throw new ApiError("This is a read-only showcase of recorded runs. Use the documented local setup for live investigations.", "showcase_readonly", 405);
  }
  const url = isShowcase
    ? `${import.meta.env.BASE_URL}showcase/${path.slice(1).replaceAll("/", "-").split("?")[0]}.json`
    : `/api${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
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
