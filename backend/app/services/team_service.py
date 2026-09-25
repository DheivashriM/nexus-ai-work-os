from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.team import Team, TeamMember
from app.schemas.team import TeamCreate, TeamUpdate, TeamMemberCreate
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
from app.services.activity_service import ActivityService

class TeamService:
    def __init__(self, db: Session):
        self.db = db
        self.team_repo = TeamRepository(db)
        self.user_repo = UserRepository(db)
        self.activity_service = ActivityService(db)

    def create_team(self, team_in: TeamCreate, current_user_id: str) -> Team:
        team = Team(
            name=team_in.name,
            description=team_in.description
        )
        created_team = self.team_repo.create(team)
        self.activity_service.log_activity(
            activity_type="TEAM_CREATED",
            description=f"Created team '{team.name}'",
            user_id=current_user_id,
            metadata={"team_id": created_team.id}
        )
        return created_team

    def get_team_by_id(self, team_id: str) -> Team:
        team = self.team_repo.get_by_id(team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team '{team_id}' not found."
            )
        return team

    def get_all_teams(self, skip: int = 0, limit: int = 100) -> List[Team]:
        return self.team_repo.get_all(skip=skip, limit=limit)

    def update_team(self, team_id: str, team_in: TeamUpdate) -> Team:
        team = self.get_team_by_id(team_id)
        if team_in.name is not None:
            team.name = team_in.name
        if team_in.description is not None:
            team.description = team_in.description
        return self.team_repo.update(team)

    def add_member(self, team_id: str, member_in: TeamMemberCreate, current_user_id: str) -> TeamMember:
        team = self.get_team_by_id(team_id)
        user = self.user_repo.get_by_id(member_in.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{member_in.user_id}' not found."
            )
        existing = self.team_repo.get_member(team_id, member_in.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{member_in.user_id}' is already a member of team '{team.name}'."
            )
        member = TeamMember(
            team_id=team_id,
            user_id=member_in.user_id,
            role=member_in.role
        )
        added_member = self.team_repo.add_member(member)
        self.activity_service.log_activity(
            activity_type="TEAM_MEMBER_ADDED",
            description=f"Added {user.name} to team '{team.name}'",
            user_id=current_user_id,
            metadata={"team_id": team_id, "user_id": user.id}
        )
        return added_member
