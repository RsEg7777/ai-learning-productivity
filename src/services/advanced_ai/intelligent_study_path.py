"""Intelligent Study Path Generator with ML-powered personalization."""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import math

from ...shared.aws_clients.bedrock_client import BedrockClient
from ...shared.aws_clients.dynamodb_client import DynamoDBClient
from ...shared.utils.logger import get_logger
from ...shared.utils.errors import ServiceError

logger = get_logger(__name__)


@dataclass
class SkillGap:
    """Represents a skill gap."""
    skill: str
    current_level: float  # 0-100
    target_level: float
    gap_size: float
    priority: str  # high, medium, low
    estimated_hours: int


@dataclass
class Milestone:
    """Represents a learning milestone."""
    milestone_id: str
    title: str
    description: str
    skills: List[str]
    estimated_hours: int
    week_number: int
    resources: List[Dict[str, str]]
    assessments: List[str]


@dataclass
class StudyPath:
    """Represents a complete study path."""
    path_id: str
    user_id: str
    goal: str
    current_level: str
    target_level: str
    duration_weeks: int
    total_hours: int
    milestones: List[Milestone]
    skill_gaps: List[SkillGap]
    created_at: str
    progress: float


class IntelligentStudyPathGenerator:
    """
    AI-powered study path generator with adaptive learning.
    
    Features:
    - Skill gap analysis with ML
    - Prerequisite detection
    - Personalized learning paths
    - Adaptive difficulty adjustment
    - Progress predictions
    - Resource recommendations
    """

    def __init__(
        self,
        bedrock_client: Optional[BedrockClient] = None,
        dynamodb_client: Optional[DynamoDBClient] = None,
    ):
        """Initialize study path generator."""
        self.bedrock_client = bedrock_client or BedrockClient()
        self.dynamodb_client = dynamodb_client or DynamoDBClient()
        self.table_name = "study_paths"
        logger.info("IntelligentStudyPathGenerator initialized")

    def generate_study_path(
        self,
        user_id: str,
        goal: str,
        current_level: str,
        target_level: str,
        duration_weeks: int,
        learning_style: str = "balanced",
        time_per_week: int = 10,
    ) -> StudyPath:
        """
        Generate personalized study path.
        
        Args:
            user_id: User identifier
            goal: Learning goal (e.g., "Master Python", "Learn AWS")
            current_level: Current skill level (beginner, intermediate, advanced)
            target_level: Target skill level
            duration_weeks: Duration in weeks
            learning_style: Learning style (visual, auditory, kinesthetic, balanced)
            time_per_week: Available hours per week
            
        Returns:
            StudyPath object
        """
        try:
            logger.info(f"Generating study path for {user_id}: {goal}")
            
            # Analyze skill gaps
            skill_gaps = self._analyze_skill_gaps(
                user_id, goal, current_level, target_level
            )
            
            # Detect prerequisites
            prerequisites = self._detect_prerequisites(goal, current_level)
            
            # Generate milestones
            milestones = self._generate_milestones(
                goal=goal,
                skill_gaps=skill_gaps,
                prerequisites=prerequisites,
                duration_weeks=duration_weeks,
                time_per_week=time_per_week,
                learning_style=learning_style,
            )
            
            # Calculate total hours
            total_hours = sum(m.estimated_hours for m in milestones)
            
            # Create study path
            path_id = f"path_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            study_path = StudyPath(
                path_id=path_id,
                user_id=user_id,
                goal=goal,
                current_level=current_level,
                target_level=target_level,
                duration_weeks=duration_weeks,
                total_hours=total_hours,
                milestones=milestones,
                skill_gaps=skill_gaps,
                created_at=datetime.now().isoformat(),
                progress=0.0,
            )
            
            # Save to DynamoDB
            self._save_study_path(study_path)
            
            logger.info(f"Generated study path: {path_id}")
            return study_path
            
        except Exception as e:
            logger.error(f"Error generating study path: {e}", exc_info=True)
            raise ServiceError(f"Failed to generate study path: {str(e)}")

    def adapt_difficulty(
        self,
        path_id: str,
        performance_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Adapt difficulty based on performance.
        
        Args:
            path_id: Study path identifier
            performance_data: Recent performance metrics
            
        Returns:
            Dictionary with adaptation recommendations
        """
        try:
            # Load study path
            study_path = self._load_study_path(path_id)
            
            # Analyze performance
            avg_score = performance_data.get("average_score", 0)
            completion_rate = performance_data.get("completion_rate", 0)
            time_spent = performance_data.get("time_spent_hours", 0)
            
            # Determine adaptation
            if avg_score >= 90 and completion_rate >= 80:
                recommendation = "increase_difficulty"
                adjustment = 1.2
                message = "You're excelling! Let's challenge you more."
            elif avg_score >= 70 and completion_rate >= 60:
                recommendation = "maintain"
                adjustment = 1.0
                message = "Great progress! Keep going at this pace."
            elif avg_score >= 50:
                recommendation = "add_practice"
                adjustment = 1.0
                message = "Let's add more practice exercises."
            else:
                recommendation = "decrease_difficulty"
                adjustment = 0.8
                message = "Let's slow down and reinforce fundamentals."
            
            # Generate adapted milestones
            adapted_milestones = self._adapt_milestones(
                study_path.milestones,
                adjustment,
                recommendation
            )
            
            return {
                "path_id": path_id,
                "recommendation": recommendation,
                "adjustment_factor": adjustment,
                "message": message,
                "adapted_milestones": [
                    {
                        "milestone_id": m.milestone_id,
                        "title": m.title,
                        "estimated_hours": m.estimated_hours,
                    }
                    for m in adapted_milestones
                ],
                "performance_analysis": {
                    "average_score": avg_score,
                    "completion_rate": completion_rate,
                    "time_efficiency": self._calculate_time_efficiency(
                        time_spent, study_path.total_hours
                    ),
                },
            }
            
        except Exception as e:
            logger.error(f"Error adapting difficulty: {e}", exc_info=True)
            raise ServiceError(f"Failed to adapt difficulty: {str(e)}")

    def predict_completion_time(
        self,
        path_id: str,
        current_progress: float,
        time_spent_hours: int,
    ) -> Dict[str, Any]:
        """
        Predict when user will complete the study path.
        
        Args:
            path_id: Study path identifier
            current_progress: Current progress (0-100)
            time_spent_hours: Hours spent so far
            
        Returns:
            Dictionary with predictions
        """
        try:
            study_path = self._load_study_path(path_id)
            
            # Calculate velocity
            if current_progress > 0:
                hours_per_percent = time_spent_hours / current_progress
                remaining_progress = 100 - current_progress
                estimated_hours_remaining = hours_per_percent * remaining_progress
            else:
                estimated_hours_remaining = study_path.total_hours
            
            # Predict completion date
            weeks_remaining = math.ceil(estimated_hours_remaining / 10)  # Assuming 10 hrs/week
            completion_date = datetime.now() + timedelta(weeks=weeks_remaining)
            
            # Calculate confidence
            confidence = min(100, current_progress * 1.5)  # Higher progress = higher confidence
            
            return {
                "path_id": path_id,
                "current_progress": current_progress,
                "estimated_hours_remaining": int(estimated_hours_remaining),
                "estimated_weeks_remaining": weeks_remaining,
                "predicted_completion_date": completion_date.isoformat(),
                "confidence_level": confidence,
                "on_track": weeks_remaining <= study_path.duration_weeks,
                "velocity": {
                    "hours_per_week": time_spent_hours / max(1, (datetime.now() - datetime.fromisoformat(study_path.created_at)).days / 7),
                    "progress_per_week": current_progress / max(1, (datetime.now() - datetime.fromisoformat(study_path.created_at)).days / 7),
                },
            }
            
        except Exception as e:
            logger.error(f"Error predicting completion: {e}", exc_info=True)
            raise ServiceError(f"Failed to predict completion: {str(e)}")

    def _analyze_skill_gaps(
        self,
        user_id: str,
        goal: str,
        current_level: str,
        target_level: str,
    ) -> List[SkillGap]:
        """Analyze skill gaps using AI."""
        prompt = f"""Analyze skill gaps for a learner.

Goal: {goal}
Current Level: {current_level}
Target Level: {target_level}

Identify 5-8 key skill gaps and provide analysis in JSON format:
{{
    "skill_gaps": [
        {{
            "skill": "Skill name",
            "current_level": 0-100,
            "target_level": 0-100,
            "gap_size": 0-100,
            "priority": "high|medium|low",
            "estimated_hours": hours_to_bridge_gap
        }}
    ]
}}"""

        response = self.bedrock_client.invoke_model(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.5,
        )
        
        try:
            data = json.loads(response)
            return [
                SkillGap(
                    skill=gap["skill"],
                    current_level=gap["current_level"],
                    target_level=gap["target_level"],
                    gap_size=gap["gap_size"],
                    priority=gap["priority"],
                    estimated_hours=gap["estimated_hours"],
                )
                for gap in data.get("skill_gaps", [])
            ]
        except json.JSONDecodeError:
            return []

    def _detect_prerequisites(
        self,
        goal: str,
        current_level: str,
    ) -> List[str]:
        """Detect prerequisites using AI."""
        prompt = f"""Identify prerequisites for learning goal.

Goal: {goal}
Current Level: {current_level}

List prerequisites in JSON format:
{{
    "prerequisites": ["prerequisite1", "prerequisite2", ...]
}}"""

        response = self.bedrock_client.invoke_model(
            prompt=prompt,
            max_tokens=500,
            temperature=0.3,
        )
        
        try:
            data = json.loads(response)
            return data.get("prerequisites", [])
        except json.JSONDecodeError:
            return []

    def _generate_milestones(
        self,
        goal: str,
        skill_gaps: List[SkillGap],
        prerequisites: List[str],
        duration_weeks: int,
        time_per_week: int,
        learning_style: str,
    ) -> List[Milestone]:
        """Generate learning milestones using AI."""
        skill_gaps_text = "\n".join([
            f"- {gap.skill}: {gap.gap_size}% gap, {gap.estimated_hours}h, priority: {gap.priority}"
            for gap in skill_gaps
        ])
        
        prompt = f"""Create a detailed learning path with milestones.

Goal: {goal}
Duration: {duration_weeks} weeks
Time Available: {time_per_week} hours/week
Learning Style: {learning_style}

Skill Gaps:
{skill_gaps_text}

Prerequisites: {', '.join(prerequisites)}

Create {duration_weeks} weekly milestones in JSON format:
{{
    "milestones": [
        {{
            "title": "Week 1: Title",
            "description": "What to learn",
            "skills": ["skill1", "skill2"],
            "estimated_hours": hours,
            "resources": [
                {{"type": "video", "title": "Resource title", "url": "url"}},
                {{"type": "article", "title": "Article title", "url": "url"}},
                {{"type": "practice", "title": "Exercise", "url": "url"}}
            ],
            "assessments": ["Quiz 1", "Project 1"]
        }}
    ]
}}"""

        response = self.bedrock_client.invoke_model(
            prompt=prompt,
            max_tokens=3000,
            temperature=0.7,
        )
        
        try:
            data = json.loads(response)
            milestones = []
            for i, m in enumerate(data.get("milestones", []), 1):
                milestone = Milestone(
                    milestone_id=f"milestone_{i}",
                    title=m["title"],
                    description=m["description"],
                    skills=m["skills"],
                    estimated_hours=m["estimated_hours"],
                    week_number=i,
                    resources=m.get("resources", []),
                    assessments=m.get("assessments", []),
                )
                milestones.append(milestone)
            return milestones
        except json.JSONDecodeError:
            return []

    def _adapt_milestones(
        self,
        milestones: List[Milestone],
        adjustment: float,
        recommendation: str,
    ) -> List[Milestone]:
        """Adapt milestones based on performance."""
        adapted = []
        for m in milestones:
            adapted_milestone = Milestone(
                milestone_id=m.milestone_id,
                title=m.title,
                description=m.description,
                skills=m.skills,
                estimated_hours=int(m.estimated_hours * adjustment),
                week_number=m.week_number,
                resources=m.resources,
                assessments=m.assessments,
            )
            adapted.append(adapted_milestone)
        return adapted

    def _calculate_time_efficiency(
        self,
        time_spent: int,
        total_hours: int,
    ) -> float:
        """Calculate time efficiency."""
        if total_hours == 0:
            return 0.0
        return min(100, (total_hours / max(1, time_spent)) * 100)

    def _save_study_path(self, study_path: StudyPath) -> None:
        """Save study path to DynamoDB."""
        try:
            item = {
                "path_id": study_path.path_id,
                "user_id": study_path.user_id,
                "goal": study_path.goal,
                "current_level": study_path.current_level,
                "target_level": study_path.target_level,
                "duration_weeks": study_path.duration_weeks,
                "total_hours": study_path.total_hours,
                "milestones": [asdict(m) for m in study_path.milestones],
                "skill_gaps": [asdict(g) for g in study_path.skill_gaps],
                "created_at": study_path.created_at,
                "progress": study_path.progress,
            }
            self.dynamodb_client.put_item(self.table_name, item)
        except Exception as e:
            logger.warning(f"Failed to save study path: {e}")

    def _load_study_path(self, path_id: str) -> StudyPath:
        """Load study path from DynamoDB."""
        try:
            item = self.dynamodb_client.get_item(
                self.table_name,
                {"path_id": path_id}
            )
            
            if not item:
                raise ServiceError(f"Study path not found: {path_id}")
            
            milestones = [Milestone(**m) for m in item.get("milestones", [])]
            skill_gaps = [SkillGap(**g) for g in item.get("skill_gaps", [])]
            
            return StudyPath(
                path_id=item["path_id"],
                user_id=item["user_id"],
                goal=item["goal"],
                current_level=item["current_level"],
                target_level=item["target_level"],
                duration_weeks=item["duration_weeks"],
                total_hours=item["total_hours"],
                milestones=milestones,
                skill_gaps=skill_gaps,
                created_at=item["created_at"],
                progress=item.get("progress", 0.0),
            )
        except Exception as e:
            logger.error(f"Failed to load study path: {e}", exc_info=True)
            raise ServiceError(f"Failed to load study path: {str(e)}")
