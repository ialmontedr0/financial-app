"""Use case: Get combined AI dashboard."""

from __future__ import annotations

import uuid

import structlog

if __name__ != "__main__":
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetDashboardUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Get combined dashboard with habits, risks, savings, and recommendations."""
        from app.ai.recommendations.habit_analyzer import HabitAnalyzer
        from app.ai.recommendations.risk_assessor import RiskAssessor
        from app.ai.recommendations.savings_optimizer import SavingsOptimizer
        from app.ai.recommendations.engine import RecommendationEngine

        analyzer = HabitAnalyzer()
        assessor = RiskAssessor()
        optimizer = SavingsOptimizer()
        engine = RecommendationEngine()

        habits = await analyzer.analyze(self._session, user_id)
        risks = await assessor.assess(self._session, user_id)
        savings = await optimizer.optimize(self._session, user_id)
        recommendations = await engine.generate(self._session, user_id)

        return {
            "habits": {
                "score": habits.get("overall_habit_score", 0),
                "patterns": habits.get("spending_patterns", {}),
                "stability": habits.get("habit_stability", {}),
                "recommendations_count": len(habits.get("recommendations", [])),
            },
            "risks": {
                "health_score": risks.get("financial_health_score", 0),
                "risk_factors": risks.get("risk_factors", []),
                "metrics": risks.get("metrics", {}),
                "recommendations_count": len(risks.get("recommendations", [])),
            },
            "savings": {
                "allocation": savings.get("allocation_50_30_20", {}),
                "goal_allocation": savings.get("goal_allocation", {}),
                "debt_strategy": savings.get("debt_strategy", {}),
                "estimated_total_savings": savings.get("estimated_total_savings", 0),
                "recommendations_count": len(savings.get("recommendations", [])),
            },
            "recommendations": {
                "total": len(recommendations),
                "high_priority": sum(1 for r in recommendations if r.get("priority") == "high"),
                "estimated_total_savings": round(
                    sum(r.get("estimated_savings", 0) for r in recommendations), 2
                ),
            },
        }
