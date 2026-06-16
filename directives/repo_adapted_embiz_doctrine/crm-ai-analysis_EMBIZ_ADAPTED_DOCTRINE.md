# crm-ai-analysis EMBIZ ADAPTED DOCTRINE

## Source Material Read

**Repository:** crm-ai-analysis  
**Location:** `/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis`

**Core Components Identified:**
- FastAPI-based REST API for CRM data analysis
- Text-to-SQL RAG system using LangChain and LangGraph
- SQL injection detection agent
- Chat message history management with SQLAlchemy
- Customer Lifetime Value (CLTV) prediction using BetaGeoFitter and GammaGammaFitter
- RFM (Recency, Frequency, Monetary) segmentation
- DBT integration for data transformation
- Streamlit UI for data querying and entry
- PostgreSQL database with medallion architecture (source/staging/analytics views)
- Pydantic schemas for data validation

**Key Technologies:**
- LangChain/LangGraph for agentic workflows
- OpenAI GPT-4o-mini for LLM operations
- SQLAlchemy ORM
- Lifetimes library for predictive analytics
- FireDucks pandas for performance
- DBT for data modeling

## What This Repo Contributes To EMBIZ

This repository provides **customer intelligence and conversational data access** capabilities that EMBIZ can adapt for:

1. **Customer Relationship Management** - Track embroidery customer interactions, order history, and engagement patterns
2. **Natural Language Database Queries** - Allow agents to query customer/order data using plain English instead of SQL
3. **Customer Lifetime Value Prediction** - Forecast which embroidery customers are most valuable for retention efforts
4. **RFM Segmentation** - Identify high-value customers, at-risk customers, and re-engagement opportunities
5. **Conversational Analytics** - Enable Maya/Madeline/Morgan to answer business questions about sales, customers, products
6. **SQL Injection Protection** - Secure agent that validates queries before database execution
7. **Chat History Persistence** - Maintain conversation context across agent interactions

**EMBIZ-Specific Value:**
- Replace "sales agents" with embroidery order tracking
- Replace "products" with embroidery designs/services
- Replace "accounts" with embroidery customers (businesses, individuals, repeat clients)
- Adapt CLTV models to predict embroidery customer retention and order frequency
- Enable agents to answer: "Which customers haven't ordered in 90 days?" or "What's our average order value by customer segment?"

## EMBIZ-Specific Adaptation

### Database Schema Adaptation

**Original CRM Tables → EMBIZ Tables:**

| Original | EMBIZ Equivalent | Purpose |
|----------|------------------|---------|
| `sales_pipeline_source` | `embroidery_orders_source` | Track orders through workflow stages |
| `accounts_source` | `customers_source` | Customer business/contact info |
| `products_source` | `designs_services_source` | Embroidery designs, digitizing, products |
| `sales_teams_source` | `staff_source` | Maya, Madeline, Morgan assignments |
| `deal_stage` | `order_stage` | Inquiry → Quote → Digitizing → Production → Delivered |

**New EMBIZ Fields:**
- `digitizing_required` (boolean)
- `file_formats_delivered` (array: PES, DST, EXP, etc.)
- `stitch_count` (integer)
- `thread_colors` (integer)
- `garment_type` (string)
- `rush_order` (boolean)
- `human_approval_timestamp` (datetime)

### Agent Role Mapping

**Text-to-SQL Agent → "Meredith" (Analytics Agent)**
- Handles natural language queries about customer data
- Generates SQL, validates for injection, executes safely
- Returns results in conversational format

**SQL Injection Validator → "Mackenzie" (Security Agent)**
- Pre-validates all database queries
- Blocks malicious patterns
- Logs security events to Slack

**Customer Segmentation → "Mila" (Customer Intelligence Agent)**
- Runs RFM analysis on embroidery customers
- Identifies at-risk customers (low recency)
- Suggests re-engagement campaigns

**CLTV Prediction → "Melanie" (Forecasting Agent)**
- Predicts customer lifetime value
- Identifies high-value customers for VIP treatment
- Forecasts order frequency

### Prompt Adaptations

