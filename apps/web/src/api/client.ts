import type {
  AnswerFeedback,
  AnswerFeedbackCreate,
  ApiErrorPayload,
  AskRequest,
  AskResponse,
  FeedbackQuery,
  FeedbackReviewRequest,
  HealthResponse,
  KnowledgeBaseChangeQuery,
  KnowledgeBaseChangeTask,
  LearningEvent,
  LearningEventQuery,
  QualityReview,
  ResourceUploadResponse,
  TaskPublishRequest,
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
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${apiBaseUrl}/api/v1${path}`, {
    ...init,
    headers: isFormData
      ? { ...init?.headers }
      : {
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

function queryString(params: object): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (typeof value === "string") query.set(key, value);
  });
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export const getHealth = () => request<HealthResponse>("/health");

export const askQuestion = (payload: AskRequest) =>
  request<AskResponse>("/qa/ask", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const listTasks = () => request<TaskTemplate[]>("/tasks");

export const publishTask = (payload: TaskPublishRequest) =>
  request<TaskTemplate>("/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const getTask = (taskId: string) =>
  request<TaskTemplate>(`/tasks/${encodeURIComponent(taskId)}`);

export const recordEvent = (event: LearningEvent) =>
  request<LearningEvent>("/events", {
    method: "POST",
    body: JSON.stringify(event),
  });

export const queryEvents = (params: LearningEventQuery = {}) =>
  request<LearningEvent[]>(`/events${queryString(params)}`);

export const createFeedback = (payload: AnswerFeedbackCreate) =>
  request<AnswerFeedback>("/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const listFeedback = (params: FeedbackQuery = {}) =>
  request<AnswerFeedback[]>(`/feedback${queryString(params)}`);

export const getFeedback = (feedbackId: string) =>
  request<AnswerFeedback>(`/feedback/${encodeURIComponent(feedbackId)}`);

export const reviewFeedback = (feedbackId: string, payload: FeedbackReviewRequest) =>
  request<AnswerFeedback>(`/feedback/${encodeURIComponent(feedbackId)}/review`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const listKnowledgeBaseChanges = (params: KnowledgeBaseChangeQuery = {}) =>
  request<KnowledgeBaseChangeTask[]>(
    `/knowledge-base/changes${queryString(params)}`,
  );

export const getKnowledgeBaseChange = (changeId: string) =>
  request<KnowledgeBaseChangeTask>(
    `/knowledge-base/changes/${encodeURIComponent(changeId)}`,
  );

export const listQualityReviews = () => request<QualityReview[]>("/quality/reviews");

export const uploadResource = (formData: FormData) =>
  request<ResourceUploadResponse>("/resources/upload", {
    method: "POST",
    body: formData,
  });
