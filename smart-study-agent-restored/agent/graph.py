from langgraph.graph import StateGraph,START,END
from agent.state import AgentState
from agent.nodes import build_nodes
from agent.routing import after_extract,after_clarify,after_validate,after_review

def build_graph(planner,checkpointer):
    g=StateGraph(AgentState)
    for name,node in build_nodes(planner).items(): g.add_node(name,node)
    g.add_edge(START,'extract')
    g.add_conditional_edges('extract',after_extract,{'clarify':'clarify','generate':'generate'})
    g.add_conditional_edges('clarify',after_clarify,{'end':END,'extract':'extract'})
    g.add_edge('generate','validate'); g.add_conditional_edges('validate',after_validate,{'retry':'retry','review':'review'})
    g.add_edge('retry','generate'); g.add_conditional_edges('review',after_review,{'generate':'generate','end':END})
    return g.compile(checkpointer=checkpointer)