**Original System Prompt (Text-to-SQL):**
```
You are an agent designed to interact with a SQL database.
Given the input question, create a syntactically correct {dialect} query...
```

**EMBIZ Adapted Prompt:**
```
You are Meredith, an embroidery business analytics agent.
You help answer questions about customers, orders, designs, and business performance.

Available data:
- embroidery_orders: Order history with stages (Inquiry, Quote, Digitizing, Production, Delivered)
- customers: Business and individual customer information
- designs_services: Embroidery designs, digitizing services, products
- staff: Maya (sales), Madeline (digitizing), Morgan (production), etc.

When answering:
- Use embroidery-specific terminology (stitch count, thread colors, garment types)
- Never claim files exist unless verified on disk
- Respect human approval requirements for customer contact
- Today's date is {today_date}

Example questions you can answer:
- "Which customers haven't ordered in 90 days?"
- "What's our average stitch count by customer segment?"
- "Show me all orders waiting for digitizing approval"
```

### RFM Metric Adaptations

**Original Metrics:**
- Recency: Days since last purchase
- Frequency: Number of purchases
- Monetary: Total revenue

**EMBIZ Metrics:**
- **Recency:** Days since last embroidery order
- **Frequency:** Number of orders (weight digitizing orders higher)
- **Monetary:** Total order value + digitizing fees
- **Custom Metric - Complexity Score:** Average stitch count × thread colors (identifies high-skill customers)

### CLTV Model Adaptations

**Training Data Requirements:**
- Minimum 6 months of order history
- Filter out one-time event orders (weddings, etc.) unless repeat customer
- Weight rush orders higher (indicates urgency/value)
- Separate B2B (corporate apparel) from B2C (individual) models

**Prediction Outputs:**
- Expected orders in next 12 months
- Expected revenue in next 12 months
- Probability customer is still active
- Recommended retention actions

## Assigned Agent Ownership

| Agent | Role | Responsibilities |
|-------|------|------------------|
| **Meredith** | Analytics/Text-to-SQL | Natural language database queries, report generation |
| **Mackenzie** | Security Validator | SQL injection detection, query sanitization |
| **Mila** | Customer Intelligence | RFM segmentation, customer health scoring |
| **Melanie** | Forecasting | CLTV prediction, order frequency forecasting |
| **Madeline** | Digitizing Coordinator | Tracks digitizing workflow, approvals |
| **Maya** | Customer Relations | Uses analytics to inform customer outreach |
| **Morgan** | Production Coordinator | Uses analytics for capacity planning |

**Shared Responsibilities:**
- All agents can request analytics from Meredith
- Mackenzie validates all database operations
- Mila provides customer context to Maya/Madeline/Morgan

## Local Skill / Knowledge Library Integration

**Storage Locations:**

```
/root/embroidery_business_agent_system/
├── analytics/
│   ├── models/
│   │   ├── beta_geo_fitter.pkl          # BG/NBD model for order prediction
│   │   ├── gamma_gamma_fitter.pkl       # Monetary value model
│   │   └── rfm_segments.json            # Current customer segments
│   ├── queries/
│   │   ├── common_analytics.sql         # Pre-built queries
│   │   └── table_metadata.json          # Schema documentation for LLM
│   └── reports/
│       └── daily_customer_health.json   # Automated reports
├── skills/
│   ├── text_to_sql/
│   │   ├── skill.py                     # Meredith's core skill
│   │   ├── examples.json                # Few-shot examples
│   │   └── table_descriptions.json      # EMBIZ schema docs
│   ├── sql_injection_detection/
│   │   ├── skill.py                     # Mackenzie's validator
│   │   └── patterns.json                # Known attack patterns
│   ├── rfm_segmentation/
│   │   ├── skill.py                     # Mila's segmentation
│   │   └── segment_definitions.json     # RFM thresholds
│   └── cltv_prediction/
│       ├── skill.py                     # Melanie's forecasting
│       └── model_config.json            # Model parameters
└── knowledge/
    ├── customer_segments.md             # Segment definitions
    ├── analytics_playbook.md            # How to use analytics
    └── sql_schema.md                    # Database documentation
```

**Integration with OpenClaw:**

