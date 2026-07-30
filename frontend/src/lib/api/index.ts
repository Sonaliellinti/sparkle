import { apiRequest } from "./client";
import type {
  AuthResponse,
  Concept,
  ConceptGraph,
  ConceptMastery,
  DiagnosisReport,
  QuestionPublic,
  QuizAttempt,
  QuizResponseRead,
  RoadmapResponse,
  SubjectRoadmapResponse,
  TutorMessage,
  TutorReply,
  User,
} from "./types";

// ── Auth ──────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: {
    username: string;
    email: string;
    full_name: string;
    password: string;
  }) => apiRequest<AuthResponse>("/auth/register", { method: "POST", body: data, skipAuth: true }),

  login: (username: string, password: string) =>
    apiRequest<AuthResponse>("/auth/login", {
      method: "POST",
      formBody: { username, password },
      skipAuth: true,
    }),

  me: () => apiRequest<User>("/auth/me"),
};

// ── Concepts / graph ────────────────────────────────────────────────────────
export const conceptsApi = {
  list: () => apiRequest<Concept[]>("/concepts"),
  graph: () => apiRequest<ConceptGraph>("/concepts/graph"),
  prerequisites: (conceptId: number) =>
    apiRequest<Concept[]>(`/concepts/${conceptId}/prerequisites`),
  questions: (conceptId: number) =>
    apiRequest<QuestionPublic[]>(`/concepts/${conceptId}/questions`),
};

// ── Quiz ─────────────────────────────────────────────────────────────────
export const quizApi = {
  startAttempt: () => apiRequest<QuizAttempt>("/quiz/attempts", { method: "POST" }),
  listAttempts: () => apiRequest<QuizAttempt[]>("/quiz/attempts"),
  listQuestions: () => apiRequest<QuestionPublic[]>("/quiz/questions"),
  generateQuiz: (subject?: string, counts?: { easy?: number; medium?: number; hard?: number }) => {
    const params = new URLSearchParams();
    if (subject) params.set("subject", subject);
    if (counts?.easy !== undefined) params.set("easy", String(counts.easy));
    if (counts?.medium !== undefined) params.set("medium", String(counts.medium));
    if (counts?.hard !== undefined) params.set("hard", String(counts.hard));
    const qs = params.toString();
    return apiRequest<QuestionPublic[]>(`/quiz/generate${qs ? `?${qs}` : ""}`);
  },
  submitResponse: (
    attemptId: number,
    data: {
      question_id: number;
      selected_option: string;
      confidence: number;
      reasoning_text?: string;
      time_taken_seconds?: number;
    }
  ) =>
    apiRequest<QuizResponseRead>(`/quiz/attempts/${attemptId}/responses`, {
      method: "POST",
      body: data,
    }),
  complete: (attemptId: number) =>
    apiRequest<QuizAttempt>(`/quiz/attempts/${attemptId}/complete`, { method: "POST" }),
};

// ── Diagnosis / dashboard ────────────────────────────────────────────────
export const diagnosisApi = {
  getForAttempt: (attemptId: number) =>
    apiRequest<DiagnosisReport>(`/diagnosis/attempts/${attemptId}`),
};

export const dashboardApi = {
  mastery: () => apiRequest<ConceptMastery[]>("/dashboard/mastery"),
};

// ── AI features ──────────────────────────────────────────────────────────
export const aiApi = {
  explainMistake: (responseId: number) =>
    apiRequest<{ response_id: number; explanation: string }>(
      `/ai/explain-mistake/${responseId}`
    ),
  roadmap: (attemptId: number) =>
    apiRequest<RoadmapResponse>(`/ai/roadmap/${attemptId}`),
  subjectRoadmap: (subject: string) =>
    apiRequest<SubjectRoadmapResponse>(`/ai/roadmap/subject/${subject}`),
  tutorChat: (message: string) =>
    apiRequest<TutorReply>("/ai/tutor", { method: "POST", body: { message } }),
  tutorHistory: () => apiRequest<TutorMessage[]>("/ai/tutor/history"),
};
