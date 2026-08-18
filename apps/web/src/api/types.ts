import type { components, operations } from "./schema";

export type AnswerFeedback = components["schemas"]["AnswerFeedback"];
export type AnswerFeedbackCreate = components["schemas"]["AnswerFeedbackCreate"];
export type ApiErrorPayload = components["schemas"]["ApiError"];
export type AskRequest = components["schemas"]["AskRequest"];
export type AskResponse = components["schemas"]["AskResponse"];
export type FeedbackQuery = NonNullable<
  operations["list_feedback_api_v1_feedback_get"]["parameters"]["query"]
>;
export type FeedbackReviewRequest = components["schemas"]["FeedbackReviewRequest"];
export type HealthResponse = components["schemas"]["HealthResponse"];
export type KnowledgeBaseChangeQuery = NonNullable<
  operations["list_changes_api_v1_knowledge_base_changes_get"]["parameters"]["query"]
>;
export type KnowledgeBaseChangeTask = components["schemas"]["KnowledgeBaseChangeTask"];
export type LearningEvent = components["schemas"]["LearningEvent"];
export type LearningEventQuery = NonNullable<
  operations["query_events_api_v1_events_get"]["parameters"]["query"]
>;
export type QualityReview = components["schemas"]["QualityReview"];
export type ResourceUploadResponse = components["schemas"]["ResourceUploadResponse"];
export type TaskPublishRequest = components["schemas"]["TaskPublishRequest"];
export type TaskTemplate = components["schemas"]["TaskTemplate"];
export type TaskType = components["schemas"]["TaskType"];
