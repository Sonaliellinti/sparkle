export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Concept {
  id: number;
  slug: string;
  name: string;
  description: string;
  subject: string;
  difficulty_level: number;
}

export interface ConceptDependency {
  id: number;
  prerequisite_id: number;
  dependent_id: number;
  weight: number;
}

export interface ConceptGraph {
  nodes: Concept[];
  edges: ConceptDependency[];
}

export interface QuestionPublic {
  id: number;
  concept_id: number;
  text: string;
  options: Record<string, string>;
  difficulty: number;
}

export interface QuizAttempt {
  id: number;
  user_id: number;
  status: "in_progress" | "completed" | "abandoned";
  started_at: string;
  completed_at: string | null;
}

export interface QuizResponseRead {
  id: number;
  question_id: number;
  selected_option: string | null;
  is_correct: boolean;
  confidence: number;
  reasoning_text: string;
  time_taken_seconds: number;
}

export interface ConceptDiagnosisEntry {
  concept_id: number;
  slug: string;
  name: string;
  score: number;
  is_propagated: boolean;
  hidden_risk: boolean;
  misconceptions: string[];
  root_cause_concept_id: number | null;
}

export interface DiagnosisReport {
  id: number;
  attempt_id: number;
  summary: {
    weak_concepts: ConceptDiagnosisEntry[];
    hidden_risks: ConceptDiagnosisEntry[];
    all_scores: Record<string, number>;
  };
  generated_at: string;
}

export type MasteryLevel = "weak" | "moderate" | "strong";

export interface ConceptMastery {
  concept_id: number;
  score: number;
  level: MasteryLevel;
  is_propagated: boolean;
  updated_at: string;
}

export type Subject = "dsa" | "python" | "sql" | "ml";

export interface RoadmapResponse {
  attempt_id: number;
  weak_concepts: ConceptDiagnosisEntry[];
  roadmap: string;
}

export interface SubjectRoadmapResponse {
  subject: string;
  weak_concepts: ConceptDiagnosisEntry[];
  roadmap: string;
}

export interface TutorMessage {
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}

export interface TutorReply {
  reply: string;
  weak_concepts: string[];
}
