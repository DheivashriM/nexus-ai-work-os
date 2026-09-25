from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.team import Team, TeamMember

class TeamRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, team_id: str) -> Optional[Team]:
        return self.db.query(Team).filter(Team.id == team_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Team]:
        return self.db.query(Team).offset(skip).limit(limit).all()

    def create(self, team: Team) -> Team:
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def update(self, team: Team) -> Team:
        self.db.commit()
        self.db.refresh(team)
        return team

    def add_member(self, member: TeamMember) -> TeamMember:
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def get_member(self, team_id: str, user_id: str) -> Optional[TeamMember]:
        return self.db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()
