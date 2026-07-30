"use client";

import * as React from "react";
import Link from "next/link";
import { TrendingUp, ListChecks, Sparkles } from "lucide-react";
import { RequireAuth } from "@/components/layout/require-auth";
import { AppShell } from "@/components/layout/app-shell";
import { SubjectCard, type SubjectDefinition } from "@/components/dashboard/subject-card";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { conceptsApi, dashboardApi, quizApi } from "@/lib/api";
import type { Concept, ConceptMastery, QuizAttempt } from "@/lib/api/types";

const SUBJECTS: SubjectDefinition[] = [
  { slug: "dsa", label: "DSA" },
  { slug: "python", label: "Python" },
  { slug: "sql", label: "SQL" },
  { slug: "ml", label: "Machine Learning" },
];

export default function DashboardPage() {
  return (
    <RequireAuth>
      <AppShell>
        <DashboardContent />
      </AppShell>
    </RequireAuth>
  );
}

function DashboardContent() {
  const [concepts, setConcepts] = React.useState<Concept[]>([]);
  const [mastery, setMastery] = React.useState<ConceptMastery[]>([]);
  const [attempts, setAttempts] = React.useState<QuizAttempt[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    Promise.all([conceptsApi.list(), dashboardApi.mastery(), quizApi.listAttempts()])
      .then(([c, m, a]) => {
        setConcepts(c);
        setMastery(m);
        setAttempts(a);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  const conceptById = new Map(concepts.map((c) => [c.id, c]));
  const completedAttempts = attempts.filter((a) => a.status === "completed");
  const trackedMastery = mastery.filter((m) => conceptById.has(m.concept_id));
  const overallAvg =
    trackedMastery.length > 0
      ? trackedMastery.reduce((sum, m) => sum + m.score, 0) / trackedMastery.length
      : 0;
  const totalWeak = trackedMastery.filter((m) => m.level === "weak").length;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-semibold">Your readiness</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Four independent subject modules — each with its own randomized
          quizzes, mastery tracking, and AI recommendations.
        </p>
      </div>

      {trackedMastery.length === 0 ? (
        <Card className="max-w-lg mx-auto text-center py-6">
          <CardHeader>
            <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
              <Sparkles className="h-6 w-6 text-accent" />
            </div>
            <CardTitle>No diagnosis yet</CardTitle>
            <CardDescription>
              Pick a subject below and take its first quiz to start tracking
              your progress.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-1.5">
                <TrendingUp className="h-3.5 w-3.5" /> Overall mastery
              </CardDescription>
              <CardTitle className="text-3xl">{Math.round(overallAvg * 100)}%</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-1.5">
                <ListChecks className="h-3.5 w-3.5" /> Quizzes completed
              </CardDescription>
              <CardTitle className="text-3xl">{completedAttempts.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-1.5">
                Weak concepts (all subjects)
              </CardDescription>
              <CardTitle className="text-3xl">{totalWeak}</CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      <div>
        <h2 className="font-display text-lg font-semibold mb-3">Subjects</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {SUBJECTS.map((subject) => {
            const subjectConcepts = concepts.filter((c) => c.subject === subject.slug);
            const subjectConceptIds = new Set(subjectConcepts.map((c) => c.id));
            const subjectMastery = mastery.filter((m) => subjectConceptIds.has(m.concept_id));
            return (
              <SubjectCard
                key={subject.slug}
                subject={subject}
                concepts={subjectConcepts}
                mastery={subjectMastery}
              />
            );
          })}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent quizzes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {attempts.length === 0 && (
            <p className="text-sm text-muted-foreground">No quizzes yet.</p>
          )}
          {attempts.slice(0, 5).map((a) => (
            <div key={a.id} className="flex items-center justify-between text-sm py-1.5 border-b border-border last:border-0">
              <span>Attempt #{a.id}</span>
              <span className="text-muted-foreground">
                {new Date(a.started_at).toLocaleDateString()}
              </span>
              <Badge variant={a.status === "completed" ? "strong" : "outline"}>{a.status}</Badge>
            </div>
          ))}
          <Button variant="outline" className="w-full mt-2" asChild>
            <Link href="/quiz">Take a mixed practice quiz</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
