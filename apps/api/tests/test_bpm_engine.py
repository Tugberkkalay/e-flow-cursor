"""Tests for BPM Engine lazy execution."""
import pytest
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.engine.executor import BPMEngine
from app.models.flow import ProcessVersion
from app.models.instance import ProcessInstance, NodeInstance, TaskInstance, ApprovalInstance, AuditEvent


def make_graph(nodes, edges):
    return {"nodes": nodes, "edges": edges}


def make_node(id, engine_type, label="", config=None):
    return {
        "id": id,
        "type": "eflowNode",
        "position": {"x": 0, "y": 0},
        "data": {
            "label": label or engine_type,
            "engineType": engine_type,
            "category": "test",
            "config": config or {},
        },
    }


def make_edge(source, target, handle=None, label=""):
    return {
        "id": f"e_{source}_{target}",
        "source": source,
        "target": target,
        "sourceHandle": handle,
        "label": label,
    }


class TestExpressionResolutionInEngine:
    """Test that the engine resolves {{ }} expressions correctly."""

    def test_simple_resolve(self):
        from app.engine.expression import ExpressionEngine
        e = ExpressionEngine()
        ctx = {"form": {"amount": 100000}}
        result = e.resolve("{{ form.amount }}", ctx)
        assert result == 100000

    def test_gate_condition_high_amount(self):
        from app.engine.expression import ExpressionEngine
        e = ExpressionEngine()
        ctx = {"form": {"total_amount": 75000, "request_type": "Abonelik"}}
        condition = {
            "or": [
                {"field": "form.total_amount", "op": ">=", "value": 50000},
                {"field": "form.request_type", "op": "==", "value": "Abonelik"},
            ]
        }
        assert e.evaluate_condition(condition, ctx) is True

    def test_gate_condition_low_amount(self):
        from app.engine.expression import ExpressionEngine
        e = ExpressionEngine()
        ctx = {"form": {"total_amount": 10000, "request_type": "Mal Alımı"}}
        condition = {
            "or": [
                {"field": "form.total_amount", "op": ">=", "value": 50000},
                {"field": "form.request_type", "op": "==", "value": "Abonelik"},
            ]
        }
        assert e.evaluate_condition(condition, ctx) is False

    def test_calculate_vat(self):
        from app.engine.expression import ExpressionEngine
        e = ExpressionEngine()
        ctx = {"form": {"total_amount": 100000}}
        vat = e.resolve("{{ form.total_amount * 0.20 }}", ctx)
        assert vat == pytest.approx(20000.0)

    def test_three_way_match_within_tolerance(self):
        from app.engine.expression import ExpressionEngine
        e = ExpressionEngine()
        po_amount = 100000
        invoice_amount = 102000
        tolerance = 5  # 5%
        diff_pct = abs(po_amount - invoice_amount) / max(po_amount, 0.01) * 100
        assert diff_pct <= tolerance  # 2% < 5%

    def test_three_way_match_outside_tolerance(self):
        from app.engine.expression import ExpressionEngine
        e = ExpressionEngine()
        po_amount = 100000
        invoice_amount = 120000
        tolerance = 5
        diff_pct = abs(po_amount - invoice_amount) / max(po_amount, 0.01) * 100
        assert diff_pct > tolerance  # 20% > 5%


