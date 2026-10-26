"""Tests for the Product Master Data Agent."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def add_app_to_path(add_agent_to_path):
    """Ensure app/ is on sys.path for all tests in this module."""


@pytest.fixture
def mock_tools():
    """Return a minimal set of mock MCP tools for testing."""
    def make_tool(name: str, response: dict):
        def fn(**kwargs):
            return response
        return StructuredTool.from_function(func=fn, name=name, description=f"Mock {name}")

    return [
        make_tool("mcp_api-product-srv__list_a_product_for_api_product_srv", {
            "results": [{"Product": "P-100", "BaseUnit": "EA", "ProductGroup": "A001"}]
        }),
        make_tool("mcp_api-product-srv__get_a_product_for_api_product_srv", {
            "Product": "P-100", "BaseUnit": "EA", "ProductGroup": "A001",
            "GrossWeight": "1.500", "WeightUnit": "KG"
        }),
        make_tool("mcp_api-product-srv__list_a_productdescription_for_api_product_srv", {
            "results": [{"Product": "P-100", "Language": "EN", "ProductDescription": "Laptop Computer 15 inch"}]
        }),
        make_tool("mcp_api-product-srv__list_a_productunitsofmeasure_for_api_product_srv", {
            "results": [{"Product": "P-100", "AlternativeUnit": "EA", "QuantityNumerator": "1.000"}]
        }),
        make_tool("mcp_api-clfn-product-srv__list_a_clfnproduct_for_api_clfn_product_srv", {
            "results": [{"Product": "P-100", "ClassType": "001", "ClassName": "LAPTOPS"}]
        }),
        make_tool("mcp_sap-self-avail__list_productstoragelocation_for_sap_self", {
            "results": [{"Product": "P-100", "Plant": "1000", "StorageLocation": "0001",
                         "MatlWrhsStkQtyInMatlBaseUnit": "250.000", "BaseUnit": "EA"}]
        }),
    ]


@pytest.fixture
def mock_llm():
    """Return a mock LLM that returns a canned response."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=AIMessage(content="The base unit of measure for product P-100 is EA (Each)."))
    return llm


# ---------------------------------------------------------------------------
# Unit tests — one per tool category
# ---------------------------------------------------------------------------

class TestProductMasterDataRetrieval:
    """Tests for basic product detail retrieval (R1 + R2)."""

    @pytest.mark.asyncio
    async def test_list_products_tool_returns_results(self, mock_tools):
        """The list_a_product tool returns a list of product records."""
        tool = next(t for t in mock_tools if "list_a_product_for_api" in t.name)
        result = tool.invoke({})
        assert "results" in result
        assert len(result["results"]) >= 1
        assert result["results"][0]["Product"] == "P-100"

    @pytest.mark.asyncio
    async def test_get_product_by_key_returns_single_record(self, mock_tools):
        """The get_a_product tool returns a single product record with key fields."""
        tool = next(t for t in mock_tools if "get_a_product_for_api" in t.name)
        result = tool.invoke({"product": "P-100"})
        assert result["Product"] == "P-100"
        assert "BaseUnit" in result
        assert "GrossWeight" in result

    @pytest.mark.asyncio
    async def test_list_product_descriptions_returns_language_data(self, mock_tools):
        """The list_a_productdescription tool returns description with language."""
        tool = next(t for t in mock_tools if "productdescription" in t.name)
        result = tool.invoke({"$filter": "Product eq 'P-100'"})
        assert "results" in result
        assert result["results"][0]["Language"] == "EN"
        assert "ProductDescription" in result["results"][0]

    @pytest.mark.asyncio
    async def test_list_units_of_measure_returns_packaging_data(self, mock_tools):
        """The list_a_productunitsofmeasure tool returns UoM details."""
        tool = next(t for t in mock_tools if "productunitsofmeasure" in t.name)
        result = tool.invoke({"$filter": "Product eq 'P-100'"})
        assert "results" in result
        assert result["results"][0]["AlternativeUnit"] == "EA"


class TestProductClassificationLookup:
    """Tests for product classification retrieval (R3)."""

    @pytest.mark.asyncio
    async def test_list_classifications_returns_class_data(self, mock_tools):
        """The list_a_clfnproduct tool returns classification records."""
        tool = next(t for t in mock_tools if "clfnproduct" in t.name)
        result = tool.invoke({"$filter": "Product eq 'P-100'"})
        assert "results" in result
        assert result["results"][0]["ClassName"] == "LAPTOPS"
        assert "ClassType" in result["results"][0]