```
/root/.openclaw/workspace/
├── analytics_cache/
│   ├── query_results/                   # Cached query results (1 hour TTL)
│   └── model_predictions/               # Cached CLTV predictions (24 hour TTL)
└── conversation_history/
    └── analytics_sessions/              # Meredith's chat history
```

## Runtime Rules

### Query Execution Rules

1. **All database queries MUST:**
   - Pass through Mackenzie (SQL injection validator) first
   - Be logged to `/var/log/embiz/analytics_queries.log`
   - Include agent name and timestamp
   - Respect row limits (default 100, max 1000)

2. **Text-to-SQL workflow:**
   ```
   User Question → Meredith (generate SQL) → Mackenzie (validate) → 
   Execute → Format Results → Return to User
   ```

3. **Security validations:**
   - No DROP, DELETE, UPDATE, INSERT statements
   - No TRUNCATE or ALTER operations
   - No access to system tables
   - No UNION-based injection patterns
   - No comment-based injection (-- or /* */)

4. **Performance limits:**
   - Query timeout: 30 seconds
   - Result set limit: 1000 rows
   - Concurrent queries: 3 max per agent

### Customer Data Privacy

1. **PII Protection:**
   - Never log full customer names in plain text
   - Mask email addresses in logs (j***@example.com)
   - Mask phone numbers (***-***-1234)
   - Use customer_id in inter-agent messages

2. **Slack notifications:**
   - Analytics summaries only (no individual customer details)
   - Aggregate metrics only ("15 customers at risk")
   - Use customer IDs, not names

### Model Retraining Rules

1. **RFM Segmentation:**
   - Recalculate daily at 2 AM
   - Requires minimum 50 customers with 2+ orders
   - Alert if segment distribution changes >20%

2. **CLTV Models:**
   - Retrain monthly on 1st at 3 AM
   - Requires minimum 6 months historical data
   - Validate predictions against actual orders
   - Alert if model accuracy drops below 70%

3. **Model versioning:**
   - Keep last 3 model versions
   - Tag with training date
   - Log training metrics to `/var/log/embiz/model_training.log`

### Human Approval Requirements

**Analytics operations that require approval:**
- Bulk customer contact based on segmentation (Maya must get approval)
- Exporting customer lists
- Sharing analytics with external parties
- Modifying RFM segment definitions
- Changing CLTV model parameters

**Auto-approved operations:**
- Read-only queries
- Report generation
- Model predictions
- Segment calculations

## Required Files / Configs

### Database Configuration

**File:** `/root/embroidery_business_agent_system/config/analytics_db.env`

```bash
# PostgreSQL Connection
DB_URL=postgresql://embiz_analytics:${DB_PASSWORD}@localhost:5432/embiz_analytics
DB_SCHEMA=analytics
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Query Limits
QUERY_TIMEOUT_SECONDS=30
MAX_RESULT_ROWS=1000
MAX_CONCURRENT_QUERIES=3

# Model Paths
BETA_GEO_MODEL_PATH=/root/embroidery_business_agent_system/analytics/models/beta_geo_fitter.pkl
GAMMA_GAMMA_MODEL_PATH=/root/embroidery_business_agent_system/analytics/models/gamma_gamma_fitter.pkl

# DBT Configuration
DBT_PATH=/root/embroidery_business_agent_system/analytics/dbt
DBT_PROFILES_DIR=/root/embroidery_business_agent_system/analytics/dbt/profiles

# OpenAI Configuration
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.0
OPENAI_MAX_TOKENS=2000

# Logging
ANALYTICS_LOG_PATH=/var/log/embiz/analytics_queries.log
MODEL_LOG_PATH=/var/log/embiz/model_training.log
```

### Table Metadata for LLM

**File:** `/root/embroidery_business_agent_system/analytics/queries/table_metadata.json`

