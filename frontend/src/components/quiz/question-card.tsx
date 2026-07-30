"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { QuestionPublic } from "@/lib/api/types";

const CONFIDENCE_LABELS: Record<number, string> = {
  1: "Guessing",
  2: "Unsure",
  3: "Somewhat sure",
  4: "Confident",
  5: "Certain",
};

export function QuestionCard({
  question,
  index,
  total,
  onSubmit,
}: {
  question: QuestionPublic;
  index: number;
  total: number;
  onSubmit: (answer: {
    selected_option: string;
    confidence: number;
    reasoning_text: string;
    time_taken_seconds: number;
  }) => void;
}) {
  const [selected, setSelected] = React.useState<string | null>(null);
  const [confidence, setConfidence] = React.useState(3);
  const [reasoning, setReasoning] = React.useState("");
  const startedAt = React.useRef(Date.now());

  React.useEffect(() => {
    setSelected(null);
    setConfidence(3);
    setReasoning("");
    startedAt.current = Date.now();
  }, [question.id]);

  function handleSubmit() {
    if (!selected) return;
    onSubmit({
      selected_option: selected,
      confidence,
      reasoning_text: reasoning,
      time_taken_seconds: (Date.now() - startedAt.current) / 1000,
    });
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <Badge variant="secondary">
            Question {index + 1} of {total}
          </Badge>
          <Badge variant="outline">Difficulty {question.difficulty}/5</Badge>
        </div>
        <CardTitle className="text-xl font-normal leading-snug pt-2">
          {question.text}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-2">
          {Object.entries(question.options).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setSelected(key)}
              className={cn(
                "flex items-center gap-3 rounded-md border px-4 py-3 text-left text-sm transition-colors",
                selected === key
                  ? "border-primary bg-secondary"
                  : "border-border hover:bg-secondary/50"
              )}
            >
              <span
                className={cn(
                  "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-xs font-medium",
                  selected === key ? "border-primary bg-primary text-primary-foreground" : "border-border"
                )}
              >
                {key}
              </span>
              {label}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>How confident are you?</Label>
            <span className="text-sm font-medium text-accent-foreground bg-accent/20 px-2 py-0.5 rounded">
              {CONFIDENCE_LABELS[confidence]}
            </span>
          </div>
          <Slider min={1} max={5} step={1} value={[confidence]} onValueChange={([v]) => setConfidence(v)} />
        </div>

        <div className="space-y-2">
          <Label htmlFor="reasoning">Why did you pick this? (optional)</Label>
          <Textarea
            id="reasoning"
            placeholder="Briefly explain your reasoning — this helps pinpoint exactly where a misunderstanding might be."
            value={reasoning}
            onChange={(e) => setReasoning(e.target.value)}
            rows={3}
          />
        </div>

        <Button className="w-full" size="lg" disabled={!selected} onClick={handleSubmit}>
          {index + 1 === total ? "Submit final answer" : "Next question"}
        </Button>
      </CardContent>
    </Card>
  );
}
