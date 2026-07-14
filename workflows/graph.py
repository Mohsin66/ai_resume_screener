from langgraph.graph import StateGraph, START, END
from workflows.state import Screening
from agents.nodes import (
    extract_resume_text,
    auto_reject_candidate,
    score_candidate,
    compile_results,
    check_identity_validation,
)

graph = StateGraph(Screening)

graph.add_node("extract_resume_text", extract_resume_text)
graph.add_node("auto_reject_candidate",auto_reject_candidate)
graph.add_node("score_candidate", score_candidate)
graph.add_node("compile_results", compile_results)

# The job description is parsed once in main.py and passed in with each invoke,
# so the graph only screens a single resume: extract -> score -> compile.
graph.add_edge(START, "extract_resume_text")
graph.add_conditional_edges("extract_resume_text", check_identity_validation, {"valid": "score_candidate", "invalid":"auto_reject_candidate"})
graph.add_edge("score_candidate", "compile_results")
graph.add_edge("auto_reject_candidate", "compile_results")
graph.add_edge("compile_results", END)


app = graph.compile()