```json
{
  "tables": [
    {
      "name": "embroidery_orders",
      "description": "All embroidery orders from inquiry to delivery",
      "columns": [
        {"name": "order_id", "type": "string", "description": "Unique order identifier"},
        {"name": "customer_id", "type": "string", "description": "Customer identifier"},
        {"name": "order_stage", "type": "string", "description": "Inquiry|Quote|Digitizing|Production|Delivered"},
        {"name": "order_date", "type": "date", "description": "Date order was placed"},
        {"name": "delivery_date", "type": "date", "description": "Date order was delivered"},
        {"name": "order_value", "type": "float", "description": "Total order value in USD"},
        {"name": "digitizing_required", "type": "boolean", "description": "Whether digitizing was needed"},
        {"name": "digitizing_fee", "type": "float", "description": "Digitizing service fee"},
        {"name": "stitch_count", "type": "integer", "description": "Total stitches in design"},
        {"name": "thread_colors", "type": "integer", "description": "Number of thread colors"},
        {"name": "garment_type", "type": "string", "description": "Type of garment (hat, shirt, jacket, etc.)"},
        {"name": "rush_order", "type": "boolean", "description": "Whether rush service was requested"},
        {"name": "assigned_agent", "type": "string", "description": "Staff member handling order"}
      ]
    },
    {
      "name": "customers",
      "description": "Customer information for businesses and individuals",
      "columns": [
        {"name": "customer_id", "type": "string", "description": "Unique customer identifier"},
        {"name": "customer_name", "type": "string", "description": "Business or individual name"},
        {"name": "customer_type", "type": "string", "description": "B2B|B2C"},
        {"name": "first_order_date", "type": "date", "description": "Date of first order"},
        {"name": "last_order_date", "type": "date", "description": "Date of most recent order"},
        {"name": "total_orders", "type": "integer", "description": "Lifetime order count"},
        {"name": "total_revenue", "type": "float", "description": "Lifetime revenue"},
        {"name": "rfm_segment", "type": "string", "description": "RFM segment (Champions, At Risk, etc.)"},
        {"name": "predicted_cltv", "type": "float", "description": "Predicted 12-month customer lifetime value"},
        {"name": "office_location", "type": "string", "description": "Customer location"}
      ]
    },
    {
      "name": "designs_services",
      "description": "Embroidery designs and digitizing services catalog",
      "columns": [
        {"name": "design_id", "type": "string", "description": "Unique design identifier"},
        {"name": "design_name", "type": "string", "description": "Design name"},
        {"name": "design_category", "type": "string", "description": "Category (logo, text, custom, etc.)"},
        {"name": "base_price", "type": "float", "description": "Base price for design"},
        {"name": "avg_stitch_count", "type": "integer", "description": "Average stitch count"},
        {"name": "digitizing_complexity", "type": "string", "description": "Simple|Medium|Complex"}
      ]
    }
  ]
}
```

### Few-Shot Examples for Text-to-SQL

**File:** `/root/embroidery_business_agent_system/skills/text_to_sql/examples.json`

```json
{
  "examples": [
    {
      "question": "Which customers haven't ordered in 90 days?",
      "sql": "SELECT customer_id, customer_name, last_order_date, CURRENT_DATE - last_order_date AS days_since_order FROM customers WHERE CURRENT_DATE - last_order_date > 90 ORDER BY days_since_order DESC LIMIT 100;",
      "explanation": "Find customers with last_order_date more than 90 days ago"
    },
    {
      "question": "What's our average order value by customer segment?",
      "sql": "SELECT rfm_segment, AVG(order_value) AS avg_order_value, COUNT(*) AS order_count FROM embroidery_orders JOIN customers ON embroidery_orders.customer_id = customers.customer_id GROUP BY rfm_segment ORDER BY avg_order_value DESC;",
      "explanation": "Group orders by RFM segment and calculate average value"
    },
    {
      "question": "Show me all orders waiting for digitizing approval",
      "sql": "SELECT order_id, customer_name, order_date, stitch_count, thread_colors FROM embroidery_orders JOIN customers ON embroidery_orders.customer_id = customers.customer_id WHERE order_stage = 'Digitizing' AND digitizing_required = true ORDER BY order_date ASC LIMIT 100;",
      "explanation": "Filter orders in Digitizing stage that require digitizing"
    },
    {
      "question": "What's the total revenue from rush orders this month?",
      "sql": "SELECT SUM(order_value) AS total_rush_revenue, COUNT(*) AS rush_order_count FROM embroidery_orders WHERE rush_order = true AND order_date >= DATE_TRUNC('month', CURRENT_DATE);",
      "explanation": "Sum order values for rush orders in current month"
    },
    {
      "question": "Which customers have the highest predicted lifetime value?",
      "sql": "SELECT customer_id, customer_name, predicted_cltv, total_orders, total_revenue FROM customers ORDER BY predicted_cltv DESC LIMIT 20;",
      "explanation": "Sort customers by predicted CLTV descending"
    }
  ]
}
```