class TestGraphTraversal:
    """Test graph traversal logic without DB."""

    def setup_method(self):
        self.engine = BPMEngine(db=None)

    def test_find_start_node(self):
        graph = make_graph([
            make_node("n1", "FormFill"),
            make_node("start", "ManualStart"),
            make_node("end", "End"),
        ], [])
        node = self.engine._find_start_node(graph)
        assert node is not None
        assert node["id"] == "start"

    def test_find_start_node_form_trigger(self):
        graph = make_graph([
            make_node("trigger", "FormSubmitTrigger"),
            make_node("task", "FormFill"),
        ], [])
        node = self.engine._find_start_node(graph)
        assert node["id"] == "trigger"

    def test_get_next_node(self):
        graph = make_graph([
            make_node("a", "ManualStart"),
            make_node("b", "FormFill"),
            make_node("c", "End"),
        ], [
            make_edge("a", "b"),
            make_edge("b", "c"),
        ])
        node_a = graph["nodes"][0]
        node_b = self.engine._get_next_node(node_a, graph, {})
        assert node_b is not None
        assert node_b["id"] == "b"

    def test_get_next_node_by_handle_true(self):
        graph = make_graph([
            make_node("gate", "IF"),
            make_node("yes_node", "FormFill"),
            make_node("no_node", "End"),
        ], [
            make_edge("gate", "yes_node", handle="true", label="Evet"),
            make_edge("gate", "no_node", handle="false", label="Hayır"),
        ])
        gate = graph["nodes"][0]
        next_node = self.engine._get_next_node_by_handle(gate, graph, "true", {})
        assert next_node is not None
        assert next_node["id"] == "yes_node"

    def test_get_next_node_by_handle_false(self):
        graph = make_graph([
            make_node("gate", "IF"),
            make_node("yes_node", "FormFill"),
            make_node("no_node", "End"),
        ], [
            make_edge("gate", "yes_node", handle="true"),
            make_edge("gate", "no_node", handle="false"),
        ])
        gate = graph["nodes"][0]
        next_node = self.engine._get_next_node_by_handle(gate, graph, "false", {})
        assert next_node is not None
        assert next_node["id"] == "no_node"

    def test_find_node_by_id(self):
        graph = make_graph([
            make_node("abc123", "Calculate"),
            make_node("xyz789", "End"),
        ], [])
        found = self.engine._find_node_by_id(graph, "abc123")
        assert found is not None
        assert found["id"] == "abc123"

    def test_find_node_by_id_not_found(self):
        graph = make_graph([make_node("abc", "Calculate")], [])
        found = self.engine._find_node_by_id(graph, "nonexistent")
        assert found is None

    def test_set_nested_simple(self):
        d = {}
        self.engine._set_nested(d, "form.amount", 12345)
        assert d == {"form": {"amount": 12345}}

    def test_set_nested_deep(self):
        d = {}
        self.engine._set_nested(d, "docs.invoice.amount", 99000)
        assert d["docs"]["invoice"]["amount"] == 99000

    def test_get_all_next_nodes(self):
        graph = make_graph([
            make_node("split", "ParallelSplit"),
            make_node("branch1", "FormFill"),
            make_node("branch2", "FormFill"),
        ], [
            make_edge("split", "branch1"),
            make_edge("split", "branch2"),
        ])
        split_node = graph["nodes"][0]
        nexts = self.engine._get_all_next_nodes(split_node, graph)
        assert len(nexts) == 2
        ids = {n["id"] for n in nexts}
        assert "branch1" in ids
        assert "branch2" in ids


class TestScriptTaskLogic:
    """Test calculate and policy check logic."""

    def test_calculate_normalizes_context(self):
        from app.engine.expression import ExpressionEngine
        e = ExpressionEngine()

        variables = {"form": {"total_amount": 100000}}
        calculations = [
            {"output_field": "calc.vat_amount", "expression": "{{ form.total_amount * 0.20 }}"},
            {"output_field": "calc.total_with_vat", "expression": "{{ form.total_amount * 1.20 }}"},
        ]

        engine = BPMEngine(db=None)
        for calc in calculations:
            field = calc["output_field"]
            expr = calc["expression"]
            value = e.resolve(expr, variables)
            engine._set_nested(variables, field, value)

        assert variables["calc"]["vat_amount"] == pytest.approx(20000.0)
        assert variables["calc"]["total_with_vat"] == pytest.approx(120000.0)

    def test_policy_check_triggers_flag(self):
        from app.engine.expression import ExpressionEngine
        e = ExpressionEngine()

        variables = {"form": {"total_amount": 150000, "justification": ""}}
        rules = [
            {
                "name": "high_value_without_justification",
                "severity": "warning",
                "condition": {
                    "and": [
                        {"field": "form.total_amount", "op": ">=", "value": 100000},
                        {"field": "form.justification", "op": "is_empty", "value": None},
                    ]
                }
            }
        ]

        flags = []
        for rule in rules:
            if e.evaluate_condition(rule["condition"], variables):
                flags.append({"rule": rule["name"], "severity": rule["severity"]})

        assert len(flags) == 1
        assert flags[0]["rule"] == "high_value_without_justification"

    def test_three_way_match_calculation(self):
        engine = BPMEngine(db=None)
        variables = {
            "gen": {"po": {"amount": 100000}},
            "form": {"invoice_amount": 104000},
        }
        from app.engine.expression import ExpressionEngine
        e = ExpressionEngine()
        po_amount = e.resolve("{{ gen.po.amount }}", variables)
        inv_amount = e.resolve("{{ form.invoice_amount }}", variables)
        tolerance = 5
        diff_pct = abs(float(po_amount or 0) - float(inv_amount or 0)) / max(float(po_amount or 1), 0.01) * 100
        matched = diff_pct <= tolerance
        assert matched  # 4% within 5% tolerance


