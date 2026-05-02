# ✨ GLOW - Agentic Personal Assistant

**GLOW** (Guided Life Optimization Workflow) is an advanced AI-powered agentic personal assistant built with Azure services. It provides personalized coaching across **4 key life domains**: Career, Learning, Finance, and Wellness.

## 🎯 Problem Statement Solution

GLOW implements all requirements:
- ✅ **Multi-Agent Architecture**: 5 specialized agents (career, learning, finance, wellness, general)
- ✅ **Agentic Behavior**: Intent classification → Memory retrieval → Knowledge search → Agent routing → Response generation
- ✅ **Azure Services**: OpenAI + AI Search + Cosmos DB + Bing Search Integration
- ✅ **Planning & Reasoning**: Proactive goal adjustments and multi-step action planning
- ✅ **Safety Framework**: PII detection, risk assessment, content filtering, disclaimers
- ✅ **Adaptive Learning**: Goal tracking, trend analysis, progress monitoring
- ✅ **Task Tracking**: Study plans, budget analysis, habit tracking, progress trends

## 🏗️ Architecture

```
User Input → Safety Check → Intent Classification → Memory + RAG → Agent Routing → Response
                ↓                                    ↓              ↓
         (PII Detection)                    (Cosmos DB)    (Azure OpenAI)
         (Risk Assessment)                  (AI Search)    (Specialized)
```

## 🚀 Key Features

### 1. Multi-Agent System
- **Learning**: Adaptive study plans, quiz generation, difficulty adjustment
- **Career**: CV analysis, job application checklists, interview prep
- **Finance**: Expense analysis, budgeting, overspending detection
- **Wellness**: Habit tracking, routine planning, motivation patterns
- **General**: Fallback agent for other topics
- **Web Grounding**: Real-time information retrieval via Bing Search API
### 2. Task & Goal Tracking
- Create goals with steps and metrics
- Log progress and detect trends
- Adaptive recommendations based on performance
- Multi-domain support

### 3. Safety & Ethics
- **PII Detection**: Emails, phones, SSNs, credit cards, IPs
- **Risk Assessment**: Flags illegal/harmful requests
- **Auto-Disclaimers**: Domain-specific safety warnings
- **Emergency Detection**: Identifies critical situations

### 4. Chat History
- Persistent storage (up to 10 chats)
- Quick switching between conversations
- Auto-titling based on first message
- Browser localStorage

### 5. RAG Integration
- Azure AI Search for knowledge base
- User conversation history
- Context-aware responses
- Multi-step reasoning

## 📦 Tech Stack
- **Frontend**: React + TypeScript + Vite
- **Backend**: Python + FastAPI
- **AI**: Azure OpenAI (gpt-3.5-turbo / gpt-4)
- **Search**: Azure AI Search
- **Database**: Azure Cosmos DB
- **Safety**: Custom Python evaluator

## 🛡️ Safety Implementation

### PII Detection & Masking
- Email → [EMAIL]
- Phone → [PHONE]
- SSN → [SSN]
- Credit Card → [CREDIT_CARD]
- IP Address → [IP_ADDRESS]

### Risk Levels
- **LOW**: General information, learning, motivation
- **MEDIUM**: Health/finance advice (with disclaimer)
- **HIGH**: Illegal activities, emergencies (blocked)

### Compliance
- ✅ No PII in code (all from .env)
- ✅ No hardcoded API keys
- ✅ Automatic masking of sensitive data
- ✅ Domain-specific disclaimers
- ✅ Emergency detection & referrals

## 📋 Project Structure

```
glow-app/
├── src/                    # React Frontend
│   ├── App.tsx            # Chat with history
│   ├── App.css
│   └── main.tsx
├── main.py                # FastAPI server
├── orchestrator.py        # 🧠 Orchestration engine
├── config.py              # Configuration
├── agents.py              # 🎯 Agent system
├── memory.py              # 💾 Cosmos DB
├── task_tracker.py        # 📊 Goal tracking
├── safety_evaluator.py    # 🛡️  Safety checks
├── .env                   # Secrets (git ignored)
├── requirements.txt
├── package.json
└── README.md
```

## 🚀 Quick Start

### Setup
```bash
# Clone and setup
git clone <repo>
cd glow-app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
```

### Configure `.env`
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=glow-gpt
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-key
AZURE_SEARCH_INDEX=your-index
COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_KEY=your-key
COSMOS_DB=glow-cosmos
COSMOS_CONTAINER=user-memory
```

### Run
```bash
# Terminal 1: Backend
source .venv/bin/activate
uvicorn main:app --reload

# Terminal 2: Frontend
npm run dev

# Open: http://localhost:5173
```

## 📚 Module Documentation

### orchestrator.py
**Central coordination engine** that orchestrates the entire pipeline:
1. Validates request safety
2. Classifies intent (career/learning/finance/wellness)
3. Retrieves user memory from Cosmos DB
4. Searches knowledge base (Azure AI Search)
5. Routes to appropriate agent
6. Generates response
7. Saves to memory

### agents.py
**Specialized agents** for each domain with RAG integration.
- Uses domain-specific prompts
- Integrates knowledge base context
- References user history
- Formats output (numbered lists, bullets)

### memory.py
**Cosmos DB integration** for persistent user data:
- Conversation history
- User preferences
- Goal tracking
- Progress records

### task_tracker.py
**Goal & progress management**:
- `create_goal()` - Create structured goals
- `log_progress()` - Track metrics
- `detect_trends()` - Analyze patterns
- `create_study_plan()` - Generate study schedules
- `analyze_expenses()` - Expense categorization
- `track_habit()` - Habit monitoring

### safety_evaluator.py
**Safety & compliance**:
- `detect_pii()` - Find sensitive info
- `sanitize_text()` - Mask PII
- `assess_risk()` - Evaluate safety
- `validate_request()` - Complete validation
- `get_safety_disclaimer()` - Return warnings

## 🔄 Example Workflow

**User**: "How should I manage my debt?"

1. ✅ **Safety Check** → No PII, Finance domain, LOW RISK
2. 🧠 **Intent** → "finance"
3. 💾 **Memory** → Load previous messages
4. 🔍 **Search** → Find debt management info
5. 🎯 **Agent** → finance_agent selected
6. 📝 **Response** → Formatted with steps/tips
7. 📌 **Disclaimer** → Finance advice warning
8. 💾 **Save** → Memory updated

## 🧪 Testing

```bash
# Test imports
python -c "
from config import *
from orchestrator import handle_message
from task_tracker import create_goal
from safety_evaluator import validate_request
print('✅ All modules loaded')
"

# Test API
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Help with career", "user_id": "test"}'
```

## 🔐 Security

- ✅ No hardcoded secrets
- ✅ PII detection & masking
- ✅ Risk assessment
- ✅ HTTPS encryption
- ✅ Cosmos DB encryption
- ✅ Input validation
- ✅ Per-user data isolation
- ✅ Emergency referrals

## 📈 Production Deployment

- Azure App Service (backend)
- Azure Functions (async tasks)
- Azure CDN (frontend)
- Cosmos DB (serverless)
- Load Balancer (traffic distribution)

## 📄 License

MIT License - Open source

## 🏆 Achievements

✅ Multi-agent agentic system
✅ Full Azure integration
✅ Comprehensive safety framework
✅ Adaptive goal tracking
✅ Persistent chat history
✅ Professional UI
✅ Production-ready code
✅ Complete documentation

---

**Made with ❤️ for Azure AI Challenge**

* No PII stored
* Synthetic data used
* API keys secured via environment variables
* Guardrails applied to prevent harmful outputs