### RFM Segment Definitions

**File:** `/root/embroidery_business_agent_system/skills/rfm_segmentation/segment_definitions.json`

```json
{
  "segments": {
    "Champions": {
      "description": "Best customers - ordered recently, frequently, and spend the most",
      "rfm_criteria": {"recency": [4, 5], "frequency": [4, 5], "monetary": [4, 5]},
      "action": "Reward with VIP treatment, early access to new designs, loyalty discounts"
    },
    "Loyal Customers": {
      "description": "Order regularly with good spend",
      "rfm_criteria": {"recency": [3, 5], "frequency": [3, 5], "monetary": [3, 5]},
      "action": "Upsell premium services, request referrals, maintain engagement"
    },
    "Potential Loyalists": {
      "description": "Recent customers with potential to become loyal",
      "rfm_criteria": {"recency": [4, 5], "frequency": [1, 3], "monetary": [1, 3]},
      "action": "Offer membership, recommend related designs, build relationship"
    },
    "At Risk": {
      "description": "Used to order frequently but haven't recently",
      "rfm_criteria": {"recency": [1, 2], "frequency": [3, 5], "monetary": [3, 5]},
      "action": "Send re-engagement campaign, special offers, check satisfaction"
    },
    "Hibernating": {
      "description": "Last order was long ago, low frequency",
      "rfm_criteria": {"recency": [1, 2], "frequency": [1, 2], "monetary": [1, 2]},
      "action": "Win-back campaign, survey for feedback, special reactivation offer"
    },
    "Lost": {
      "description": "Lowest recency, frequency, and monetary scores",
      "rfm_criteria": {"recency": [1], "frequency": [1], "monetary": [1]},
      "action": "Aggressive win-back or remove from active marketing"
    }
  },
  "scoring": {
    "recency_days": {
      "5": "0-30 days",
      "4": "31-60 days",
      "3": "61-90 days",
      "2": "91-180 days",
      "1": "180+ days"
    },
    "frequency_orders": {
      "5": "10+ orders",
      "4": "6-9 orders",
      "3": "3-5 orders",
      "2": "2 orders",
      "1": "1 order"
    },
    "monetary_value": {
      "5": "$5000+",
      "4": "$2000-$4999",
      "3": "$500-$1999",
      "2": "$100-$499",
      "1": "$0-$99"
    }
  }
}
```

## Commands / Checks

### Analytics Service Commands

```bash
# Start analytics API
cd /root/embroidery_business_agent_system/analytics/api
python main.py

# Run RFM segmentation
python -m skills.rfm_segmentation.skill --recalculate

# Train CLTV models
python -m skills.cltv_prediction.skill --train --validate

# Run DBT transformations
cd /root/embroidery_business_agent_system/analytics/dbt
dbt run

# Generate DBT documentation
dbt docs generate
dbt docs serve --port 8080

# Test database connection
python -c "from core.database import engine; print(engine.execute('SELECT 1').scalar())"

# Validate SQL injection detector
python -m skills.sql_injection_detection.skill --test

# Export customer segments
python -m skills.rfm_segmentation.skill --export /tmp/segments.json
```

### Health Checks

