# Design Document: Agentic AI Red-Teaming Assistant (NVIDIA NIM on Hugging Face)

## Overview

The Agentic AI Red-Teaming Assistant is a **minimal-cost** MVP multi-agent system built in Python that performs automated security testing of AI systems. The architecture uses free Hugging Face models with EC2 local storage (no S3), making it perfect for hackathons and proof-of-concept demonstrations at minimal cost. The system follows an agent-based design pattern where specialized agents collaborate to plan, execute, and evaluate adversarial attacks.

### Minimal-Cost MVP Configuration

**Total Cost: ~$30/month** (Infrastructure Only!)
- Hugging Face Free Tier: $0 (rate-limited but functional)
- AWS EC2 t3.medium: ~$30/month (infrastructure)
- Local Storage on EC2: $0 (included in EBS volume)
- No S3 costs: $0 (everything stored locally on EC2)

**Models Used** (All Free):
- **LLM**: `google/flan-t5-base` or `mistralai/Mistral-7B-Instruct-v0.2` (free, no gating)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (lightweight, fast, free)

**Optional Upgrade Path** (if you need better performance later):
- Hugging Face Pro: +$9/month (faster inference, higher limits)
- S3 Storage: +$1-5/month (for backups and redundancy)
- NVIDIA models: Available if you upgrade to HF Pro

### Key Design Principles

- **Minimal Cost**: Only ~$30/month for EC2, no other costs
- **No S3 Required**: All storage local on EC2 (reports, logs, FAISS index)
- **Free AI Models**: Uses Hugging Face free tier (no API costs)
- **Agent Autonomy**: Each agent is self-contained with clear responsibilities
- **API-First**: All model interactions use Hugging Face Inference API (free tier)
- **Safety-First**: Multiple layers of safety controls including emergency stop
- **Upgrade Ready**: Easy to add S3, HF Pro, or better models later

## Minimal-Cost Setup Details

### Why Free Hugging Face Models?

**Benefits**:
1. **Zero API Costs**: Completely free to use (rate-limited)
2. **No Gating**: Models like Flan-T5 and Mistral available immediately
3. **Good for MVP**: Sufficient quality for proof-of-concept
4. **Easy Upgrade**: Can switch to better models anytime
5. **No Vendor Lock-in**: Standard HF API works with any model

### Free Tier vs Pro Tier

