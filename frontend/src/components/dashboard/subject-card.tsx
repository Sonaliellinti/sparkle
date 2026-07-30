"use client";

import * as React from "react";
import Link from "next/link";
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";
import { Sparkles, ChevronUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { aiApi } from "@/lib/api";
import type { Concept, ConceptMastery } from "@/lib/api/types";

export interface SubjectDefinition {
  slug: string;
  label: string;
}

export function SubjectCard({
  subject,
  concepts,
  mastery,
}: {
  subject: SubjectDefinition;
  concepts: Concept[];
  mastery: ConceptMastery[];
}) {
  const [expanded, setExpanded] = React.useState(false);
  const [roadmap, setRoadmap] = React.useState<string | null>(null);
  const [loadingRoadmap, setLoadingRoadmap] = React.useState(false);

  const conceptById = new Map(concepts.map((c) => [c.id, c]));
  const hasData = mastery.length > 0;
  const avgMastery = hasData
    ? mastery.reduce((sum, m) => sum + m.score, 0) / mastery.length
    : 0;
  const weakCount = mastery.filter((m) => m.level === "weak").length;

  const chartData = mastery
    .map((m) => ({
      concept: conceptById.get(m.concept_id)?.name.split(" ").slice(0, 2).join(" ") ?? "?",
      mastery: Math.round(m.score * 100),
    }))
    .sort((a, b) => a.mastery - b.mastery);

  async function handleGetRecommendations() {
    if (roadmap) {
      setExpanded((e) => !e);
      return;
    }
    setLoadingRoadmap(true);
    setExpanded(true);
    try {
      const res = await aiApi.subjectRoadmap(subject.slug);
      setRoadmap(res.roadmap);
    } catch {
      setRoadmap("Couldn't load recommendations right now.");
    } finally {
      setLoadingRoadmap(false);
    }
  }

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{subject.label}</CardTitle>
          {hasData ? (
            <Badge variant={weakCount > 0 ? "weak" : "strong"}>
              {Math.round(avgMastery * 100)}% mastery
            </Badge>
          ) : (
            <Badge variant="outline">Not started</Badge>
          )}
        </div>
        <CardDescription>
          {hasData
            ? `${weakCount} weak concept${weakCount === 1 ? "" : "s"} of ${mastery.length} tracked`
            : "Take a quiz to start tracking this subject."}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col gap-3">
        {hasData ? (
          <div className="h-32">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 8 }}>
                <XAxis type="number" domain={[0, 100]} hide />
                <YAxis
                  type="category"
                  dataKey="concept"
                  width={90}
                  tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 11,
                  }}
                />
                <Bar dataKey="mastery" fill="var(--primary)" radius={[0, 4, 4, 0]} barSize={10} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-32 flex items-center justify-center text-xs text-muted-foreground border border-dashed border-border rounded-md">
            No data yet
          </div>
        )}

        <div className="flex gap-2 mt-auto pt-1">
          <Button className="flex-1" asChild>
            <Link href={`/quiz?subject=${subject.slug}`}>Start {subject.label} quiz</Link>
          </Button>
          {hasData && (
            <Button variant="outline" size="icon" onClick={handleGetRecommendations} title="AI recommendations">
              {expanded ? <ChevronUp className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
            </Button>
          )}
        </div>

        {expanded && (
          <div className="rounded-md border border-border bg-secondary/40 p-3 text-xs leading-relaxed whitespace-pre-line">
            {loadingRoadmap ? (
              <Skeleton className="h-12 w-full" />
            ) : (
              roadmap
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
