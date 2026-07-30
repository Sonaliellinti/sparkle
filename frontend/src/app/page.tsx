import Link from "next/link";
import { Sparkles, ArrowRight, Target, Share2, MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2 font-display font-semibold text-lg">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-accent text-accent-foreground">
            <Sparkles className="h-4 w-4" fill="currentColor" />
          </span>
          Sparkle
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" asChild>
            <Link href="/login">Log in</Link>
          </Button>
          <Button asChild>
            <Link href="/register">Get started</Link>
          </Button>
        </div>
      </header>

      <section className="mx-auto max-w-4xl px-6 pt-16 pb-10 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground mb-6">
          <Sparkles className="h-3 w-3 text-accent" fill="currentColor" /> DSA · Python · SQL · Machine Learning
        </div>
        <h1 className="font-display text-4xl sm:text-5xl font-semibold tracking-tight text-balance">
          Sparkle
        </h1>
        <p className="mt-3 text-xl text-primary font-medium">
          AI-powered interview readiness platform
        </p>
        <p className="mt-5 text-lg text-muted-foreground max-w-2xl mx-auto text-balance">
          Diagnose skills. Practice smarter. Get interview ready. A deterministic
          engine grades every attempt, traces weaknesses through a skill
          dependency graph, and hands you a personalized roadmap — with an AI
          mentor that only talks about what you actually need to fix.
        </p>
        <div className="mt-8 flex items-center justify-center gap-3">
          <Button size="lg" asChild>
            <Link href="/register">
              Start practicing <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/login">I already have an account</Link>
          </Button>
        </div>
      </section>

      <div className="circuit-divider max-w-4xl mx-auto" />

      <section className="mx-auto max-w-5xl px-6 pb-24 grid gap-6 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <Target className="h-5 w-5 text-accent mb-2" />
            <CardTitle>Deterministic diagnosis</CardTitle>
            <CardDescription>
              Grading and mastery scoring are plain, reproducible math across
              DSA, Python, SQL, and ML — not an LLM guessing at your level.
            </CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <Share2 className="h-5 w-5 text-accent mb-2" />
            <CardTitle>Skill graph propagation</CardTitle>
            <CardDescription>
              A NetworkX dependency graph traces weakness upstream and
              downstream, even to concepts you never answered a question on.
            </CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <MessageCircle className="h-5 w-5 text-accent mb-2" />
            <CardTitle>Scope-restricted AI mentor</CardTitle>
            <CardDescription>
              Groq-powered explanations and mentoring — but only ever about
              the concepts your diagnosis actually flagged.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    </div>
  );
}
