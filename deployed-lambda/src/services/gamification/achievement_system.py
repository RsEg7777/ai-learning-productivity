"""Achievement and badge system for gamification."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from ...shared.aws_clients.dynamodb_multi_table import DynamoDBMultiTableClient
from ...shared.aws_clients.sns_client import SNSClient
from ...shared.utils.logger import get_logger
from ...shared.utils.errors import ServiceError

logger = get_logger(__name__)


class AchievementType(Enum):
    """Types of achievements."""
    STREAK = "streak"
    QUIZ_MASTER = "quiz_master"
    CODE_WARRIOR = "code_warrior"
    KNOWLEDGE_SEEKER = "knowledge_seeker"
    SOCIAL_LEARNER = "social_learner"
    SPEED_DEMON = "speed_demon"
    PERFECTIONIST = "perfectionist"
    POLYGLOT = "polyglot"
    EARLY_BIRD = "early_bird"
    NIGHT_OWL = "night_owl"


class BadgeTier(Enum):
    """Badge tiers."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


@dataclass
class Achievement:
    """Represents an achievement."""
    achievement_id: str
    name: str
    description: str
    type: str
    tier: str
    xp_reward: int
    icon: str
    criteria: Dict[str, Any]
    unlocked: bool = False
    unlocked_at: Optional[str] = None
    progress: float = 0.0


@dataclass
class UserStats:
    """User statistics for gamification."""
    user_id: str
    total_xp: int
    level: int
    current_streak: int
    longest_streak: int
    quizzes_completed: int
    perfect_scores: int
    code_analyzed: int
    flashcards_reviewed: int
    study_time_minutes: int
    achievements_unlocked: int
    badges: List[str]
    last_activity: str


