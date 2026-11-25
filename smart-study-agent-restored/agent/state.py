from typing import TypedDict
class AgentState(TypedDict,total=False):
    text:str
    images:list[str]
    now:str
    preferences:dict
    existing:list[dict]
    events:list[dict]
    questions:list[str]
    plan:dict
    errors:list[str]
    warnings:list[str]
    feedback:str
    retries:int
    clarifications:int
    reviews:int
    status:str
