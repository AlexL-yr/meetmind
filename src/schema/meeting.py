from pydantic import BaseModel, Field
from typing import List
class MeetingAction(BaseModel):
  """
  meeting action schema (optional)
  """
  action: str = Field(..., description="The action to take")
  owner: str = Field(..., description="The owner of the meeting")
  deadline: str = Field(default = None, description="The deadline of the meeting")

class MeetingSummary(BaseModel):
    """
    Meeting summary schema
    """

    title: str = Field(..., description="The title of the meeting")
    date: str = Field(..., description="The date of the meeting")
    attendees: List[str] = Field(..., description="The list of meeting attendees")
    summary: str = Field(..., description="The summary of the meeting")
    decisions: List[str] = Field(default_factory=list, description="The decisions made in the meeting")
    action_items: List[MeetingAction] = Field(default_factory=list, description="The action items from the meeting")
    notes: str = Field(default=None, description="Additional notes")

    def to_markdown(self) -> str:
      """
      Convert meeting summary to Markdown format

      Returns:
          str: Formatted Markdown string
      """
      md_parts = [
          f"# {self.title}",
          "",
          f"**Date**: {self.date}",
          "",
          f"**Attendees**: {', '.join(self.attendees)}",
          "",
          "## Meeting Summary",
          "",
          self.summary,
      ]

      # Add meeting decisions
      if self.decisions:
          md_parts.extend(["", "## Decisions", ""])
          for i, decision in enumerate(self.decisions, 1):
              md_parts.append(f"{i}. {decision}")

      # Add action items table
      if self.action_items:
          md_parts.extend(["", "## Action Items", ""])
          md_parts.append("| Action Item | Owner | Deadline |")
          md_parts.append("| :--- | :--- | :--- |")
          for item in self.action_items:
              md_parts.append(f"| {item.action} | {item.owner} | {item.deadline or '-'} |")

      # Add notes
      if self.notes:
          md_parts.extend(["", "## Notes", "", self.notes])

      return "\n".join(md_parts)