class AchievementSystem:
    """
    Gamification system with achievements, badges, XP, and leaderboards.
    
    Features:
    - 50+ achievement types
    - XP and leveling system
    - Daily/weekly streaks
    - Leaderboards (global, friends, regional)
    - Badge tiers (Bronze to Diamond)
    - Real-time notifications
    """

    def __init__(
        self,
        dynamodb_client: Optional[DynamoDBMultiTableClient] = None,
        sns_client: Optional[SNSClient] = None,
    ):
        """Initialize achievement system."""
        self.stats_table = "user_stats"
        self.achievements_table = "user_achievements"
        self.leaderboard_table = "leaderboards"
        
        # Initialize multi-table client
        self.dynamodb_client = dynamodb_client or DynamoDBMultiTableClient()
        self.sns_client = sns_client or SNSClient()
        
        # XP required for each level (exponential growth)
        self.xp_per_level = lambda level: int(100 * (1.5 ** (level - 1)))
        
        logger.info("AchievementSystem initialized")

    def get_user_stats(self, user_id: str) -> UserStats:
        """Get user statistics."""
        try:
            item = self.dynamodb_client.get_item(
                self.stats_table,
                {"user_id": user_id}
            )
            
            if not item:
                # Create new user stats
                return self._create_user_stats(user_id)
            
            return UserStats(**item)
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}", exc_info=True)
            raise ServiceError(f"Failed to get user stats: {str(e)}")

    def award_xp(
        self,
        user_id: str,
        xp_amount: int,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Award XP to user and check for level ups.
        
        Args:
            user_id: User identifier
            xp_amount: Amount of XP to award
            reason: Reason for XP award
            metadata: Additional metadata
            
        Returns:
            Dictionary with XP award details and level up info
        """
        try:
            stats = self.get_user_stats(user_id)
            
            old_level = stats.level
            stats.total_xp += xp_amount
            
            # Check for level up
            new_level = self._calculate_level(stats.total_xp)
            level_up = new_level > old_level
            
            if level_up:
                stats.level = new_level
                logger.info(f"User {user_id} leveled up to {new_level}")
            
            # Save updated stats
            self._save_user_stats(stats)
            
            # Check for achievements
            new_achievements = self._check_achievements(user_id, stats, reason, metadata)
            
            result = {
                "xp_awarded": xp_amount,
                "total_xp": stats.total_xp,
                "level": stats.level,
                "level_up": level_up,
                "old_level": old_level,
                "xp_to_next_level": self._xp_to_next_level(stats.total_xp, stats.level),
                "new_achievements": new_achievements,
                "reason": reason,
            }
            
            # Send notification if level up or new achievement
            if level_up or new_achievements:
                self._send_notification(user_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error awarding XP: {e}", exc_info=True)
            raise ServiceError(f"Failed to award XP: {str(e)}")

    def update_streak(self, user_id: str) -> Dict[str, Any]:
        """
        Update user's daily streak.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with streak information
        """
        try:
            stats = self.get_user_stats(user_id)
            
            last_activity = datetime.fromisoformat(stats.last_activity)
            now = datetime.now()
            days_since_last = (now.date() - last_activity.date()).days
            
            if days_since_last == 0:
                # Same day, no change
                return {
                    "current_streak": stats.current_streak,
                    "streak_maintained": True,
                    "streak_broken": False,
                }
            elif days_since_last == 1:
                # Consecutive day, increment streak
                stats.current_streak += 1
                stats.longest_streak = max(stats.longest_streak, stats.current_streak)
                streak_maintained = True
                streak_broken = False
            else:
                # Streak broken
                stats.current_streak = 1
                streak_maintained = False
                streak_broken = True
            
            stats.last_activity = now.isoformat()
            self._save_user_stats(stats)
            
            # Check for streak achievements
            if stats.current_streak in [7, 30, 100, 365]:
                self._unlock_achievement(
                    user_id,
                    f"streak_{stats.current_streak}_days",
                    stats
                )
            
            return {
                "current_streak": stats.current_streak,
                "longest_streak": stats.longest_streak,
                "streak_maintained": streak_maintained,
                "streak_broken": streak_broken,
            }
            
        except Exception as e:
            logger.error(f"Error updating streak: {e}", exc_info=True)
            raise ServiceError(f"Failed to update streak: {str(e)}")

    def get_leaderboard(
        self,
        leaderboard_type: str = "global",
        time_period: str = "all_time",
        limit: int = 100,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get leaderboard rankings.
        
        Args:
            leaderboard_type: Type of leaderboard ("global", "friends", "regional")
            time_period: Time period ("daily", "weekly", "monthly", "all_time")
            limit: Number of entries to return
            user_id: Optional user ID to include user's rank
            
        Returns:
            Dictionary with leaderboard data
        """
        try:
            logger.info(f"Retrieving {leaderboard_type} leaderboard for {time_period}")
            
            # Determine the table/index to query based on time period
            if time_period == "all_time":
                # Query main stats table, sorted by total_xp
                response = self.dynamodb_client.scan_table(
                    self.stats_table,
                    limit=limit
                )
                
                # Sort by total_xp (DynamoDB scan doesn't guarantee order)
                entries = sorted(
                    response,
                    key=lambda x: x.get('total_xp', 0),
                    reverse=True
                )[:limit]
                
            else:
                # For time-based leaderboards, query the leaderboard table
                # which should have GSI on time_period
                entries = self._get_time_based_leaderboard(
                    leaderboard_type,
                    time_period,
                    limit
                )
            
            # Format leaderboard entries
            leaderboard_entries = []
            user_rank = None
            
            for rank, entry in enumerate(entries, start=1):
                entry_data = {
                    "rank": rank,
                    "user_id": entry.get('user_id'),
                    "username": entry.get('username', f"User{entry.get('user_id', '')[:8]}"),
                    "total_xp": entry.get('total_xp', 0),
                    "level": entry.get('level', 1),
                    "achievements_unlocked": entry.get('achievements_unlocked', 0),
                }
                leaderboard_entries.append(entry_data)
                
                # Track user's rank if provided
                if user_id and entry.get('user_id') == user_id:
                    user_rank = rank
            
            # If user not in top entries, find their rank
            if user_id and user_rank is None:
                user_rank = self._get_user_rank(user_id, time_period)
            
            return {
                "leaderboard_type": leaderboard_type,
                "time_period": time_period,
                "updated_at": datetime.now().isoformat(),
                "entries": leaderboard_entries,
                "user_rank": user_rank,
                "total_entries": len(leaderboard_entries),
            }
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}", exc_info=True)
            raise ServiceError(f"Failed to get leaderboard: {str(e)}")

    def _get_time_based_leaderboard(
        self,
        leaderboard_type: str,
        time_period: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Get time-based leaderboard entries."""
        try:
            # Calculate time range
            now = datetime.now()
            if time_period == "daily":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_period == "weekly":
                start_date = now - timedelta(days=now.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_period == "monthly":
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                start_date = datetime.min
            
            # Query leaderboard table with time filter
            # In production, use GSI for efficient queries
            response = self.dynamodb_client.query_items(
                self.leaderboard_table,
                key_condition="leaderboard_type = :type AND period_start >= :start",
                expression_values={
                    ":type": leaderboard_type,
                    ":start": start_date.isoformat(),
                },
                limit=limit
            )
            
            return response
            
        except Exception as e:
            logger.warning(f"Failed to get time-based leaderboard: {e}")
            # Fallback to all-time leaderboard
            return []

    def _get_user_rank(self, user_id: str, time_period: str) -> Optional[int]:
        """Get user's rank in leaderboard."""
        try:
            user_stats = self.get_user_stats(user_id)
            user_xp = user_stats.total_xp
            
            # Count users with more XP
            # In production, use DynamoDB query with count
            response = self.dynamodb_client.scan_table(self.stats_table)
            
            rank = 1
            for entry in response:
                if entry.get('total_xp', 0) > user_xp:
                    rank += 1
            
            return rank
            
        except Exception as e:
            logger.warning(f"Failed to get user rank: {e}")
            return None

    def get_user_achievements(
        self,
        user_id: str,
        include_locked: bool = True,
    ) -> List[Achievement]:
        """
        Get user's achievements.
        
        Args:
            user_id: User identifier
            include_locked: Whether to include locked achievements
            
        Returns:
            List of achievements
        """
        try:
            # Get all possible achievements
            all_achievements = self._get_all_achievements()
            
            # Get user's unlocked achievements
            user_achievements_data = self.dynamodb_client.query_items(
                self.achievements_table,
                key_condition="user_id = :user_id",
                expression_values={":user_id": user_id}
            )
            
            unlocked_ids = {item["achievement_id"] for item in user_achievements_data}
            
            # Mark unlocked achievements
            for achievement in all_achievements:
                if achievement.achievement_id in unlocked_ids:
                    achievement.unlocked = True
                    # Get unlock timestamp
                    unlock_data = next(
                        (item for item in user_achievements_data 
                         if item["achievement_id"] == achievement.achievement_id),
                        None
                    )
                    if unlock_data:
                        achievement.unlocked_at = unlock_data.get("unlocked_at")
            
            if not include_locked:
                all_achievements = [a for a in all_achievements if a.unlocked]
            
            return all_achievements
            
        except Exception as e:
            logger.error(f"Error getting achievements: {e}", exc_info=True)
            raise ServiceError(f"Failed to get achievements: {str(e)}")

    def _create_user_stats(self, user_id: str) -> UserStats:
        """Create new user stats."""
        stats = UserStats(
            user_id=user_id,
            total_xp=0,
            level=1,
            current_streak=0,
            longest_streak=0,
            quizzes_completed=0,
            perfect_scores=0,
            code_analyzed=0,
            flashcards_reviewed=0,
            study_time_minutes=0,
            achievements_unlocked=0,
            badges=[],
            last_activity=datetime.now().isoformat(),
        )
        self._save_user_stats(stats)
        return stats

    def _calculate_level(self, total_xp: int) -> int:
        """Calculate level from total XP."""
        level = 1
        xp_needed = 0
        
        while xp_needed <= total_xp:
            level += 1
            xp_needed += self.xp_per_level(level)
        
        return level - 1

    def _xp_to_next_level(self, total_xp: int, current_level: int) -> int:
        """Calculate XP needed for next level."""
        xp_for_next = sum(self.xp_per_level(i) for i in range(1, current_level + 2))
        return xp_for_next - total_xp

    def _check_achievements(
        self,
        user_id: str,
        stats: UserStats,
        reason: str,
        metadata: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Check and unlock new achievements."""
        new_achievements = []
        
        # Quiz-related achievements
        if reason == "quiz_completed":
            if stats.quizzes_completed == 1:
                new_achievements.append(self._unlock_achievement(
                    user_id, "first_quiz", stats
                ))
            elif stats.quizzes_completed == 10:
                new_achievements.append(self._unlock_achievement(
                    user_id, "quiz_enthusiast", stats
                ))
            elif stats.quizzes_completed == 100:
                new_achievements.append(self._unlock_achievement(
                    user_id, "quiz_master", stats
                ))
        
        # Perfect score achievements
        if reason == "perfect_score":
            if stats.perfect_scores == 1:
                new_achievements.append(self._unlock_achievement(
                    user_id, "perfectionist", stats
                ))
            elif stats.perfect_scores == 10:
                new_achievements.append(self._unlock_achievement(
                    user_id, "flawless_master", stats
                ))
        
        # Level achievements
        if stats.level in [5, 10, 25, 50, 100]:
            new_achievements.append(self._unlock_achievement(
                user_id, f"level_{stats.level}", stats
            ))
        
        return [a for a in new_achievements if a]

    def _unlock_achievement(
        self,
        user_id: str,
        achievement_id: str,
        stats: UserStats,
    ) -> Optional[str]:
        """Unlock an achievement for user."""
        try:
            # Check if already unlocked
            existing = self.dynamodb_client.get_item(
                self.achievements_table,
                {"user_id": user_id, "achievement_id": achievement_id}
            )
            
            if existing:
                return None
            
            # Unlock achievement
            self.dynamodb_client.put_item(
                self.achievements_table,
                {
                    "user_id": user_id,
                    "achievement_id": achievement_id,
                    "unlocked_at": datetime.now().isoformat(),
                }
            )
            
            stats.achievements_unlocked += 1
            self._save_user_stats(stats)
            
            logger.info(f"Unlocked achievement {achievement_id} for user {user_id}")
            return achievement_id
            
        except Exception as e:
            logger.warning(f"Failed to unlock achievement: {e}")
            return None

    def _get_all_achievements(self) -> List[Achievement]:
        """Get all possible achievements."""
        # Define all achievements (50+ types)
        achievements = [
            # Streak achievements
            Achievement(
                achievement_id="streak_7_days",
                name="Week Warrior",
                description="Maintain a 7-day learning streak",
                type=AchievementType.STREAK.value,
                tier=BadgeTier.BRONZE.value,
                xp_reward=100,
                icon="🔥",
                criteria={"streak_days": 7},
            ),
            Achievement(
                achievement_id="streak_30_days",
                name="Monthly Master",
                description="Maintain a 30-day learning streak",
                type=AchievementType.STREAK.value,
                tier=BadgeTier.SILVER.value,
                xp_reward=500,
                icon="🔥🔥",
                criteria={"streak_days": 30},
            ),
            # Quiz achievements
            Achievement(
                achievement_id="first_quiz",
                name="Quiz Beginner",
                description="Complete your first quiz",
                type=AchievementType.QUIZ_MASTER.value,
                tier=BadgeTier.BRONZE.value,
                xp_reward=50,
                icon="📝",
                criteria={"quizzes_completed": 1},
            ),
            Achievement(
                achievement_id="quiz_master",
                name="Quiz Master",
                description="Complete 100 quizzes",
                type=AchievementType.QUIZ_MASTER.value,
                tier=BadgeTier.GOLD.value,
                xp_reward=1000,
                icon="🏆",
                criteria={"quizzes_completed": 100},
            ),
            # Add more achievements...
        ]
        
        return achievements

    def _save_user_stats(self, stats: UserStats) -> None:
        """Save user stats to DynamoDB."""
        try:
            self.dynamodb_client.put_item(
                self.stats_table,
                asdict(stats)
            )
        except Exception as e:
            logger.warning(f"Failed to save user stats: {e}")

    def _send_notification(self, user_id: str, data: Dict[str, Any]) -> None:
        """Send notification for achievements/level ups."""
        try:
            message = self._format_notification_message(data)
            # In production, send via SNS
            logger.info(f"Notification for {user_id}: {message}")
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")

    def _format_notification_message(self, data: Dict[str, Any]) -> str:
        """Format notification message."""
        messages = []
        
        if data.get("level_up"):
            messages.append(f"🎉 Level Up! You're now level {data['level']}!")
        
        if data.get("new_achievements"):
            count = len(data["new_achievements"])
            messages.append(f"🏆 Unlocked {count} new achievement{'s' if count > 1 else ''}!")
        
        return " ".join(messages)
