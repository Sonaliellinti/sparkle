"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle2, XCircle, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { RequireAuth } from "@/components/layout/require-auth";
import { AppShell } from "@/components/layout/app-shell";
import { QuestionCard } from "@/components/quiz/question-card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { quizApi } from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import type { QuestionPublic, QuizResponseRead } from "@/lib/api/types";

const SUBJECT_LABELS: Record<string, string> = {
  dsa: "DSA",
  python: "Python",
  sql: "SQL",
  ml: "Machine Learning",
};

type Stage = "loading" | "intro" | "in_progress" | "submitting" | "done" | "error";

export default function QuizPage() {
  return (
    <RequireAuth>
      <AppShell>
        <React.Suspense fallback={<div className="text-muted-foreground">Loading…</div>}>
          <QuizFlow />
        </React.Suspense>
      </AppShell>
    </RequireAuth>
  );
}

function QuizFlow() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const subject = searchParams.get("subject") || undefined;

  const [stage, setStage] = React.useState<Stage>("loading");
  const [questions, setQuestions] = React.useState<QuestionPublic[]>([]);
  const [attemptId, setAttemptId] = React.useState<number | null>(null);
  const [currentIndex, setCurrentIndex] = React.useState(0);
  const [results, setResults] = React.useState<QuizResponseRead[]>([]);

  React.useEffect(() => {
    setStage("intro");
  }, [subject]);

  async function handleStart() {
    try {
      setStage("loading");
      const [attempt, qs] = await Promise.all([
        quizApi.startAttempt(),
        quizApi.generateQuiz(subject),
      ]);
      setAttemptId(attempt.id);
      setQuestions(qs);
      setCurrentIndex(0);
      setResults([]);
      setStage("in_progress");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not start the quiz.");
      setStage("intro");
    }
  }

  async function handleAnswer(answer: {
    selected_option: string;
    confidence: number;
    reasoning_text: string;
    time_taken_seconds: number;
  }) {
    if (!attemptId) return;
    const question = questions[currentIndex];
    try {
      const result = await quizApi.submitResponse(attemptId, {
        question_id: question.id,
        ...answer,
      });
      setResults((r) => [...r, result]);

      if (currentIndex + 1 < questions.length) {
        setCurrentIndex((i) => i + 1);
      } else {
        setStage("submitting");
        await quizApi.complete(attemptId);
        setStage("done");
      }
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not submit your answer.");
    }
  }

  if (stage === "loading") {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20 text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin" />
        Preparing your quiz…
      </div>
    );
  }

  if (stage === "error") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Couldn&apos;t load questions</CardTitle>
          <CardDescription>
            Make sure the backend is running and seeded, then refresh this page.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (stage === "intro") {
    const label = subject ? SUBJECT_LABELS[subject] || subject : "Mixed";
    return (
      <Card className="max-w-xl mx-auto">
        <CardHeader>
          <CardTitle>{label} Practice Quiz</CardTitle>
          <CardDescription>
            A fresh, randomly generated set of Easy/Medium/Hard questions —
            different every attempt. For each one, pick an answer, rate how
            confident you are, and optionally say why you chose it — that&apos;s
            what lets the diagnosis engine tell a lucky guess from real
            understanding.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button size="lg" className="w-full" onClick={handleStart}>
            <Sparkles className="h-4 w-4" /> Start {label} quiz
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (stage === "submitting") {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20 text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin" />
        Running your diagnosis…
      </div>
    );
  }

  if (stage === "done") {
    const correctCount = results.filter((r) => r.is_correct).length;
    return (
      <Card className="max-w-xl mx-auto">
        <CardHeader>
          <CardTitle>Quiz complete</CardTitle>
          <CardDescription>
            You got {correctCount} of {results.length} correct. Your full
            diagnosis — including concepts you never directly answered a
            question on — is ready on your dashboard.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <ul className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
            {results.map((r, i) => (
              <li key={r.id} className="flex items-center gap-2 text-sm">
                {r.is_correct ? (
                  <CheckCircle2 className="h-4 w-4 text-mastery-strong shrink-0" />
                ) : (
                  <XCircle className="h-4 w-4 text-mastery-weak shrink-0" />
                )}
                Question {i + 1} — confidence {r.confidence}/5
              </li>
            ))}
          </ul>
          <Button className="w-full" size="lg" onClick={() => router.push("/dashboard")}>
            View my diagnosis
          </Button>
        </CardContent>
      </Card>
    );
  }

  const question = questions[currentIndex];
  return (
    <div className="max-w-xl mx-auto space-y-4">
      <Progress value={((currentIndex) / questions.length) * 100} />
      <QuestionCard
        question={question}
        index={currentIndex}
        total={questions.length}
        onSubmit={handleAnswer}
      />
    </div>
  );
}
