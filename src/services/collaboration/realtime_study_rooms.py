"""Real-time collaborative study rooms with WebSocket support."""

import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict

from ...shared.aws_clients.dynamodb_client import DynamoDBClient
from ...shared.utils.logger import get_logger
from ...shared.utils.errors import ServiceError

logger = get_logger(__name__)


@dataclass
class Participant:
    """Study room participant."""
    user_id: str
    username: str
    connection_id: str
    joined_at: str
    score: int = 0
    is_active: bool = True


@dataclass
class StudyRoom:
    """Collaborative study room."""
    room_id: str
    name: str
    creator_id: str
    max_participants: int
    participants: List[Participant]
    current_activity: Optional[str]
    created_at: str
    is_active: bool


@dataclass
class QuizBattle:
    """Live quiz battle."""
    battle_id: str
    room_id: str
    quiz_id: str
    participants: List[str]
    scores: Dict[str, int]
    current_question: int
    total_questions: int
    started_at: str
    status: str  # waiting, active, completed


class RealtimeStudyRooms:
    """
    Real-time collaborative learning with WebSocket.
    
    Features:
    - Create and join study rooms
    - Live quiz battles
    - Real-time progress synchronization
    - Chat and collaboration
    - Leaderboards
    - Screen sharing (ready)
    """

    def __init__(
        self,
        dynamodb_client: Optional[DynamoDBClient] = None,
    ):
        """Initialize realtime study rooms."""
        self.dynamodb_client = dynamodb_client or DynamoDBClient()
        self.rooms_table = "study_rooms"
        self.battles_table = "quiz_battles"
        self.connections_table = "websocket_connections"
        
        # In-memory cache for active connections
        self.active_connections: Dict[str, Set[str]] = defaultdict(set)
        
        logger.info("RealtimeStudyRooms initialized")

    def create_room(
        self,
        creator_id: str,
        room_name: str,
        max_participants: int = 10,
    ) -> StudyRoom:
        """
        Create a new study room.
        
        Args:
            creator_id: Creator user ID
            room_name: Room name
            max_participants: Maximum number of participants
            
        Returns:
            StudyRoom object
        """
        try:
            room_id = f"room_{creator_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            room = StudyRoom(
                room_id=room_id,
                name=room_name,
                creator_id=creator_id,
                max_participants=max_participants,
                participants=[],
                current_activity=None,
                created_at=datetime.now().isoformat(),
                is_active=True,
            )
            
            # Save to DynamoDB
            self._save_room(room)
            
            logger.info(f"Created study room: {room_id}")
            return room
            
        except Exception as e:
            logger.error(f"Error creating room: {e}", exc_info=True)
            raise ServiceError(f"Failed to create room: {str(e)}")

    def join_room(
        self,
        room_id: str,
        user_id: str,
        username: str,
        connection_id: str,
    ) -> Dict[str, Any]:
        """
        Join a study room.
        
        Args:
            room_id: Room identifier
            user_id: User identifier
            username: Username
            connection_id: WebSocket connection ID
            
        Returns:
            Dictionary with room info and participants
        """
        try:
            room = self._load_room(room_id)
            
            # Check if room is full
            if len(room.participants) >= room.max_participants:
                raise ServiceError("Room is full")
            
            # Check if already in room
            if any(p.user_id == user_id for p in room.participants):
                raise ServiceError("Already in room")
            
            # Add participant
            participant = Participant(
                user_id=user_id,
                username=username,
                connection_id=connection_id,
                joined_at=datetime.now().isoformat(),
            )
            room.participants.append(participant)
            
            # Save room
            self._save_room(room)
            
            # Track connection
            self.active_connections[room_id].add(connection_id)
            
            # Broadcast join event
            self._broadcast_to_room(
                room_id,
                {
                    "type": "user_joined",
                    "user_id": user_id,
                    "username": username,
                    "participant_count": len(room.participants),
                }
            )
            
            logger.info(f"User {user_id} joined room {room_id}")
            
            return {
                "room_id": room_id,
                "room_name": room.name,
                "participants": [
                    {
                        "user_id": p.user_id,
                        "username": p.username,
                        "score": p.score,
                        "joined_at": p.joined_at,
                    }
                    for p in room.participants
                ],
                "current_activity": room.current_activity,
            }
            
        except Exception as e:
            logger.error(f"Error joining room: {e}", exc_info=True)
            raise ServiceError(f"Failed to join room: {str(e)}")

    def leave_room(
        self,
        room_id: str,
        user_id: str,
        connection_id: str,
    ) -> None:
        """Leave a study room."""
        try:
            room = self._load_room(room_id)
            
            # Remove participant
            room.participants = [
                p for p in room.participants
                if p.user_id != user_id
            ]
            
            # Save room
            self._save_room(room)
            
            # Remove connection
            self.active_connections[room_id].discard(connection_id)
            
            # Broadcast leave event
            self._broadcast_to_room(
                room_id,
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "participant_count": len(room.participants),
                }
            )
            
            logger.info(f"User {user_id} left room {room_id}")
            
        except Exception as e:
            logger.error(f"Error leaving room: {e}", exc_info=True)

    def start_quiz_battle(
        self,
        room_id: str,
        quiz_id: str,
        question_count: int = 10,
    ) -> QuizBattle:
        """
        Start a live quiz battle.
        
        Args:
            room_id: Room identifier
            quiz_id: Quiz identifier
            question_count: Number of questions
            
        Returns:
            QuizBattle object
        """
        try:
            room = self._load_room(room_id)
            
            battle_id = f"battle_{room_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Get participant IDs
            participant_ids = [p.user_id for p in room.participants]
            
            battle = QuizBattle(
                battle_id=battle_id,
                room_id=room_id,
                quiz_id=quiz_id,
                participants=participant_ids,
                scores={uid: 0 for uid in participant_ids},
                current_question=0,
                total_questions=question_count,
                started_at=datetime.now().isoformat(),
                status="active",
            )
            
            # Save battle
            self._save_battle(battle)
            
            # Update room activity
            room.current_activity = f"quiz_battle:{battle_id}"
            self._save_room(room)
            
            # Broadcast battle start
            self._broadcast_to_room(
                room_id,
                {
                    "type": "quiz_battle_started",
                    "battle_id": battle_id,
                    "quiz_id": quiz_id,
                    "question_count": question_count,
                    "participants": participant_ids,
                }
            )
            
            logger.info(f"Started quiz battle: {battle_id}")
            return battle
            
        except Exception as e:
            logger.error(f"Error starting quiz battle: {e}", exc_info=True)
            raise ServiceError(f"Failed to start quiz battle: {str(e)}")

    def submit_battle_answer(
        self,
        battle_id: str,
        user_id: str,
        question_index: int,
        answer: str,
        is_correct: bool,
        time_taken_ms: int,
    ) -> Dict[str, Any]:
        """
        Submit answer in quiz battle.
        
        Args:
            battle_id: Battle identifier
            user_id: User identifier
            question_index: Question index
            answer: User's answer
            is_correct: Whether answer is correct
            time_taken_ms: Time taken in milliseconds
            
        Returns:
            Dictionary with updated scores and rankings
        """
        try:
            battle = self._load_battle(battle_id)
            
            # Calculate points (faster = more points)
            if is_correct:
                base_points = 100
                time_bonus = max(0, 50 - (time_taken_ms // 1000))
                points = base_points + time_bonus
                battle.scores[user_id] = battle.scores.get(user_id, 0) + points
            
            # Save battle
            self._save_battle(battle)
            
            # Get rankings
            rankings = sorted(
                battle.scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Broadcast update
            self._broadcast_to_room(
                battle.room_id,
                {
                    "type": "battle_answer_submitted",
                    "user_id": user_id,
                    "question_index": question_index,
                    "is_correct": is_correct,
                    "points_earned": points if is_correct else 0,
                    "rankings": [
                        {"user_id": uid, "score": score}
                        for uid, score in rankings
                    ],
                }
            )
            
            return {
                "battle_id": battle_id,
                "user_score": battle.scores.get(user_id, 0),
                "rankings": rankings,
                "points_earned": points if is_correct else 0,
            }
            
        except Exception as e:
            logger.error(f"Error submitting battle answer: {e}", exc_info=True)
            raise ServiceError(f"Failed to submit answer: {str(e)}")

    def sync_progress(
        self,
        room_id: str,
        user_id: str,
        progress_data: Dict[str, Any],
    ) -> None:
        """
        Sync user progress in real-time.
        
        Args:
            room_id: Room identifier
            user_id: User identifier
            progress_data: Progress data to sync
        """
        try:
            # Broadcast progress update
            self._broadcast_to_room(
                room_id,
                {
                    "type": "progress_update",
                    "user_id": user_id,
                    "progress": progress_data,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            
        except Exception as e:
            logger.error(f"Error syncing progress: {e}", exc_info=True)

    def send_chat_message(
        self,
        room_id: str,
        user_id: str,
        username: str,
        message: str,
    ) -> None:
        """Send chat message to room."""
        try:
            self._broadcast_to_room(
                room_id,
                {
                    "type": "chat_message",
                    "user_id": user_id,
                    "username": username,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending chat message: {e}", exc_info=True)

    def get_room_leaderboard(
        self,
        room_id: str,
    ) -> List[Dict[str, Any]]:
        """Get room leaderboard."""
        try:
            room = self._load_room(room_id)
            
            # Sort by score
            leaderboard = sorted(
                room.participants,
                key=lambda p: p.score,
                reverse=True
            )
            
            return [
                {
                    "rank": i + 1,
                    "user_id": p.user_id,
                    "username": p.username,
                    "score": p.score,
                }
                for i, p in enumerate(leaderboard)
            ]
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}", exc_info=True)
            return []

    def _broadcast_to_room(
        self,
        room_id: str,
        message: Dict[str, Any],
    ) -> None:
        """Broadcast message to all room participants."""
        # In production, use API Gateway WebSocket API
        # to send messages to all connections
        logger.info(f"Broadcasting to room {room_id}: {message['type']}")
        
        # This would use boto3 to post to WebSocket connections
        # for connection_id in self.active_connections[room_id]:
        #     apigatewaymanagementapi.post_to_connection(
        #         ConnectionId=connection_id,
        #         Data=json.dumps(message)
        #     )

    def _save_room(self, room: StudyRoom) -> None:
        """Save room to DynamoDB."""
        try:
            item = {
                "room_id": room.room_id,
                "name": room.name,
                "creator_id": room.creator_id,
                "max_participants": room.max_participants,
                "participants": [asdict(p) for p in room.participants],
                "current_activity": room.current_activity,
                "created_at": room.created_at,
                "is_active": room.is_active,
            }
            self.dynamodb_client.put_item(self.rooms_table, item)
        except Exception as e:
            logger.warning(f"Failed to save room: {e}")

    def _load_room(self, room_id: str) -> StudyRoom:
        """Load room from DynamoDB."""
        try:
            item = self.dynamodb_client.get_item(
                self.rooms_table,
                {"room_id": room_id}
            )
            
            if not item:
                raise ServiceError(f"Room not found: {room_id}")
            
            participants = [Participant(**p) for p in item.get("participants", [])]
            
            return StudyRoom(
                room_id=item["room_id"],
                name=item["name"],
                creator_id=item["creator_id"],
                max_participants=item["max_participants"],
                participants=participants,
                current_activity=item.get("current_activity"),
                created_at=item["created_at"],
                is_active=item.get("is_active", True),
            )
        except Exception as e:
            logger.error(f"Failed to load room: {e}", exc_info=True)
            raise ServiceError(f"Failed to load room: {str(e)}")

    def _save_battle(self, battle: QuizBattle) -> None:
        """Save battle to DynamoDB."""
        try:
            self.dynamodb_client.put_item(self.battles_table, asdict(battle))
        except Exception as e:
            logger.warning(f"Failed to save battle: {e}")

    def _load_battle(self, battle_id: str) -> QuizBattle:
        """Load battle from DynamoDB."""
        try:
            item = self.dynamodb_client.get_item(
                self.battles_table,
                {"battle_id": battle_id}
            )
            
            if not item:
                raise ServiceError(f"Battle not found: {battle_id}")
            
            return QuizBattle(**item)
        except Exception as e:
            logger.error(f"Failed to load battle: {e}", exc_info=True)
            raise ServiceError(f"Failed to load battle: {str(e)}")
