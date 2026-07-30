"use client";

import * as React from "react";
import { Send, Loader2, Bot, User as UserIcon } from "lucide-react";
import { toast } from "sonner";
import { RequireAuth } from "@/components/layout/require-auth";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { aiApi } from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import type { TutorMessage } from "@/lib/api/types";

export default function TutorPage() {
  return (
    <RequireAuth>
      <AppShell>
        <TutorContent />
      </AppShell>
    </RequireAuth>
  );
}

function TutorContent() {
  const [messages, setMessages] = React.useState<TutorMessage[]>([]);
  const [weakConcepts, setWeakConcepts] = React.useState<string[]>([]);
  const [input, setInput] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const [loadingHistory, setLoadingHistory] = React.useState(true);
  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    aiApi
      .tutorHistory()
      .then(setMessages)
      .finally(() => setLoadingHistory(false));
  }, []);

  React.useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setSending(true);
    try {
      const res = await aiApi.tutorChat(text);
      setWeakConcepts(res.weak_concepts);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "The tutor didn't respond.");
      setMessages((m) => m.slice(0, -1)); // roll back the optimistic user message's pairing
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div>
        <h1 className="font-display text-2xl font-semibold">AI Tutor</h1>
        <p className="text-sm text-muted-foreground">
          Scoped to your current weak concepts — ask about those, and I&apos;ll help.
          Anything else gets redirected back to your roadmap.
        </p>
        {weakConcepts.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {weakConcepts.map((c) => (
              <Badge key={c} variant="weak">
                {c}
              </Badge>
            ))}
          </div>
        )}
      </div>

      <Card className="flex flex-col h-[560px]">
        <ScrollArea className="flex-1 px-4">
          <div className="py-4 space-y-4">
            {loadingHistory && <p className="text-sm text-muted-foreground">Loading conversation…</p>}
            {!loadingHistory && messages.length === 0 && (
              <div className="text-center py-16 text-muted-foreground text-sm">
                <Bot className="h-8 w-8 mx-auto mb-2 text-accent" />
                Ask me anything about the concepts your diagnosis flagged as weak.
              </div>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={cn("flex gap-2.5", m.role === "user" ? "justify-end" : "justify-start")}
              >
                {m.role === "assistant" && (
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/20 text-accent-foreground">
                    <Bot className="h-4 w-4" />
                  </span>
                )}
                <div
                  className={cn(
                    "max-w-[80%] rounded-lg px-3.5 py-2 text-sm whitespace-pre-line",
                    m.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-secondary-foreground"
                  )}
                >
                  {m.content}
                </div>
                {m.role === "user" && (
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10">
                    <UserIcon className="h-4 w-4" />
                  </span>
                )}
              </div>
            ))}
            {sending && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-3.5 w-3.5 animate-spin" /> Thinking…
              </div>
            )}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>
        <CardContent className="border-t border-border pt-4">
          <div className="flex items-end gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about one of your weak concepts…"
              rows={1}
              className="min-h-10 resize-none"
            />
            <Button size="icon" onClick={handleSend} disabled={sending || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
