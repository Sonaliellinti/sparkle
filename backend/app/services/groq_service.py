"""
Groq integration — the ONLY module that ever calls an LLM.

Hard rule enforced by design: every function here EXPLAINS, NARRATES, or
CHATS about a diagnosis that was already produced deterministically by
app/services/diagnosis_engine.py. None of these functions can change a
score or a mastery level — they only receive already-decided facts and
turn them into natural language.

Mock-first: if GROQ_API_KEY is unset, or the Groq API call fails for any
reason (rate limit, network, bad key), every function here falls back to
a realistic canned response instead of raising — the app must never
crash because of the AI layer.
"""
from app.core.config import settings

_client = None
_client_init_attempted = False


def _get_client():
    global _client, _client_init_attempted
    if _client_init_attempted:
        return _client
    _client_init_attempted = True
    if not settings.GROQ_API_KEY:
        _client = None
        return None
    try:
        from groq import Groq

        _client = Groq(api_key=settings.GROQ_API_KEY)
    except Exception as exc:  # noqa: BLE001
        print(f"[groq_service] Could not initialize Groq client, using mocks ({exc}).")
        _client = None
    return _client


def _chat(system_prompt: str, user_prompt: str, mock_fn) -> str:
    """Shared call/fallback wrapper used by every public function below."""
    client = _get_client()
    if client is None:
        return mock_fn()
    try:
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=600,
        )
        content = completion.choices[0].message.content
        return content.strip() if content else mock_fn()
    except Exception as exc:  # noqa: BLE001 — never let an LLM failure crash a request
        print(f"[groq_service] Groq call failed, falling back to mock ({exc}).")
        return mock_fn()


# ── 1. Mistake explanations ────────────────────────────────────────────────
def explain_mistake(
    question_text: str,
    selected_option: str,
    correct_option: str,
    reference_explanation: str,
    misconceptions: list[str],
) -> str:
    def mock() -> str:
        parts = [
            f"You selected option {selected_option}, but the correct answer is {correct_option}.",
            reference_explanation,
        ]
        if misconceptions:
            parts.append(
                "Your reasoning suggests a common mix-up: "
                + misconceptions[0]
                + ". Reviewing this specific point should clear things up."
            )
        return " ".join(parts)

    system_prompt = (
        "You are a patient technical interview mentor covering DSA, Python, SQL, and "
        "Machine Learning. Explain concisely (3-5 sentences) why the "
        "student's answer was wrong and why the correct option is right, grounded strictly "
        "in the reference explanation provided. If a likely misconception is given, address "
        "it directly and gently. Do not introduce facts beyond the reference explanation."
    )
    user_prompt = (
        f"Question: {question_text}\n"
        f"Student selected: {selected_option}\n"
        f"Correct answer: {correct_option}\n"
        f"Reference explanation: {reference_explanation}\n"
        f"Detected misconceptions (may be empty): {misconceptions}"
    )
    return _chat(system_prompt, user_prompt, mock)


# ── 2. Personalized study roadmap ──────────────────────────────────────────
def generate_roadmap(weak_concepts: list[dict]) -> str:
    """`weak_concepts` is the diagnosis engine's own output (concept name,
    score, root_cause) — Groq only writes the prose around an ordering the
    engine already implies (root causes first)."""

    def mock() -> str:
        if not weak_concepts:
            return (
                "No weak concepts detected yet — take a diagnostic quiz first, "
                "or if you already have, great work: everything is currently at "
                "or above the mastery threshold!"
            )
        lines = ["Here's a suggested study order based on your diagnosis:"]
        for i, c in enumerate(weak_concepts, start=1):
            root_note = (
                f" (root cause: focus on concept id {c['root_cause_concept_id']} first)"
                if c.get("root_cause_concept_id")
                else ""
            )
            lines.append(
                f"{i}. {c['name']} — currently at {round(c['score'] * 100)}% mastery.{root_note} "
                "Review the core formula, then work through 5-10 practice problems."
            )
        return "\n".join(lines)

    system_prompt = (
        "You are Sparkle's interview-prep planning assistant. Given a list of weak concepts "
        "(with scores and, where present, a root-cause concept already identified by a "
        "deterministic diagnosis engine), write a short, encouraging, ordered study plan. "
        "Do NOT re-rank or second-guess which concepts are weak — that has already been "
        "decided. Only add explanatory prose and a sensible day-by-day study sequence."
    )
    user_prompt = f"Weak concepts (already ranked by the diagnosis engine): {weak_concepts}"
    return _chat(system_prompt, user_prompt, mock)


# ── 3. AI tutor (scope-restricted — see app/api/routes/ai.py for the
#      server-side enforcement that runs BEFORE this is ever called) ───────
def tutor_reply(conversation: list[dict], weak_concept_names: list[str]) -> str:
    def mock() -> str:
        if weak_concept_names:
            return (
                f"Let's focus on {weak_concept_names[0]}, one of the areas your diagnosis "
                "flagged as weak. Could you tell me which part of it feels unclear — the "
                "core formula, or applying it in a problem?"
            )
        return "Take a diagnostic quiz first so I know which concepts to help you with."

    system_prompt = (
        "You are Sparkle's AI Interview Mentor, covering DSA, Python, SQL, and Machine "
        "Learning. Ask clarifying/follow-up questions like a real interviewer would, give "
        "hints before full solutions, and explain time/space complexity where relevant. "
        "You may ONLY "
        f"discuss these concepts, which the student's diagnosis has flagged as weak: "
        f"{weak_concept_names}. If the student asks about anything else, gently redirect "
        "them back to these concepts and their study roadmap instead of answering directly. "
        "Be encouraging, concise, and Socratic where possible."
    )
    # conversation is a list of {"role": "user"|"assistant", "content": str}
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in conversation[-10:])
    return _chat(system_prompt, history_text, mock)
