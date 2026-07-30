"""
Concept dependency graph models.

`Concept` = one node in the Sparkle skill graph (DSA / Python / SQL / ML)
(e.g. "Ohm's Law", "Kirchhoff's Voltage Law").

`ConceptDependency` = one directed edge, meaning:
    prerequisite_concept  --->  dependent_concept
i.e. a student should master `prerequisite_concept` before
`dependent_concept`. This edge list is what gets loaded into a
NetworkX DiGraph in Phase 2 for weakness propagation — no graph
algorithms live in this file, it is pure schema.
"""
from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Which subject this concept belongs to: "dsa" | "python" | "sql" | "ml".
    # Lets one shared concept graph / question bank span multiple subjects
    # instead of one graph per subject.
    subject: Mapped[str] = mapped_column(String(32), default="dsa", nullable=False, index=True)

    # 1 = foundational, higher = more advanced. Purely descriptive metadata;
    # actual difficulty-weighted logic is added in the diagnosis engine phase.
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1)

    # ── Relationships ───────────────────────────────────────────────────
    questions: Mapped[list["Question"]] = relationship(back_populates="concept")

    outgoing_edges: Mapped[list["ConceptDependency"]] = relationship(
        foreign_keys="ConceptDependency.prerequisite_id",
        back_populates="prerequisite",
        cascade="all, delete-orphan",
    )
    incoming_edges: Mapped[list["ConceptDependency"]] = relationship(
        foreign_keys="ConceptDependency.dependent_id",
        back_populates="dependent",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Concept slug={self.slug!r}>"


class ConceptDependency(Base):
    """A directed edge: prerequisite_id -> dependent_id."""

    __tablename__ = "concept_dependencies"
    __table_args__ = (
        UniqueConstraint("prerequisite_id", "dependent_id", name="uq_concept_edge"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    prerequisite_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    dependent_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), nullable=False)

    # Edge weight in [0, 1]: how strongly weakness in the prerequisite
    # propagates forward to the dependent concept. Used by the NetworkX
    # propagation algorithm built in Phase 2 — not evaluated here.
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    prerequisite: Mapped["Concept"] = relationship(
        foreign_keys=[prerequisite_id], back_populates="outgoing_edges"
    )
    dependent: Mapped["Concept"] = relationship(
        foreign_keys=[dependent_id], back_populates="incoming_edges"
    )

    def __repr__(self) -> str:
        return f"<ConceptDependency {self.prerequisite_id} -> {self.dependent_id}>"