```bash
# Check analytics API health
curl http://localhost:8200/api/health

# Check database connectivity
psql -h localhost -U embiz_analytics -d embiz_analytics -c "SELECT COUNT(*) FROM embroidery_orders;"

# Check model files exist
ls -lh /root/embroidery_business_agent_system/analytics/models/*.pkl

# Check query logs
tail -f /var/log/embiz/analytics_queries.log

# Check model training logs
tail -f /var/log/embiz/model_training.log

# Verify DBT models compiled
ls -lh /root/embroidery_business_agent_system/analytics/dbt/target/compiled/

# Test text-to-SQL with example
curl -X POST http://localhost:8200/api/text-to-sql/ \
  -H "Content-Type: application/json" \
  -d '{"message_history_id": 1, "query": "Which customers haven'\''t ordered in 90 days?"}'

# Test SQL injection detection
curl http://localhost:8200/api/verify-sql-injection/SELECT%20*%20FROM%20customers

# Check RFM segment distribution
python -c "from skills.rfm_segmentation.skill import get_segment_distribution; print(get_segment_distribution())"
```

### Monitoring Commands

```bash
# Monitor active queries
psql -h localhost -U embiz_analytics -d embiz_analytics -c "SELECT pid, query, state, query_start FROM pg_stat_activity WHERE datname = 'embiz_analytics';"

# Check query performance
grep "SLOW QUERY" /var/log/embiz/analytics_queries.log | tail -20

# Monitor model prediction accuracy
python -m skills.cltv_prediction.skill --validate --report

# Check cache hit rates
python -c "from analytics.cache import get_cache_stats; print(get_cache_stats())"

# Alert on security events
grep "SQL_INJECTION_BLOCKED" /var/log/embiz/analytics_queries.log | tail -10
```

## Security Restrictions

### Database Access Control

1. **Read-only access for analytics:**
   - Analytics database user has SELECT-only privileges
   - No INSERT, UPDATE, DELETE, DROP permissions
   - No access to system catalogs or pg_* tables

2. **Query validation (Mackenzie enforces):**
   - Block all DML statements (INSERT, UPDATE, DELETE)
   - Block all DDL statements (CREATE, ALTER, DROP, TRUNCATE)
   - Block UNION-based injection attempts
   - Block comment-based injection (-- and /* */)
   - Block stacked queries (semicolon separation)
   - Block time-based blind injection (SLEEP, WAITFOR)

3. **SQL injection patterns to block:**
   ```python
   BLOCKED_PATTERNS = [
       r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE)",
       r"(UNION|UNION\s+ALL)\s+SELECT",
       r"--\s*$",
       r"/\*.*\*/",
       r"(SLEEP|WAITFOR|BENCHMARK)\s*\(",
       r"(EXEC|EXECUTE)\s+",
       r"xp_cmdshell",
       r"INTO\s+(OUTFILE|DUMPFILE)",
       r"LOAD_FILE\s*\(",
       r"(AND|OR)\s+1\s*=\s*1",
       r"'\s*(OR|AND)\s+'1'\s*=\s*'1"
   ]
   ```

### API Security

1. **Rate limiting:**
   - 100 requests per minute per agent
   - 10 concurrent queries per agent
   - 1000 requests per hour per agent

2. **Authentication:**
   - All API requests require agent authentication token
   - Tokens stored in `/root/embroidery_business_agent_system/config/agent_tokens.json`
   - Tokens rotate every 30 days

3. **Input validation:**
   - Maximum query length: 1000 characters
   - Maximum result rows: 1000
   - Query timeout: 30 seconds
   - Sanitize all user inputs

### Data Privacy

1. **PII masking in logs:**
   - Customer names: "Customer #12345"
   - Email addresses: "j***@example.com"
   - Phone numbers: "***-***-1234"
   - Addresses: City/State only

2. **Slack notifications:**
   - Aggregate metrics only
   - No individual customer details
   - Use customer IDs, not names
   - Mask sensitive data

3. **Export restrictions:**
   - Customer lists require human approval
   - Maximum 100 customers per export
   - Log all exports with timestamp and agent
   - Exports auto-delete after 24 hours

### Model Security

1. **Model file permissions:**
   - Read-only for analytics service
   - Write-only for training process
   - No web-accessible paths

2. **Training data access:**
   - Training process runs as separate user
   - No direct database access from training scripts
   - Use exported CSV files only

3. **Model versioning:**
   - Keep last 3 versions only
   - Tag with training date and metrics
   - Validate before deployment

## Verification Checklist

### Pre-Deployment Checks