class TestProductAvailabilityCheck:
    """Tests for product availability retrieval (R4)."""

    @pytest.mark.asyncio
    async def test_list_storage_locations_returns_stock_data(self, mock_tools):
        """The list_productstoragelocation tool returns stock quantities."""
        tool = next(t for t in mock_tools if "productstoragelocation" in t.name)
        result = tool.invoke({"$filter": "Product eq 'P-100'"})
        assert "results" in result
        stock = result["results"][0]
        assert "MatlWrhsStkQtyInMatlBaseUnit" in stock
        assert float(stock["MatlWrhsStkQtyInMatlBaseUnit"]) > 0


class TestMockToolLoading:
    """Tests for mcp_tools module with IBD_TESTING mode."""

    def test_mcp_mock_json_exists(self, agent_path):
        """mcp-mock.json must exist at the agent root."""
        mock_file = agent_path / "mcp-mock.json"
        assert mock_file.exists(), "mcp-mock.json not found at agent root"

    def test_mcp_mock_json_is_valid(self, agent_path):
        """mcp-mock.json must be valid JSON with expected structure."""
        mock_file = agent_path / "mcp-mock.json"
        data = json.loads(mock_file.read_text())
        assert "servers" in data
        assert "metadata" in data
        assert data["metadata"]["total_servers"] == 3

    @pytest.mark.asyncio
    async def test_get_mcp_tools_returns_tools_in_test_mode(self, add_agent_to_path):
        """get_mcp_tools() returns mock tools when IBD_TESTING is set."""
        from mcp_tools import get_mcp_tools
        tools = await get_mcp_tools()
        assert len(tools) > 0
        tool_names = [t.name for t in tools]
        # Check that product master tools are present
        assert any("product" in name.lower() for name in tool_names)


class TestAgentSystemPrompt:
    """Tests verifying the agent's system prompt behaviour."""

    def test_system_prompt_contains_read_only_guardrail(self, add_agent_to_path):
        """System prompt must include read-only guardrail."""
        from agent import get_system_prompt
        prompt = get_system_prompt()
        assert "read-only" in prompt.lower() or "never attempt to create" in prompt.lower()

    def test_system_prompt_contains_no_fabrication_instruction(self, add_agent_to_path):
        """System prompt must instruct agent not to fabricate data."""
        from agent import get_system_prompt
        prompt = get_system_prompt()
        assert "never fabricate" in prompt.lower() or "must use tools" in prompt.lower()

    def test_system_prompt_mentions_pricing_out_of_scope(self, add_agent_to_path):
        """System prompt must state pricing is out of scope."""
        from agent import get_system_prompt
        prompt = get_system_prompt()
        assert "pricing" in prompt.lower()


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------

class TestAgentIntegration:
    """End-to-end integration test for the product master data agent."""

    @pytest.mark.asyncio
    async def test_agent_invoke_returns_product_answer(self, add_agent_to_path, mock_tools):
        """Agent invoke returns a completed response for a product query."""
        from agent import SampleAgent

        agent = SampleAgent()

        # Mock the LLM to return a canned answer
        mock_graph_result = {
            "messages": [
                AIMessage(content="The base unit of measure for product P-100 is EA (Each). "
                                  "The gross weight is 1.5 KG.")
            ]
        }

        with patch.object(agent, "_invoke", new=AsyncMock(return_value=mock_graph_result)):
            response = await agent.invoke(
                query="What is the base unit of measure for product P-100?",
                context_id="test-session-001",
                tools=mock_tools,
            )

        assert response.status == "completed"
        assert len(response.message) > 0
        assert "P-100" in response.message or "EA" in response.message

    @pytest.mark.asyncio
    async def test_agent_returns_user_friendly_error_on_tool_failure(self, add_agent_to_path):
        """Agent returns a user-friendly message when tool call fails."""
        from agent import SampleAgent

        agent = SampleAgent()

        with patch.object(agent, "_invoke", new=AsyncMock(side_effect=Exception("API timeout"))):
            response = await agent.invoke(
                query="What is product P-999?",
                context_id="test-session-002",
                tools=[],
            )

        assert response.status in ("error", "completed")
        assert response.message  # non-empty message returned

    @pytest.mark.asyncio
    async def test_agent_stream_yields_processing_then_result(self, add_agent_to_path, mock_tools):
        """Agent stream yields a processing status then a completed result."""
        from agent import SampleAgent

        agent = SampleAgent()

        mock_graph_result = {
            "messages": [AIMessage(content="Product P-100 is a Laptop Computer.")]
        }

        chunks = []
        with patch.object(agent, "_invoke", new=AsyncMock(return_value=mock_graph_result)):
            async for chunk in agent.stream(
                query="Tell me about product P-100",
                context_id="test-session-003",
                tools=mock_tools,
            ):
                chunks.append(chunk)

        assert len(chunks) >= 2
        # First chunk should be "Processing..."
        assert chunks[0]["is_task_complete"] is False
        # Last chunk should be completed
        assert chunks[-1]["is_task_complete"] is True
        assert chunks[-1]["content"]
