"use client";

import * as React from "react";
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  Node,
  Edge,
  Position,
  useEdgesState,
  useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";
import { RequireAuth } from "@/components/layout/require-auth";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { conceptsApi, dashboardApi } from "@/lib/api";
import type { Concept, ConceptGraph, ConceptMastery, QuestionPublic } from "@/lib/api/types";

const LEVEL_COLORS: Record<string, { border: string; bg: string; label: string }> = {
  strong: { border: "var(--mastery-strong)", bg: "var(--mastery-strong-bg)", label: "Mastered" },
  moderate: { border: "var(--mastery-moderate)", bg: "var(--mastery-moderate-bg)", label: "Needs revision" },
  weak: { border: "var(--mastery-weak)", bg: "var(--mastery-weak-bg)", label: "Weak" },
};

export default function GraphPage() {
  return (
    <RequireAuth>
      <AppShell>
        <GraphContent />
      </AppShell>
    </RequireAuth>
  );
}

function GraphContent() {
  const [graph, setGraph] = React.useState<ConceptGraph | null>(null);
  const [mastery, setMastery] = React.useState<ConceptMastery[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [selected, setSelected] = React.useState<Concept | null>(null);
  const [prereqs, setPrereqs] = React.useState<Concept[]>([]);
  const [questions, setQuestions] = React.useState<QuestionPublic[]>([]);
  const [panelLoading, setPanelLoading] = React.useState(false);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  React.useEffect(() => {
    Promise.all([conceptsApi.graph(), dashboardApi.mastery()])
      .then(([g, m]) => {
        setGraph(g);
        setMastery(m);
      })
      .finally(() => setLoading(false));
  }, []);

  React.useEffect(() => {
    if (!graph) return;
    const masteryByConcept = new Map(mastery.map((m) => [m.concept_id, m]));

    // Simple layered layout by difficulty_level so prerequisites visually
    // sit to the left of what depends on them.
    const byLevel: Record<number, Concept[]> = {};
    for (const c of graph.nodes) {
      (byLevel[c.difficulty_level] ??= []).push(c);
    }
    const levels = Object.keys(byLevel).map(Number).sort((a, b) => a - b);

    const newNodes: Node[] = [];
    levels.forEach((level, colIdx) => {
      byLevel[level].forEach((concept, rowIdx) => {
        const m = masteryByConcept.get(concept.id);
        const level_ = m?.level ?? "moderate";
        const colors = LEVEL_COLORS[level_];
        newNodes.push({
          id: String(concept.id),
          position: { x: colIdx * 240, y: rowIdx * 130 },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
          data: { label: concept.name, concept },
          style: {
            border: `2px solid ${colors.border}`,
            background: colors.bg,
            borderRadius: 10,
            padding: 10,
            fontSize: 12,
            fontWeight: 500,
            width: 190,
            borderStyle: m?.is_propagated ? "dashed" : "solid",
            transition: "all 0.4s ease",
          },
        });
      });
    });

    const newEdges: Edge[] = graph.edges.map((e) => ({
      id: `e${e.id}`,
      source: String(e.prerequisite_id),
      target: String(e.dependent_id),
      animated: false,
      style: { stroke: "var(--border)", strokeWidth: Math.max(1, e.weight * 2) },
      markerEnd: { type: MarkerType.ArrowClosed, color: "var(--border)" },
    }));

    setNodes(newNodes);
    setEdges(newEdges);
  }, [graph, mastery, setNodes, setEdges]);

  async function handleNodeClick(_: React.MouseEvent, node: Node) {
    const concept = node.data.concept as Concept;
    setSelected(concept);
    setPanelLoading(true);
    try {
      const [p, q] = await Promise.all([
        conceptsApi.prerequisites(concept.id),
        conceptsApi.questions(concept.id),
      ]);
      setPrereqs(p);
      setQuestions(q);
    } finally {
      setPanelLoading(false);
    }
  }

  if (loading) {
    return <Skeleton className="h-[560px] w-full" />;
  }

  const masteryByConcept = new Map(mastery.map((m) => [m.concept_id, m]));
  const selectedMastery = selected ? masteryByConcept.get(selected.id) : undefined;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold">Concept graph</h1>
          <p className="text-sm text-muted-foreground">
            Click a node to see its mastery, prerequisites, and linked questions.
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          {Object.entries(LEVEL_COLORS).map(([key, c]) => (
            <span key={key} className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: c.border }} />
              {c.label}
            </span>
          ))}
          <span className="flex items-center gap-1.5 text-muted-foreground">
            <span className="h-2.5 w-2.5 rounded-full border border-dashed border-foreground" />
            Inferred
          </span>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <Card className="h-[560px] overflow-hidden p-0">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={handleNodeClick}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background color="var(--border)" gap={20} />
            <Controls showInteractive={false} />
          </ReactFlow>
        </Card>

        <Card className="h-[560px] overflow-y-auto">
          <CardHeader>
            <CardTitle className="text-base">
              {selected ? selected.name : "Select a concept"}
            </CardTitle>
            {selected && <CardDescription>{selected.description}</CardDescription>}
          </CardHeader>
          <CardContent className="space-y-4">
            {!selected && (
              <p className="text-sm text-muted-foreground">
                Click any node in the graph to inspect it here.
              </p>
            )}
            {selected && (
              <>
                {selectedMastery ? (
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={
                        selectedMastery.level === "strong"
                          ? "strong"
                          : selectedMastery.level === "moderate"
                          ? "moderate"
                          : "weak"
                      }
                    >
                      {Math.round(selectedMastery.score * 100)}% mastery
                    </Badge>
                    {selectedMastery.is_propagated && (
                      <Badge variant="outline">inferred, not directly tested</Badge>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">Not yet assessed.</p>
                )}

                <div>
                  <h4 className="text-sm font-medium mb-1.5">Prerequisites</h4>
                  {panelLoading ? (
                    <Skeleton className="h-4 w-32" />
                  ) : prereqs.length ? (
                    <ul className="text-sm text-muted-foreground space-y-1">
                      {prereqs.map((p) => (
                        <li key={p.id}>• {p.name}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">None — this is a foundational concept.</p>
                  )}
                </div>

                <div>
                  <h4 className="text-sm font-medium mb-1.5">Linked questions ({questions.length})</h4>
                  {panelLoading ? (
                    <Skeleton className="h-4 w-40" />
                  ) : (
                    <ul className="text-sm text-muted-foreground space-y-1 max-h-40 overflow-y-auto">
                      {questions.map((q) => (
                        <li key={q.id} className="line-clamp-1">• {q.text}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