- [ ] PostgreSQL database created with correct schema
- [ ] Analytics user created with SELECT-only privileges
- [ ] Database connection string in `/root/embroidery_business_agent_system/config/analytics_db.env`
- [ ] Table metadata JSON file created and validated
- [ ] Few-shot examples JSON file created with EMBIZ-specific queries
- [ ] RFM segment definitions JSON file created
- [ ] Model directories created: `/root/embroidery_business_agent_system/analytics/models/`
- [ ] Log directories created: `/var/log/embiz/`
- [ ] DBT project initialized in `/root/embroidery_business_agent_system/analytics/dbt/`
- [ ] OpenAI API key configured
- [ ] Agent authentication tokens generated

### Functional Checks

- [ ] Analytics API starts without errors: `python main.py`
- [ ] Database connection successful: `SELECT 1` query works
- [ ] Text-to-SQL generates valid queries for test questions
- [ ] SQL injection detector blocks malicious patterns
- [ ] SQL injection detector allows safe queries
- [ ] RFM segmentation runs and produces segments
- [ ] CLTV models train successfully with sample data
- [ ] DBT models compile and run successfully
- [ ] Chat history persists across sessions
- [ ] Query results cached correctly
- [ ] Rate limiting enforces limits

### Security Checks

- [ ] SQL injection patterns blocked (test with `'; DROP TABLE customers; --`)
- [ ] DML statements blocked (test with `DELETE FROM customers`)
- [ ] DDL statements blocked (test with `DROP TABLE customers`)
- [ ] UNION injection blocked (test with `UNION SELECT * FROM pg_user`)
- [ ] Comment injection blocked (test with `SELECT * FROM customers -- comment`)
- [ ] Analytics user cannot INSERT/UPDATE/DELETE
- [ ] PII masked in logs (check `/var/log/embiz/analytics_queries.log`)
- [ ] API requires authentication token
- [ ] Rate limiting works (test with 101 requests in 1 minute)
- [ ] Query timeout enforces 30-second limit

### Data Quality Checks

- [ ] Minimum 50 customers with 2+ orders for RFM
- [ ] Minimum 6 months historical data for CLTV
- [ ] No NULL values in critical fields (customer_id, order_date)
- [ ] Date ranges valid (order_date <= delivery_date)
- [ ] Order values positive (order_value > 0)
- [ ] RFM scores in range 1-5
- [ ] Segment distribution reasonable (no segment >50%)

### Integration Checks

- [ ] Meredith can query database via text-to-SQL
- [ ] Mackenzie validates queries before execution
- [ ] Mila can access RFM segments
- [ ] Melanie can access CLTV predictions
- [ ] Maya can request customer analytics
- [ ] Madeline can query digitizing workflow
- [ ] Morgan can query production capacity
- [ ] Slack notifications sent for security events
- [ ] Agent bus messages formatted correctly

### Performance Checks

- [ ] Simple queries return in <1 second
- [ ] Complex queries return in <10 seconds
- [ ] Query timeout enforced at 30 seconds
- [ ] Cache hit rate >50% for repeated queries
- [ ] RFM calculation completes in <5 minutes
- [ ] CLTV training completes in <30 minutes
- [ ] DBT transformations complete in <10 minutes
- [ ] API handles 10 concurrent requests

## Build Tasks

### Initial Setup

```bash
# 1. Create database
sudo -u postgres psql -c "CREATE DATABASE embiz_analytics;"
sudo -u postgres psql -c "CREATE USER embiz_analytics WITH PASSWORD 'SECURE_PASSWORD';"
sudo -u postgres psql -c "GRANT CONNECT ON DATABASE embiz_analytics TO embiz_analytics;"

# 2. Create schema and grant permissions
sudo -u postgres psql embiz_analytics -c "CREATE SCHEMA analytics;"
sudo -u postgres psql embiz_analytics -c "GRANT USAGE ON SCHEMA analytics TO embiz_analytics;"
sudo -u postgres psql embiz_analytics -c "GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO embiz_analytics;"
sudo -u postgres psql embiz_analytics -c "ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO embiz_analytics;"

# 3. Create directory structure
mkdir -p /root/embroidery_business_agent_system/analytics/{models,