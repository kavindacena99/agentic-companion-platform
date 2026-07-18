"""Deterministic, offline harness for evaluating the reasoning graph.

Runs a full turn through the *real* compiled LangGraph while stubbing the
non-deterministic / external pieces (memory retrieval, agent loader, LLM, tool
provider, reflection critic, writeback) so evaluations are reproducible and need
no network, API keys, or database.

Usage::

    result = run_turn("what is the capital of France?", memories={
        "user_memory": [{"content": "User loves geography", "relevance": 0.9}],
    })
    result.route            # -> "retrieve"
    result.response         # final reply text
    result.trace_labels     # ["input:accepted", "router:retrieve", ...]
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from graph import workflow as wf
from graph.workflow import initial_state


@dataclass
class TurnResult:
    state: Dict[str, Any]

    @property
    def route(self) -> Optional[str]:
        return self.state.get("route")

    @property
    def response(self) -> str:
        return self.state.get("response") or ""

    @property
    def trace(self) -> List[Dict[str, Any]]:
        return self.state.get("trace") or []

    @property
    def trace_labels(self) -> List[str]:
        return [f"{e.get('node')}:{e.get('decision')}" for e in self.trace]

    @property
    def retrieved(self) -> List[Dict[str, Any]]:
        return self.state.get("retrieved") or []

    @property
    def tools_used(self) -> List[str]:
        return [r.get("name") for r in (self.state.get("tool_results") or [])]

    @property
    def safety_flags(self) -> Dict[str, Any]:
        return self.state.get("safety_flags") or {}

    def visited(self, node: str) -> bool:
        return any(e.get("node") == node for e in self.trace)


def _default_llm_node(llm_text: Optional[str], ground: bool):
    def llm_node(state):
        context = dict(state.get("context") or {})
        context.update({"llm_provider": "stub", "llm_ok": True})
        if llm_text is not None:
            text = llm_text
        elif ground and state.get("user_memory"):
            # Ground the reply in the top retrieved memory so groundedness is
            # observable end-to-end.
            top = state["user_memory"][0].get("content", "")
            text = f"Based on what I know: {top}"
        else:
            text = "A helpful reply."
        return {"response": text, "context": context}

    return llm_node


def run_turn(
    message: str,
    *,
    user_id: str = "u_eval",
    agent_id: str = "best_friend",
    memories: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    llm_text: Optional[str] = None,
    ground_with_memory: bool = True,
    reflect_verdict: str = "accept",
    reflect_script: Optional[Callable[..., Dict[str, Any]]] = None,
    route_tools_fn: Optional[Callable[..., Dict[str, Any]]] = None,
) -> TurnResult:
    """Run one turn through the compiled graph with all externals stubbed."""
    saved = {
        "get_relevant_memories": wf.get_relevant_memories,
        "AgentLoaderService": wf.AgentLoaderService,
        "process_writeback": wf.process_writeback,
        "reflect_on_response": wf.reflect_on_response,
        "llm_node": wf.llm_node,
        "route_tools": wf.route_tools,
        "route_llm": wf.route_llm,
    }

    mem = memories or {}

    class _StubLoader:
        def get_agent(self, agent_id):
            return type("P", (), {"to_dict": lambda self: {"persona_prompt": "A warm companion"}})()

    default_reflect = reflect_script or (lambda **k: {"verdict": reflect_verdict, "critique": "fix it", "ok": True})
    # A tool route needs *some* generation; by default answer directly (no tool).
    default_tools = route_tools_fn or (lambda messages, tools, context=None: {"ok": True, "type": "text", "text": llm_text or "A helpful reply."})

    try:
        wf.get_relevant_memories = lambda query, user_id, agent_id, top_k=5: mem
        wf.AgentLoaderService = _StubLoader
        wf.process_writeback = lambda **kwargs: [{"action": "insert", "content": "noted"}]
        wf.reflect_on_response = default_reflect
        wf.llm_node = _default_llm_node(llm_text, ground_with_memory)
        wf.route_tools = default_tools
        wf.route_llm = lambda prompt, ctx=None: {"response": llm_text or "A helpful reply.", "provider": "stub", "ok": True}

        graph = wf.build_workflow()
        state = graph.invoke(
            initial_state(user_id, agent_id, "sess_eval", message),
            config={"recursion_limit": wf.RECURSION_LIMIT},
        )
        return TurnResult(state=state)
    finally:
        for name, value in saved.items():
            setattr(wf, name, value)
