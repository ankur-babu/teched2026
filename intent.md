# Product Master Data AI Agent for Sales Representatives

AI-powered agent enabling Sales Representatives to ask natural language questions about product master data from SAP S/4HANA Public Cloud Edition and receive instant, accurate answers — without navigating SAP screens.

## Business challenge

Sales Representatives waste time switching between SAP screens to find basic product information during customer interactions. They need a conversational interface that delivers instant answers about product details directly from SAP S/4HANA Public Cloud.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time to find product information | 5 minutes | Under 30 seconds | — | Product Master Data Lookup / Lead to Cash | user |

## Key Milestones

1. **Agent responds to basic product queries** — Sales Rep can ask "What is product X?" and receive a structured answer from S/4HANA data.
2. **Multi-attribute lookup works** — Agent can retrieve and combine product descriptions, units of measure, classifications, and packaging details in one response.
3. **Agent handles ambiguous queries** — Agent asks clarifying follow-up questions when a product query is unclear or returns multiple matches.
4. **Agent deployed and accessible** — Sales Reps can interact with the agent via Joule or another supported interface.
5. **User acceptance confirmed** — At least one Sales Representative validates the agent answers are accurate and faster than the current SAP screen workflow.

## Business Architecture (RBA)

### End-to-End Process

Lead to Cash Standard B2B

### Process Hierarchy

```
Lead to Cash Standard B2B (E2E)
└── Plan to Optimize Marketing and Sales (Phase)
    └── Plan prices and promotions (BPS-359_002)
        └── Plan and define sales prices
```

### Summary

Sales Reps querying product master data maps to the Lead to Cash E2E, specifically the "Plan prices and promotions" sub-process. The AI agent accelerates access to product information that supports the sales cycle, reducing time lost navigating SAP screens.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
|------------------------|------------------------|------------|-------------------|--------------------|--------------------|---------------------|------|---------------------|
| Retrieve basic product details (descriptions, specs, UoM, packaging) | SAP S/4HANA Cloud Public Edition — Sales Price Planning and Definition | `sap.s4:apiResource:API_PRODUCT_SRV:v1` | — | — | — | — | No | OData API available; MCP server must be custom-built |
| Retrieve product classification & categories | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1` | — | — | — | — | No | OData API available; MCP server must be custom-built |
| Check stock / availability | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:CE_API_PRODUCT_AVAILY_INFO_0001:v1` | — | — | — | — | No | OData API available; MCP server must be custom-built |
| Natural language interface for product queries | No standard SAP product covers this | — | — | — | — | — | Yes | Requires custom AI agent with MCP integration |

### Key findings

- SAP S/4HANA Cloud Public Edition is confirmed in the customer landscape and provides all relevant product master data APIs (Product Master, Classification, Availability).
- No pre-built MCP servers exist for these APIs — custom MCP translation files must be generated from the OData specs.
- The Pricing service API is marked unavailable in this landscape; pricing data will be out of scope unless the user confirms an alternative source.
- The core gap is the natural language interface — this is fulfilled entirely by a custom AI agent.
- Basic product details (descriptions, UoM, packaging, classifications) cover the stated user need of "Basic Product Details".

## Recommendations

### AI Agent for Product Master Data Queries

#### Executive Summary

Custom Python AI agent with MCP tools calling S/4HANA product APIs

#### Recommended Solution

A pro-code Python AI agent (A2A protocol) that accepts natural language questions from Sales Representatives and retrieves product master data from SAP S/4HANA Public Cloud via OData APIs wrapped as MCP tools. The agent interprets the user's query, selects the appropriate MCP tool (product details, classification, availability), and returns a concise, human-readable answer — all without the user needing to touch SAP screens.

#### Problem Statement

Sales Representatives lose an average of 5 minutes per product lookup navigating multiple SAP screens. During customer calls or meetings, this delay is costly and reduces sales effectiveness.

#### Affected User Roles

- Sales Representatives (primary users)
- Sales Managers (secondary, benefit from faster team responsiveness)

#### Important factors

##### Eliminates screen navigation overhead
Sales Reps get answers in under 30 seconds via a conversational interface, compared to 5 minutes of SAP screen navigation.

##### Leverages existing S/4HANA investment
No data migration or replication is needed — the agent reads directly from the system of record via standard OData APIs.

##### Extensible design
Additional product data domains (pricing, batch info) can be added as new MCP tools without redesigning the agent.

#### Potential risks

##### No pre-built MCP servers available
All product master data APIs require custom MCP translation files to be generated. This adds implementation effort but is fully achievable with the available tooling.

##### Pricing data out of scope
The Pricing service API is unavailable in the current landscape. If Sales Reps also need pricing answers, an alternative source must be identified.

#### Recommended solution category

AI Agent

#### Intent fit
90%
