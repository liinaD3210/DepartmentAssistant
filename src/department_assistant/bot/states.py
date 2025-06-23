# src/department_assistant/bot/states.py
from aiogram.fsm.state import State, StatesGroup

class MeetingProposal(StatesGroup):
    waiting_for_confirmation = State()

class TaskProposal(StatesGroup):
    waiting_for_confirmation = State()