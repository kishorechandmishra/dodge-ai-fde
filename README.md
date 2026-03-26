# Dodge AI FDE - Graph Query System

> Natural language interface for exploring business supply chain data through an interactive graph

## 🚀 Live Demo

[Deploy URL will be added here]

## 📋 Overview

This system transforms fragmented business data (orders, deliveries, invoices, payments) into a connected graph and enables natural language queries powered by an LLM.

**Key Features:**
- 📊 Interactive graph visualization (1,063 entities, 1,260 relationships)
- 💬 Natural language query interface
- 🛡️ Guardrails against off-topic queries
- ⚡ Fast in-memory graph processing
- 🎯 Data-backed answers (no hallucination)

## 🏗️ Architecture

### Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Backend | Python + Flask | Simple, fast API development |
| Graph DB | NetworkX | In-memory speed for <10K nodes |
| LLM | Groq API (Llama 3.1 70B) | Free, 10x faster than OpenAI |
| Frontend | Vanilla JS + Tailwind | Zero build tools needed |
| Visualization | Cytoscape.js | Industry standard |

### Design Decisions

**Why NetworkX over Neo4j?**
- ✅ Pure Python (no database server)
- ✅ Faster for <10K nodes (all in-memory)
- ✅ Simpler deployment
- ⚠️ Trade-off: Doesn't scale past 10K nodes

**Graph Schema:**
```
NODES (1,063):
├─ billing_doc (163) - Invoice documents
├─ billing_item (245) - Line items
├─ sales_order (167) - Purchase orders
├─ delivery (137) - Fulfillment records
├─ product (69) - Materials
└─ address (8) - Customer locations

EDGES (1,260):
├─ has_item: Billing → Items
├─ for_product: Item → Product
├─ refs_sales_order: Billing → Order
├─ fulfills_order: Delivery → Order
└─ billed_to: Billing → Customer
```

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.10+
pip
```

### Installation

```bash
# Clone repository
git clone <your-repo>
cd dodge-fde-project

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY from https://console.groq.com

# Run
python server.py
```

Visit: http://localhost:5000

## 📁 Project Structure

```
dodge-fde-project/
├── server.py            # Flask API server
├── graph_engine.py      # Graph construction & queries
├── query_processor.py   # LLM integration & query execution
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
├── data/               # 49 JSONL files
├── static/
│   └── index.html      # Frontend UI
└── README.md
```

## 🔍 Example Queries

### ✅ Supported Queries

**1. Product Analysis**
```
"Which products have the most billing documents?"
```
Returns top 5 products with document counts

**2. Document Tracing**
```
"Trace billing document 90504298"
```
Shows full flow: billing → items → products → orders → deliveries

**3. Incomplete Flows**
```
"Show me sales orders delivered but not billed"
```
Identifies orders with deliveries but no billing

### ❌ Rejected Queries

- "Write me a poem" → Off-topic
- "What's the weather?" → Off-topic
- "Tell me a story" → Off-topic

## 🛡️ Guardrails

**Three-layer defense:**
1. **Regex pre-filter** - Fast rejection of obvious off-topic
2. **LLM system prompt** - Explicit refusal instructions
3. **Response validation** - Check for off-topic flag

## 🌐 Deployment

### Render.com (Recommended)

1. Push to GitHub
2. Connect to Render
3. Configure:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `python server.py`
   - **Env Var:** `GROQ_API_KEY=<your-key>`
4. Deploy

Auto-deploys on git push!

## 📊 API Documentation

### `GET /api/graph/summary`
Returns graph statistics

### `GET /api/graph/data?max_nodes=500`
Returns graph for visualization

### `POST /api/query`
Process natural language query

**Request:**
```json
{"query": "Which products have most billing documents?"}
```

**Response:**
```json
{
  "answer": "Top 5 Products...",
  "success": true
}
```

## 🤖 AI-Assisted Development

Built using:
- Claude (Anthropic) for architecture & coding
- Groq API for runtime LLM queries
- Iterative prompt engineering

**Session logs:** See conversation with Claude in submission

## 📈 Performance

- Data load: ~8 seconds
- Graph: 1,063 nodes, 1,260 edges
- Memory: ~50MB
- API response: <100ms
- LLM response: 1-3 seconds

## 🔮 Future Enhancements

- [ ] SQL/Cypher query generation
- [ ] Node highlighting in graph
- [ ] Conversation memory
- [ ] Graph analytics (clustering, centrality)
- [ ] Streaming LLM responses

## 📝 License

MIT

## 👤 Author

**Kishore Chand Mishra**  
Built for Dodge AI Forward Deployed Engineer Assignment  
March 2026

---

**Assignment Submission:**
- Demo: [URL]
- GitHub: [URL]
- AI Sessions: Included in repo
