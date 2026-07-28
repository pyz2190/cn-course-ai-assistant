import type {
  ApiErrorPayload,
  AskRequest,
  AskResponse,
  HealthResponse,
  LearningEvent,
  TaskTemplate,
} from "./types";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export class ApiClientError extends Error {
  readonly code: string;
  readonly requestId: string;

  constructor(payload: ApiErrorPayload) {
    super(payload.message);
    this.name = "ApiClientError";
    this.code = payload.code;
    this.requestId = payload.request_id;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}/api/v1${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  const payload = (await response.json()) as T | ApiErrorPayload;
  if (!response.ok) {
    throw new ApiClientError(payload as ApiErrorPayload);
  }
  return payload as T;
}

export const getHealth = () => request<HealthResponse>("/health");

export const askQuestion = (payload: AskRequest) =>
  request<AskResponse>("/qa/ask", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const listTasks = () => request<TaskTemplate[]>("/tasks");

export const getTask = (taskId: string) =>
  request<TaskTemplate>(`/tasks/${encodeURIComponent(taskId)}`);

export const recordEvent = (event: LearningEvent) =>
  request<LearningEvent>("/events", {
    method: "POST",
    body: JSON.stringify(event),
  });