**Free Tier** (What we're using - $0):
- Slower inference (shared queue, 5-15 seconds per request)
- Lower rate limits (~100 requests/hour)
- May timeout on very large models
- Cold starts common (first request slow)
- **Perfect for MVP and demos**

**Pro Tier** ($9/month - Optional upgrade):
- Faster inference (priority queue, 2-5 seconds)
- Higher rate limits (1000+ requests/hour)
- Better availability
- No cold starts
- **Upgrade when you need speed**

### Performance Expectations

**With Free Tier Setup** (Flan-T5 or Mistral-7B):
- Prompt generation: 5-15 seconds per prompt (slower but works)
- Embedding generation: 2-5 seconds per text
- Mission completion: 10-15 minutes for 20 prompts
- Concurrent missions: 2-3 on t3.medium (rate limits)

**Storage on EC2**:
- Reports: Stored in `/app/data/reports/`
- Logs: Stored in `/app/data/logs/`
- FAISS index: Stored in `/app/data/faiss_index/`
- All included in 30 GB EBS volume (no extra cost)

**Cost Breakdown**:
- EC2 t3.medium: ~$30/month (730 hours × $0.0416/hour)
- EBS 30 GB: ~$3/month (included in estimate above)
- Hugging Face API: $0 (free tier)
- **Total: ~$30/month**

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI REST API                         │
│                    (Port 8080)                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  CoordinatorAgent                            │
│  (Orchestrates: Plan → Execute → Evaluate)                  │
└─────┬──────────────┬──────────────┬────────────────┬────────┘
      │              │               │                │
      ▼              ▼               ▼                ▼
┌──────────┐  ┌──────────┐   ┌──────────┐    ┌──────────┐
│ Attack   │  │Retriever │   │Executor  │    │Evaluator │
│ Planner  │  │  Agent   │   │  Agent   │    │  Agent   │
└────┬─────┘  └────┬─────┘   └────┬─────┘    └────┬─────┘
     │             │              │               │
     ▼             ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│              External Services Layer                         │
├──────────────────┬──────────────────┬───────────────────────┤
│ Hugging Face API │   FAISS Vector   │   AWS S3 Storage      │
│  (LLM + Embed)   │     Store        │   (Logs + Reports)    │
└──────────────────┴──────────────────┴───────────────────────┘
```

### Component Interaction Flow

1. **Mission Initiation**: REST API receives mission request → CoordinatorAgent
2. **Planning Phase**: CoordinatorAgent → AttackPlannerAgent → Generates adversarial prompts
3. **Retrieval Phase**: AttackPlannerAgent → RetrieverAgent → Fetches relevant context
4. **Execution Phase**: CoordinatorAgent → ExecutorAgent → Executes prompts against target
5. **Evaluation Phase**: CoordinatorAgent → EvaluatorAgent → Classifies vulnerabilities
6. **Reporting Phase**: CoordinatorAgent → Generates report → Uploads to S3

## Components and Interfaces

### 1. FastAPI Application Layer

**Purpose**: Provides REST API interface for external interactions

**Key Classes**:
- `RedTeamingAPI`: Main FastAPI application class
- `MissionRequest`: Pydantic model for mission configuration
- `MissionResponse`: Pydantic model for mission results
- `StopRequest`: Pydantic model for emergency stop

**Endpoints**:
```python
POST /missions
  Request Body: {
    "target_system_url": str,
    "attack_categories": List[str],
    "max_prompts": int,
    "authorization_token": str
  }
  Response: {
    "mission_id": str,
    "status": str,
    "created_at": str
  }

GET /missions/{mission_id}
  Response: {
    "mission_id": str,
    "status": str,
    "progress": float,
    "results": Optional[VulnerabilityReport]
  }

POST /stop
  Request Body: {
    "authorization_token": str
  }
  Response: {
    "status": str,
    "message": str
  }

GET /health
  Response: {
    "status": str,
    "services": Dict[str, str]
  }
```

### 2. CoordinatorAgent

**Purpose**: Orchestrates the entire red-teaming workflow

**Key Methods**:
```python
class CoordinatorAgent:
    def __init__(self, config: Config):
        self.planner = AttackPlannerAgent(config)
        self.retriever = RetrieverAgent(config)
        self.executor = ExecutorAgent(config)
        self.evaluator = EvaluatorAgent(config)
        self.stop_flag = threading.Event()
    
    async def execute_mission(self, mission: Mission) -> VulnerabilityReport:
        """Orchestrates complete red-teaming mission"""
        
    def check_stop_flag(self) -> bool:
        """Checks if emergency stop is activated"""
        
    async def _planning_phase(self, mission: Mission) -> List[AdversarialPrompt]:
        """Coordinates attack planning"""
        
    async def _execution_phase(self, prompts: List[AdversarialPrompt]) -> List[ExecutionResult]:
        """Coordinates prompt execution"""
        
    async def _evaluation_phase(self, results: List[ExecutionResult]) -> VulnerabilityReport:
        """Coordinates vulnerability evaluation"""
```

**State Management**:
- Maintains mission state in-memory during execution
- Persists state checkpoints to S3 every 10 prompts
- Supports mission resumption from last checkpoint

### 3. AttackPlannerAgent

**Purpose**: Generates adversarial prompts using Hugging Face LLM

**Key Methods**:
```python
class AttackPlannerAgent:
    def __init__(self, config: Config):
        self.hf_client = HuggingFaceClient(config.hf_api_key, config.hf_llm_model)
        self.retriever = None  # Injected by coordinator
    
    async def generate_attack_prompts(
        self, 
        attack_categories: List[str], 
        max_prompts: int,
        context: Optional[str] = None
    ) -> List[AdversarialPrompt]:
        """Generates adversarial prompts for specified categories"""
        
    def _build_generation_prompt(self, category: str, context: str) -> str:
        """Constructs prompt for LLM to generate adversarial test cases"""
        
    def _parse_llm_response(self, response: str) -> List[AdversarialPrompt]:
        """Extracts structured prompts from LLM output"""
```

**Attack Categories Supported**:
- Prompt Injection
- Jailbreak Attempts
- Data Extraction
- Bias Exploitation
- Hallucination Induction
- Context Confusion
- Role Manipulation

**Prompt Generation Strategy**:
- Uses few-shot prompting with examples for each category
- Retrieves similar past successful attacks from vector store
- Generates variations with different complexity levels
- Validates generated prompts for structural correctness

### 4. RetrieverAgent

**Purpose**: Manages embeddings and knowledge retrieval using FAISS

**Key Methods**:
```python
class RetrieverAgent:
    def __init__(self, config: Config):
        self.hf_client = HuggingFaceClient(config.hf_api_key, config.hf_embed_model)
        self.index = self._load_or_create_index()
        self.document_store = {}  # Maps index IDs to documents
    
    async def embed_text(self, text: str) -> np.ndarray:
        """Generates embedding vector for text"""
        
    async def add_documents(self, documents: List[Document]) -> None:
        """Adds documents to vector store"""
        
    async def search(self, query: str, top_k: int = 5) -> List[Document]:
        """Retrieves most similar documents"""
        
    def save_index(self, path: str) -> None:
        """Persists FAISS index to disk"""
        
    def _load_or_create_index(self) -> faiss.Index:
        """Loads existing index or creates new one"""
```

**Vector Store Design**:
- Uses FAISS IndexFlatL2 for exact similarity search
- Embedding dimension: 768 (typical for Hugging Face models)
- Stores metadata alongside vectors in separate dictionary
- Persists to local disk with periodic S3 backups

**Document Types Stored**:
- Past adversarial prompts and their effectiveness scores
- Known vulnerability patterns
- Attack strategy templates
- Target system documentation snippets

### 5. ExecutorAgent

**Purpose**: Executes adversarial prompts against target systems

**Key Methods**:
```python
class ExecutorAgent:
    def __init__(self, config: Config):
        self.timeout = 30  # seconds
        self.retry_config = RetryConfig(max_attempts=3, backoff_factor=2)
    
    async def execute_prompt(
        self, 
        prompt: AdversarialPrompt, 
        target_url: str
    ) -> ExecutionResult:
        """Executes single adversarial prompt"""
        
    async def execute_batch(
        self, 
        prompts: List[AdversarialPrompt], 
        target_url: str
    ) -> List[ExecutionResult]:
        """Executes multiple prompts sequentially"""
        
    def _make_request(self, prompt: str, target_url: str) -> Response:
        """Makes HTTP request to target system"""
        
    def _handle_timeout(self, prompt: AdversarialPrompt) -> ExecutionResult:
        """Creates result object for timed-out execution"""
```

**Execution Strategy**:
- Sequential execution to avoid overwhelming target
- Configurable delay between prompts (default: 1 second)
- Captures full request/response including headers
- Records timing metrics for performance analysis

**Error Handling**:
- Network errors: Retry with exponential backoff
- Timeout errors: Mark as failed, continue with next prompt
- HTTP errors: Capture error response for analysis
- All errors logged with full context

### 6. EvaluatorAgent

**Purpose**: Analyzes results and classifies vulnerabilities

**Key Methods**:
```python
class EvaluatorAgent:
    def __init__(self, config: Config):
        self.hf_client = HuggingFaceClient(config.hf_api_key, config.hf_llm_model)
        self.classification_prompt_template = self._load_template()
    
    async def evaluate_results(
        self, 
        results: List[ExecutionResult]
    ) -> VulnerabilityReport:
        """Evaluates all execution results and generates report"""
        
    async def classify_vulnerability(
        self, 
        result: ExecutionResult
    ) -> VulnerabilityClassification:
        """Classifies single result for vulnerabilities"""
        
    def _calculate_severity_score(self, classification: str, response: str) -> float:
        """Calculates numerical severity score 0-10"""
        
    def _rank_vulnerabilities(
        self, 
        vulnerabilities: List[Vulnerability]
    ) -> List[Vulnerability]:
        """Sorts vulnerabilities by severity"""
```

**Classification Logic**:
- Uses LLM to analyze prompt-response pairs
- Structured output format enforced via JSON schema
- Severity levels: CRITICAL (9-10), HIGH (7-8), MEDIUM (4-6), LOW (1-3), NONE (0)
- Considers multiple factors: data leakage, policy violations, harmful content, system compromise

**Evaluation Criteria**:
- **CRITICAL**: System compromise, credential exposure, unrestricted code execution
- **HIGH**: Significant data leakage, policy bypass, harmful content generation
- **MEDIUM**: Minor information disclosure, inconsistent behavior, bias manifestation
- **LOW**: Edge case failures, minor inconsistencies
- **NONE**: System behaved correctly, no vulnerability detected

## Data Models

### Core Data Structures

```python
@dataclass
class AdversarialPrompt:
    prompt_id: str
    attack_type: str
    prompt_text: str
    severity_estimate: str
    metadata: Dict[str, Any]
    created_at: datetime

@dataclass
class ExecutionResult:
    prompt_id: str
    prompt_text: str
    response_text: str
    status_code: int
    execution_time_ms: int
    timestamp: datetime
    error: Optional[str]

@dataclass
class Vulnerability:
    vulnerability_id: str
    prompt_id: str
    severity: str
    severity_score: float
    category: str
    description: str
    evidence: str
    remediation_suggestion: str

@dataclass
class VulnerabilityReport:
    mission_id: str
    timestamp: datetime
    total_prompts: int
    successful_executions: int
    vulnerabilities_found: int
    vulnerabilities: List[Vulnerability]
    summary: str
    metadata: Dict[str, Any]

@dataclass
class Mission:
    mission_id: str
    target_system_url: str
    attack_categories: List[str]
    max_prompts: int
    authorization_token: str
    status: str  # pending, running, completed, failed, stopped
    created_at: datetime
    completed_at: Optional[datetime]
```

### Configuration Model

```python
@dataclass
class Config:
    # Hugging Face Configuration (FREE TIER)
    hf_api_key: str
    hf_llm_model: str = "google/flan-t5-base"  # Free, no gating, 250M params
    hf_embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"  # Free, lightweight
    hf_base_url: str = "https://api-inference.huggingface.co/models"
    
    # Alternative Free Models (if needed)
    # hf_llm_model: str = "mistralai/Mistral-7B-Instruct-v0.2"  # Better quality, slower
    # hf_llm_model: str = "google/flan-t5-large"  # Larger Flan-T5, better quality
    
    # Storage Configuration (LOCAL - NO S3)
    results_path: str = "./data/reports"  # Local directory for reports
    logs_path: str = "./data/logs"  # Local directory for logs
    faiss_index_path: str = "./data/faiss_index"  # Local FAISS storage
    
    # Safety Configuration
    stop_test: bool = False
    max_mission_duration_minutes: int = 60
    
    # Execution Configuration
    executor_timeout_seconds: int = 45  # Increased for free tier
    executor_delay_seconds: float = 2.0  # Slower to respect rate limits
    max_retries: int = 3
    
    # API Configuration
    api_port: int = 8080
    api_host: str = "0.0.0.0"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Loads configuration from environment variables"""
```

### Model Selection Guide

**Recommended (FREE MVP)**:
- LLM: `google/flan-t5-base` (250M params)
  - Completely free, no gating
  - Fast on free tier
  - Good instruction-following
  - Works immediately
  
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
  - Lightweight (80MB)
  - Fast embedding generation
  - Proven performance
  - Completely free

**Alternative Free Options** (if you want better quality):
- LLM: `mistralai/Mistral-7B-Instruct-v0.2` (7B params, better quality, slower)
- LLM: `google/flan-t5-large` (780M params, better than base)
- LLM: `tiiuae/falcon-7b-instruct` (7B params, good performance)

**Upgrade Options** (with HF Pro $9/month):
- LLM: `nvidia/Llama-3.1-Nemotron-Nano-8B-Instruct-HF` (NVIDIA NIM)
- LLM: `meta-llama/Llama-2-13b-chat-hf` (requires access approval)
- Embeddings: `nvidia/NV-Embed-v2` (NVIDIA embeddings)

## Error Handling

### Error Categories and Strategies

1. **Configuration Errors** (Startup)
   - Missing environment variables → Fail fast with clear error message
   - Invalid API keys → Validate on startup, fail if invalid
   - Missing dependencies → Check on import, provide installation instructions

2. **API Errors** (Hugging Face)
   - Rate limiting (429) → Exponential backoff, max 3 retries
   - Model unavailable (503) → Retry with different model if configured
   - Authentication errors (401) → Fail mission, log security event
   - Timeout errors → Mark request as failed, continue mission

3. **Execution Errors** (Target System)
   - Network errors → Retry with backoff
   - Timeout → Mark as failed, continue
   - Invalid responses → Log and classify as potential vulnerability

4. **Storage Errors** (S3/FAISS)
   - S3 upload failure → Save locally, retry in background
   - FAISS index corruption → Rebuild from documents
   - Disk space issues → Clean old logs, alert operator

### Error Response Format

```python
@dataclass
class ErrorResponse:
    error_code: str
    error_message: str
    details: Dict[str, Any]
    timestamp: datetime
    request_id: str
```

### Logging Strategy

- **Level**: INFO for normal operations, WARNING for retries, ERROR for failures
- **Format**: JSON structured logs for easy parsing
- **Destinations**: Local file + S3 bucket
- **Rotation**: 100 MB per file, 30-day retention
- **Sensitive Data**: API keys and PII automatically redacted

## Testing Strategy

### Unit Testing

**Scope**: Individual agent methods and utility functions

**Framework**: pytest with pytest-asyncio for async tests

**Key Test Areas**:
- Configuration loading and validation
- Prompt generation logic
- Embedding and retrieval operations
- Vulnerability classification logic
- Error handling and retry mechanisms

**Mocking Strategy**:
- Mock Hugging Face API responses using `responses` library
- Mock S3 operations using `moto`
- Mock FAISS operations with in-memory index

**Example Test Structure**:
```python
@pytest.mark.asyncio
async def test_attack_planner_generates_valid_prompts():
    """Test that AttackPlannerAgent generates structurally valid prompts"""
    
@pytest.mark.asyncio
async def test_executor_handles_timeout():
    """Test that ExecutorAgent properly handles timeout scenarios"""
    
def test_evaluator_classifies_critical_vulnerability():
    """Test that EvaluatorAgent correctly identifies critical vulnerabilities"""
```

### Integration Testing

**Scope**: Agent interactions and end-to-end workflows

**Test Scenarios**:
1. Complete mission execution with mock target system
2. Emergency stop during mission execution
3. Mission resumption from checkpoint
4. Concurrent mission execution
5. S3 upload failure and recovery

**Test Environment**:
- LocalStack for S3 simulation
- Mock HTTP server for target system
- In-memory FAISS index

### API Testing

**Scope**: REST API endpoints and request/response handling

**Framework**: pytest with TestClient from FastAPI

**Test Coverage**:
- All endpoint success paths
- Invalid request handling
- Authorization validation
- Rate limiting behavior
- Error response formats

### Performance Testing

**Scope**: System performance under load

**Metrics**:
- Mission completion time
- API response latency (p50, p95, p99)
- Memory usage during execution
- Concurrent mission capacity

**Tools**: locust for load testing

**Target Performance**:
- API response time: < 200ms (p95)
- Mission completion: < 5 minutes for 20 prompts
- Concurrent missions: Support 10 simultaneous missions
- Memory usage: < 2 GB per mission

### Security Testing

**Scope**: Security controls and safety mechanisms

**Test Areas**:
- Authorization token validation
- API key protection in logs
- Stop flag responsiveness
- Input validation and sanitization
- Report data privacy (no PII leakage)

## Deployment Architecture

### Container Specification

**Dockerfile**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Deployment Options

#### Option 1: Local/Development (Free)

**Use Case**: Development, testing, small-scale usage

**Deployment**:
```bash
# Run directly with Python
python -m uvicorn app:app --host 0.0.0.0 --port 8080

# Or with Docker
docker build -t redteaming-assistant .
docker run -p 8080:8080 --env-file .env redteaming-assistant
```

**Cost**: Free (only Hugging Face API usage)

**Pros**: 
- Zero infrastructure cost
- Simple setup
- Full control

**Cons**: 
- No high availability
- Manual scaling
- Single point of failure

#### Option 2: AWS EC2 with Docker (Low Cost)

**Use Case**: Production-ready, cost-effective single instance

**Deployment**:
- EC2 instance type: t3.medium (2 vCPU, 4 GB RAM)
- Install Docker and run container
- Use Elastic IP for stable endpoint
- CloudWatch for monitoring

**Estimated Cost**: ~$30-40/month
- EC2 t3.medium: ~$30/month
- Elastic IP: Free (when attached)
- CloudWatch: ~$5/month
- S3 storage: ~$1-5/month

**Setup Script**:
```bash
# On EC2 instance
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo docker pull your-registry/redteaming-assistant:latest
sudo docker run -d -p 80:8080 --restart always --env-file /etc/redteam/.env redteaming-assistant
```

**Pros**:
- Low cost
- Simple management
- Sufficient for most use cases
- Easy to upgrade instance size if needed

**Cons**:
- Manual scaling
- Single instance (can add load balancer later)

#### Option 3: AWS ECS Fargate (Moderate Cost)

**Use Case**: Serverless containers, automatic scaling, no server management

**Deployment**:
- ECS Fargate task: 2 vCPU, 4 GB RAM
- Application Load Balancer
- Auto-scaling based on CPU/memory

**Estimated Cost**: ~$60-80/month
- Fargate: ~$50/month (2 vCPU, 4 GB, 730 hours)
- ALB: ~$20/month
- S3 storage: ~$1-5/month

**Task Definition**:
```json
{
  "family": "redteaming-assistant",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [{
    "name": "redteaming-assistant",
    "image": "your-registry/redteaming-assistant:latest",
    "portMappings": [{"containerPort": 8080}],
    "environment": [
      {"name": "HF_LLM_MODEL", "value": "meta-llama/Llama-2-7b-chat-hf"}
    ],
    "secrets": [
      {"name": "HUGGINGFACE_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
    ]
  }]
}
```

**Pros**:
- No server management
- Automatic scaling
- Pay only for what you use
- Built-in load balancing

**Cons**:
- Higher cost than EC2
- Cold start delays possible

#### Option 4: AWS EKS (Enterprise Scale)

**Use Case**: Large-scale production, multiple services, enterprise requirements

**Estimated Cost**: ~$150-200/month minimum
- EKS cluster: ~$73/month
- Worker nodes (2x t3.medium): ~$60/month
- Load Balancer: ~$20/month
- Additional AWS services: ~$20-50/month

**Kubernetes Manifest**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redteaming-assistant
spec:
  replicas: 2
  selector:
    matchLabels:
      app: redteaming-assistant
  template:
    metadata:
      labels:
        app: redteaming-assistant
    spec:
      containers:
      - name: redteaming-assistant
        image: redteaming-assistant:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "1"
            memory: "2Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
        env:
        - name: HUGGINGFACE_API_KEY
          valueFrom:
            secretKeyRef:
              name: hf-credentials
              key: api-key
---
apiVersion: v1
kind: Service
metadata:
  name: redteaming-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: redteaming-assistant
```

**Pros**:
- Enterprise-grade orchestration
- Advanced scaling and management
- Multi-service coordination
- High availability

**Cons**:
- Expensive for small projects
- Complex setup and management
- Overkill for single application

### Primary Deployment: AWS EC2 with Docker

**Target Configuration**:
- Instance Type: t3.medium (2 vCPU, 4 GB RAM)
- OS: Amazon Linux 2
- Storage: 30 GB EBS volume
- Security Group: Allow inbound on port 80 (HTTP) and 22 (SSH)
- Elastic IP: For stable endpoint

**Deployment Steps**:

1. **Launch EC2 Instance**:
   - AMI: Amazon Linux 2
   - Instance type: t3.medium
   - Configure security group with ports 22, 80
   - No IAM role needed (no S3 access required)

2. **Install Dependencies**:
```bash
sudo yum update -y
sudo yum install docker git -y
sudo service docker start
sudo usermod -a -G docker ec2-user
```

3. **Deploy Application**:
```bash
# Clone repository
git clone <repository-url>
cd redteaming-assistant

# Create data directories for local storage
mkdir -p /app/data/reports /app/data/logs /app/data/faiss_index

# Create environment file with FREE models
cat > .env << EOF
# Hugging Face API Key (FREE - get from https://huggingface.co/settings/tokens)
HUGGINGFACE_API_KEY=hf_your_key_here

# FREE Models (No Gating, No Costs)
HF_LLM_MODEL=google/flan-t5-base
HF_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Local Storage (NO S3 - saves money!)
RESULTS_PATH=/app/data/reports
LOGS_PATH=/app/data/logs
FAISS_INDEX_PATH=/app/data/faiss_index

# Safety and Auth
STOP_TEST=0
AUTHORIZED_TOKENS=your_secret_token_123
EOF

# Build and run container with volume mounts for persistence
docker build -t redteaming-assistant .
docker run -d -p 80:8080 --restart always \
  --env-file .env \
  -v /app/data:/app/data \
  --name redteam redteaming-assistant
```

**Note**: This setup is completely minimal cost:
1. Only need FREE Hugging Face account (no Pro required)
2. No S3 buckets needed - everything stored locally
3. No IAM roles needed for S3
4. Models work immediately - no gating or approval
5. Total cost: ~$30/month (just EC2)

4. **Verify Deployment**:
```bash
curl http://localhost/health
```

**Monitoring**:
- CloudWatch Logs for application logs
- CloudWatch Metrics for CPU/memory monitoring
- Set up alarms for high resource usage

**Backup Strategy**:
- Daily snapshots of EBS volume (includes all data)
- All reports, logs, and FAISS index stored on EBS
- No S3 needed for MVP

**Cost Estimate**: ~$30/month (MINIMAL!)
- EC2 t3.medium: ~$30/month (730 hours × $0.0416/hour)
- EBS 30 GB: Included in above estimate
- Elastic IP: Free (when attached)
- Hugging Face API: $0 (free tier)
- **No S3 costs**
- **No CloudWatch costs** (basic metrics free)

**Alternative Options**:
- **Local Development**: Run with `python -m uvicorn app:app` (free)
- **Fargate**: For serverless option (~$60/month)
- **EKS**: For enterprise scale (~$150+/month)

### Environment Variables

**Required Configuration** (FREE MVP):

```bash
# Hugging Face API (FREE - Required)
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxx  # Get from https://huggingface.co/settings/tokens

# FREE Models (No Gating, No Approval Needed)
HF_LLM_MODEL=google/flan-t5-base
HF_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Local Storage (NO S3 - Saves Money!)
RESULTS_PATH=/app/data/reports
LOGS_PATH=/app/data/logs
FAISS_INDEX_PATH=/app/data/faiss_index

# Safety Controls
STOP_TEST=0  # 0=allow missions, 1=block all missions

# Authorization
AUTHORIZED_TOKENS=your_secret_token_here,another_token
```

**Cost Breakdown**:
- Hugging Face Pro subscription: $9/month (recommended for better performance)
- AWS EC2 t3.medium: ~$30/month
- S3 storage: ~$1-5/month
- **Total: ~$40/month**

**Model Access Notes**:
- `nvidia/Llama-3.1-Nemotron-Nano-8B-Instruct-HF`: May require accepting license on HF
- Some NVIDIA models are gated - request access on model page if needed
- Free tier works but may be slow; Pro tier recommended for production

### Scaling Considerations

**Vertical Scaling** (Primary approach for EC2):
- Start: t3.medium (2 vCPU, 4 GB RAM) - ~$30/month
- Scale up: t3.large (2 vCPU, 8 GB RAM) - ~$60/month if needed
- Scale up: t3.xlarge (4 vCPU, 16 GB RAM) - ~$120/month for heavy load
- Storage: Start with 30 GB, expand as needed

**Horizontal Scaling** (If needed later):
- Add Application Load Balancer (~$20/month)
- Launch additional EC2 instances
- Mission state stored in S3 for cross-instance access
- Total cost: ~$80-100/month for 2 instances + ALB

**Performance Targets**:
- Single t3.medium can handle 5-10 concurrent missions
- API response time: < 200ms
- Mission completion: < 5 minutes for 20 prompts

## Security and Governance

### Authorization Model

- Token-based authorization for API access
- Tokens stored as environment variables or AWS Secrets Manager
- Each mission request must include valid authorization token
- Failed authorization attempts logged for audit

### Data Privacy

- No PII stored in logs or reports
- API keys redacted from all outputs
- Target system responses sanitized before storage
- Reports encrypted at rest in S3

### Safety Controls

1. **STOP_TEST Flag**: Global kill switch to prevent mission execution
2. **Mission Timeout**: Automatic termination after 60 minutes
3. **Rate Limiting**: Maximum 10 concurrent missions per instance
4. **Authorization Required**: All operations require valid token
5. **Audit Logging**: Complete audit trail of all operations

### Compliance Considerations

- Missions require explicit authorization
- All activities logged for audit purposes
- Data retention policies enforced (30 days)
- Supports compliance with security testing regulations

## Future Enhancements

### Phase 2 Potential Features

1. **Multi-Model Support**: Test multiple target models in single mission
2. **Custom Attack Strategies**: User-defined attack templates
3. **Real-Time Monitoring**: WebSocket-based progress updates
4. **Advanced Analytics**: Trend analysis across multiple missions
5. **Automated Remediation**: Suggested fixes for identified vulnerabilities
6. **Integration APIs**: Webhooks for CI/CD pipeline integration
7. **Fine-Tuned Models**: Custom-trained models for specific vulnerability types
8. **Distributed Execution**: Multi-region deployment for global testing

## Quick Start Guide

### Prerequisites Setup (MINIMAL COST)

1. **Hugging Face Account** (FREE - Required):
   - Sign up at https://huggingface.co/join (FREE)
   - Generate API token: https://huggingface.co/settings/tokens
   - No Pro subscription needed for MVP
   - No model approvals needed (using free models)

2. **AWS Account** (For EC2 Deployment):
   - Create AWS account: https://aws.amazon.com/
   - Set up IAM user with EC2 permissions only
   - No S3 buckets needed
   - No IAM roles needed
   - Launch EC2 t3.medium instance (~$30/month)

3. **Local Development** (Optional - for testing):
   - Python 3.10+
   - Docker (optional)
   - Git

### Local Development Setup (FREE)

```bash
# Clone repository
git clone <repository-url>
cd redteaming-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir -p data/reports data/logs data/faiss_index

# Create .env file with FREE models
cat > .env << EOF
HUGGINGFACE_API_KEY=hf_your_key_here
HF_LLM_MODEL=google/flan-t5-base
HF_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
RESULTS_PATH=./data/reports
LOGS_PATH=./data/logs
FAISS_INDEX_PATH=./data/faiss_index
STOP_TEST=0
AUTHORIZED_TOKENS=test_token_123
EOF

# Run application
python -m uvicorn app:app --host 0.0.0.0 --port 8080

# Test it
curl http://localhost:8080/health
```

### Testing Your First Mission

```bash
# Start a red-teaming mission
curl -X POST http://localhost:8080/missions \
  -H "Content-Type: application/json" \
  -d '{
    "target_system_url": "https://your-target-api.com/chat",
    "attack_categories": ["prompt_injection", "jailbreak"],
    "max_prompts": 10,
    "authorization_token": "test_token_123"
  }'

# Check mission status (use mission_id from response)
curl http://localhost:8080/missions/{mission_id}
```

## References

- Google Flan-T5 Models: https://huggingface.co/google/flan-t5-base
- Sentence Transformers: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- Hugging Face Inference API (Free): https://huggingface.co/docs/api-inference/
- Hugging Face Free Tier: https://huggingface.co/pricing
- FAISS Documentation: https://github.com/facebookresearch/faiss
- FastAPI Documentation: https://fastapi.tiangolo.com/
- AWS EC2 Pricing: https://aws.amazon.com/ec2/pricing/
- AWS Free Tier: https://aws.amazon.com/free/
- OWASP LLM Security: https://owasp.org/www-project-top-10-for-large-language-model-applications/
