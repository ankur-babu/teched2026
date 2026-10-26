# Specification: product-master-data-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read the project input (`product-requirements-document.md`, `intent.md`)
- [x] Bootstrap agent code in `assets/product-master-data-agent/` using instructions from the sap-agent-bootstrap section. (invoke from inside `assets/product-master-data-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

> **Before proceeding**, read [guidelines-agent-skills.md](../guidelines-agent-skills.md) and decide — based on the PRD/intent — whether the agent needs runtime skills.

- [x] Evaluate if runtime skills are needed. This agent answers natural language product queries — the logic is relatively straightforward. A runtime skill for product query handling may be useful if the system prompt becomes complex. Create `assets/product-master-data-agent/app/skills/product-query/SKILL.md` only if the system prompt exceeds manageable size.

---

## Project-Specific Tasks

### System Prompt & Agent Identity

- [x] Open `assets/product-master-data-agent/app/agent.py` and configure the agent's system prompt (`get_system_prompt`) with:
  - Agent role: AI assistant for Sales Representatives that answers natural language questions about product master data from SAP S/4HANA Public Cloud
  - Scope: product descriptions, units of measure, packaging details, product classification and categories, and stock availability
  - Behaviour: always use MCP tools to retrieve live data — never fabricate or guess product information
  - Ambiguity handling: when a query matches multiple products or lacks enough detail, ask a single targeted clarifying question before calling any tool
  - Limitations: pricing data is out of scope; if asked about pricing, inform the user clearly
  - Tone: concise, professional, structured responses suitable for use during customer conversations

### Product Master Data Retrieval (R1 + R2)

- [x] Implement tool usage for basic product detail queries using the `API_PRODUCT_SRV` MCP tool:
  - Retrieve product descriptions, base unit of measure, and packaging details
  - Combine multi-attribute data into a single, human-readable response
  - Handle cases where a product is not found — return a clear, friendly message

### Product Classification & Category Lookup (R3)

- [x] Implement tool usage for product classification queries using the `API_CLFN_PRODUCT_SRV` MCP tool:
  - Retrieve product classification and category data for a given product
  - Present classification in a structured, easy-to-read format

### Product Availability Check (R4)

- [x] Implement tool usage for stock and availability queries using the `CE_API_PRODUCT_AVAILY_INFO_0001` MCP tool:
  - Retrieve current stock status and availability information
  - Present availability results clearly — avoid raw API field names in the response

### Ambiguous Query Handling (R5)

- [x] Implement ambiguity detection logic in the system prompt / agent reasoning:
  - When a query matches multiple products, ask one targeted clarifying question (e.g., "Could you provide the product ID or a more specific name?")
  - When a query cannot be resolved after clarification, explain the limitation clearly without fabricating data
  - Never guess between multiple product matches — always ask

### Live Data Guarantee (R6)

- [x] Verify in `agent.py` that every response involving product data invokes an MCP tool — no static/cached responses
- [x] Ensure the agent relays tool errors as user-friendly messages (e.g., "I was unable to retrieve product information at this time. Please try again.")
- [x] Add guardrail instruction to the system prompt: agent must never write, update, or delete data in SAP S/4HANA — all operations are read-only

---

## MCP Tool Integration

> Read [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for complete MCP integration patterns.

- [x] Verify `specification/product-master-data-agent/api-specs/` contains the three downloaded EDMX files:
  - `API_PRODUCT_SRV.edmx` — Product Master (A2X)
  - `API_CLFN_PRODUCT_SRV.edmx` — Product Master Data Including Classification
  - `CE_API_PRODUCT_AVAILY_INFO_0001.edmx` — Product Availability Info
- [x] Invoke `mcp-translation-file` skill for each EDMX file to generate MCP translation files, then invoke `setup-solution` to register the MCP assets
- [x] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from the `mcp_tools` module — see [guidelines-agent-python.md](../guidelines-agent-python.md) for canonical pattern. NEVER import directly from `sap_cloud_sdk.agentgateway`. NEVER create direct HTTP clients.
- [x] Add MCP server dependencies to `asset.yaml` under `requires` — one entry per generated MCP server, using exact ORD IDs from generated assets
- [x] Generate `mcp-mock.json` using the `mcp-mock-config` skill after MCP translation files are complete (required before tests can run)

**MCP API scope definitions** (for `mcp-translation-file` skill pruning):

```
MCP API: sap.s4:apiResource:API_PRODUCT_SRV:v1
MCP tool scope: read-only
Resources in scope: A_Product, A_ProductDescription, A_ProductBasicText, A_ProductSalesDelivery, A_ProductUnitsOfMeasure
```

```
MCP API: sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1
MCP tool scope: read-only
Resources in scope: A_ClfnProduct, A_ClfnProductCharc, A_ClfnProductClass
```

```
MCP API: sap.s4:apiResource:CE_API_PRODUCT_AVAILY_INFO_0001:v1
MCP tool scope: read-only
Resources in scope: all
```

---

## Business Instrumentation

- [x] Implement business step instrumentation for each milestone from the PRD using structured logging and OpenTelemetry spans. See [guidelines-agent-python.md](../guidelines-agent-python.md) for Python-specific implementation.

  - **M1** — Agent responds to basic product queries
    - Log on achievement: `M1.achieved: basic product query resolved successfully — product data returned from S/4HANA`
    - Log on miss: `M1.missed: basic product query did not resolve — API call failed or no data returned`

  - **M2** — Multi-attribute lookup works
    - Log on achievement: `M2.achieved: multi-attribute product lookup completed — all requested attributes returned`
    - Log on miss: `M2.missed: multi-attribute lookup incomplete — one or more attributes could not be retrieved`

  - **M3** — Agent handles ambiguous queries
    - Log on achievement: `M3.achieved: ambiguous query resolved via clarification — correct product identified`
    - Log on miss: `M3.missed: ambiguous query not resolved — clarification did not lead to a unique product match`

  - **M4** — Agent deployed and accessible
    - Log on achievement: `M4.achieved: agent deployed and first production query successfully handled`
    - Log on miss: `M4.missed: agent deployment incomplete or first production query failed`

  - **M5** — User acceptance confirmed
    - Log on achievement: `M5.achieved: user acceptance confirmed — lookup time target met and accuracy validated`
    - Log on miss: `M5.missed: user acceptance not confirmed — lookup time or accuracy target not met`

- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## Testing

> See [guidelines-agent-python.md](../guidelines-agent-python.md) for Python testing setup and patterns.

- [x] `conftest.py` only sets `IBD_TESTING=true` — this causes the agent to run with mock MCP tool results during tests
- [x] Write unit tests in `assets/product-master-data-agent/tests/`:
  - One test for product master data retrieval (basic product details)
  - One test for product classification lookup
  - One test for product availability check
  - One test for ambiguous query handling (verify agent asks a clarifying question)
  - One test for not-found product (verify user-friendly error message)
- [x] Write one integration test executing the end-to-end agent flow by calling the agent's `invoke` function with mocked LLM responses and mocked MCP tools (tests must run offline)
- [x] Run `pytest` from `assets/product-master-data-agent/` (no args, no extra flags) — if coverage < 70%, add tests until threshold met
- [x] Run `pytest` again from `assets/product-master-data-agent/` (no args) to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/product-master-data-agent/` — if not, run pytest again until it does