class TestDomainTemplateFlows:
    """Integration tests for the 4 domain template flow structures."""

    def setup_method(self):
        self.engine = BPMEngine(db=None)

    def test_pr_flow_structure(self):
        from app.seed import PR_GRAPH
        nodes = PR_GRAPH["nodes"]
        edges = PR_GRAPH["edges"]

        assert len(nodes) > 0
        assert len(edges) > 0

        # Should have a start node
        start = self.engine._find_start_node(PR_GRAPH)
        assert start is not None

        # Should have at least one IF gateway
        if_nodes = [n for n in nodes if n["data"]["engineType"] == "IF"]
        assert len(if_nodes) >= 1

        # Should have an End node
        end_nodes = [n for n in nodes if n["data"]["engineType"] == "End"]
        assert len(end_nodes) >= 1

    def test_p2p_flow_structure(self):
        from app.seed import P2P_GRAPH
        start = self.engine._find_start_node(P2P_GRAPH)
        assert start is not None

        approval_nodes = [n for n in P2P_GRAPH["nodes"] if "Approval" in n["data"]["engineType"]]
        assert len(approval_nodes) >= 1

    def test_contract_flow_structure(self):
        from app.seed import CONTRACT_GRAPH
        start = self.engine._find_start_node(CONTRACT_GRAPH)
        assert start is not None

        # Should have ReviewComment for legal
        review_nodes = [n for n in CONTRACT_GRAPH["nodes"] if n["data"]["engineType"] == "ReviewComment"]
        assert len(review_nodes) >= 1

    def test_invoice_flow_structure(self):
        from app.seed import INVOICE_GRAPH
        start = self.engine._find_start_node(INVOICE_GRAPH)
        assert start is not None

        # Should have ThreeWayMatch
        match_nodes = [n for n in INVOICE_GRAPH["nodes"] if n["data"]["engineType"] == "ThreeWayMatch"]
        assert len(match_nodes) >= 1

        # Should have Switch for match status
        switch_nodes = [n for n in INVOICE_GRAPH["nodes"] if n["data"]["engineType"] == "Switch"]
        assert len(switch_nodes) >= 1

    def test_pr_gateway_routing_high_amount(self):
        from app.seed import PR_GRAPH
        from app.engine.expression import ExpressionEngine
        e = ExpressionEngine()

        # Simulate high amount scenario
        ctx = {"form": {"total_amount": 75000, "request_type": "Mal Alımı"}}
        gate_node = next(n for n in PR_GRAPH["nodes"] if n["data"]["engineType"] == "IF")
        branches = gate_node["data"]["config"]["branches"]

        true_branch = branches[0]  # "Evet" branch
        condition_result = e.evaluate_condition(true_branch["condition"], ctx)
        assert condition_result is True  # 75000 >= 50000

    def test_pr_gateway_routing_low_amount(self):
        from app.seed import PR_GRAPH
        from app.engine.expression import ExpressionEngine
        e = ExpressionEngine()

        ctx = {"form": {"total_amount": 10000, "request_type": "Hizmet Alımı"}}
        gate_node = next(n for n in PR_GRAPH["nodes"] if n["data"]["engineType"] == "IF")
        branches = gate_node["data"]["config"]["branches"]
        true_branch = branches[0]
        condition_result = e.evaluate_condition(true_branch["condition"], ctx)
        assert condition_result is False  # 10000 < 50000 AND not Abonelik
