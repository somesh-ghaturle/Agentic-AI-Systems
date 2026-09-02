# Quickstart Guide

Get the Agentic-AI-Systems repository running locally and deployed in under 30 minutes.

---

## Prerequisites

| Tool | Version | Purpose | Install Command |
|------|---------|---------|-----------------|
| Python | 3.9+ (3.10+ for `graph-agent`, `multi-agent-debate`, and `e2e-agent`; 3.11 for the `e2e-agent` Docker image) | Run examples | `brew install python` (macOS) / `sudo apt install python3` (Ubuntu) |
| pip | Latest | Python package manager | `python3 -m ensurepip --upgrade` |
| Terraform | 1.6+ | Infrastructure as code | `brew install terraform` (macOS) / See [HashiCorp docs](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli) |
| Git | Latest | Version control | `brew install git` / `sudo apt install git` |

**Verify your environment:**
```bash
python3 --version        # Should be 3.9 or higher
terraform version        # Should be 1.6 or higher
git --version
```

---

## Step 1: Clone and Set Up

```bash
# Clone the repository
git clone https://github.com/somesh-ghaturle/Agentic-AI-Systems.git
cd Agentic-AI-Systems

# Check the repository structure
ls -la
```

You should see:
```
Agentic-AI-Systems/
├── README.md
├── examples/          # Runnable agent examples
├── infra/            # Terraform deployments (AWS/Azure/GCP/Snowflake)
├── docs/             # Architecture and governance
└── tests/            # Test suites
```

---

## Step 2: Run an Agent Locally (No Cloud, No Dependencies)

The `hermes-agent` demonstrates the **write boundary** — the core security pattern of this repository.

### Try the Write Boundary

```bash
# Run without approval (should stop at the boundary)
python3 examples/hermes-agent/agent.py "restart the billing service"
```

**Expected output:**
```
trace   60d7c93b22af4c2aa0840367030695f3
intent  act → act()
status  awaiting approval
write   restart_service(service='billing')
why     Service 'billing' reports healthy=True; a restart clears the connection pool and takes about 40 seconds.
digest  9ef8f9b497df3e68...
next    re-run with --approve to authorise exactly this action
```

The agent **stopped** before executing the write action. This is the write boundary in action.

### Authorize the Action

```bash
# Re-run with approval flag
python3 examples/hermes-agent/agent.py "restart the billing service" --approve
```

**Expected output:**
```
trace   60d7c93b22af4c2aa0840367030695f3
intent  act → act()
status  approved
write   restart_service(service='billing')
result  Service 'billing' restarted successfully
```

The action only executes when **explicitly approved**.

### Explore More

```bash
# See all available commands
python3 examples/hermes-agent/agent.py --help

# Try a read-only action (no approval needed)
python3 examples/hermes-agent/agent.py "what is the status of the billing service"

# Try another write action
python3 examples/hermes-agent/agent.py "update the config file"
```

---

## Step 3: Verify the Write Boundary with Trace Evaluation

The `trace-eval` example proves that **output-only evaluation misses critical security gaps**.

```bash
# Run the trace evaluator
python3 examples/trace-eval/eval.py
```

**What this does:**
1. Scores the same agent runs **twice**:
   - One grader reads the **final answer** (output)
   - One grader reads the **full trace** (every step taken)
2. Compares the scores to find discrepancies

**Expected output:**
```
Scored 100 runs...
Found 3 discrepancies where output grader scored PASS but production service was restarted:
  - Run 42: Output said "service is healthy", trace showed restart_service() called
  - Run 87: Output said "no action taken", trace showed write operation
  - Run 91: Output was helpful, trace showed unauthorized state change

Conclusion: Output-only evaluation CANNOT detect write boundary bypasses.
Trace-level evaluation is REQUIRED for security.
```

**Key insight:** If you only evaluate the final answer, you cannot detect when an agent performs an unauthorized write action. The trace contains the evidence.

---

## Step 4: Deploy to AWS Dev Environment

This deploys the **full agentic architecture** to AWS using Terraform.

### Prepare AWS Credentials

```bash
# Install AWS CLI
git -C /tmp clone --depth 1 https://github.com/aws/aws-cli.git && \
cd /tmp/aws-cli && \
python3 -m pip install -r requirements.txt --user && \
cd /tmp && rm -rf aws-cli

# Configure AWS credentials (requires AWS account)
aws configure
# Enter: AWS Access Key ID, Secret Access Key, default region (e.g., us-east-1), output format (json)

# Verify
aws sts get-caller-identity
```

### Deploy Infrastructure

```bash
# Build the handler packages FIRST. Every module reads its zip at plan time to compute a
# deployment hash, so a tree whose packages are unbuilt cannot be planned.
infra/terraform-aws/src/build.sh

# The environment root is envs/dev — the tree root holds no .tf files of its own.
cd infra/terraform-aws/envs/dev

cp terraform.tfvars.example terraform.tfvars   # then edit it
terraform init

terraform plan
terraform apply
```

**What gets deployed:**
| Component | AWS Service | Purpose |
|-----------|-------------|---------|
| Orchestrator | Step Functions | Coordinates agent workflows |
| Tools | Lambda | Executes read/write actions |
| State | DynamoDB | Stores execution state and approvals |
| Approval Gate | Lambda + DynamoDB | Enforces human approval for writes |
| Knowledge | OpenSearch Serverless | Vector search for RAG |
| Archive | S3 | Stores audit logs and provenance |
| Observability | CloudWatch | Metrics, logs, and alarms |

### Verify Deployment

```bash
# List deployed resources
terraform state list

# Check Step Functions state machine
aws stepfunctions list-state-machines

# Check Lambda functions
aws lambda list-functions

# Check DynamoDB tables
aws dynamodb list-tables
```

### Test the Deployed System

```bash
# Find the API Gateway URL (output after apply)
API_URL=$(terraform output -raw api_gateway_url)

# Send a request that triggers a write action
curl -X POST \
  $API_URL/request \
  -H "Content-Type: application/json" \
  -d '{"prompt": "restart the billing service"}'
```

**Expected response:**
```json
{
  "trace_id": "abc123...",
  "status": "awaiting_approval",
  "action": "restart_service",
  "args": {"service": "billing"},
  "next": "POST /approve with token to authorize"
}
```

### Clean Up (When Done)

```bash
# Destroy the dev environment. Run from infra/terraform-aws/envs/dev.
#
# No -auto-approve. This is the one command in this guide that deletes data, and the
# archive bucket and approvals table are the audit trail — read the plan before confirming.
terraform destroy

# Verify cleanup
aws stepfunctions list-state-machines  # Should be empty
```

---

## Step 5: Deploy to Azure (Alternative)

```bash
# Build the handler packages first, as with AWS.
infra/terraform-azure/src/build.sh

# The environment root is envs/dev.
cd infra/terraform-azure/envs/dev

# Initialize
terraform init

# Configure Azure credentials
export ARM_CLIENT_ID="your-client-id"
export ARM_CLIENT_SECRET="your-client-secret"
export ARM_SUBSCRIPTION_ID="your-subscription-id"
export ARM_TENANT_ID="your-tenant-id"

# Plan and apply dev environment
terraform plan
terraform apply
```

**Note:** Azure's write boundary uses Entra ID audit alerts as a second line of defense. See [THREAT-MODEL.md](docs/THREAT-MODEL.md) for details.

---

## Step 6: Deploy to GCP (Alternative)

```bash
# Build the handler packages first, as with AWS.
infra/terraform-gcp/src/build.sh

# The environment root is envs/dev.
cd infra/terraform-gcp/envs/dev

# Initialize
terraform init

# Configure GCP credentials
export GOOGLE_CLOUD_KEYFILE_JSON="path/to/service-account.json"

# Plan and apply dev environment
terraform plan
terraform apply
```

**Note:** GCP uses IAM Deny policies — the strongest write boundary of the three infrastructure clouds, because a deny rule evaluates before allow policies and a later broad grant cannot reopen the path.

---

## Step 6b: Deploy to Snowflake (Alternative)

Snowflake is **not a fourth cloud** — it is a data platform running on one of the other three.
Pick it when the agent's tools are already queries over data you keep in Snowflake. See
[infra/CHOOSING-A-TREE.md](infra/CHOOSING-A-TREE.md) §0 for the trade, the largest part of
which is that approvals are *polled* rather than called back.

```bash
# No packages to build — this tree's handler logic is SQL stored procedures.
cd infra/terraform-snowflake/envs/dev

cp terraform.tfvars.example terraform.tfvars   # then edit it
terraform init

terraform plan
terraform apply
```

**Authentication is different here.** The other three trees inherit an ambient identity from
the platform. Snowflake has none, so this tree uses workload identity federation — run the
apply from a context that already holds a federated identity. There is deliberately no
private key anywhere in the configuration; see
[infra/terraform-snowflake/HOW-TO-DEPLOY.md](infra/terraform-snowflake/HOW-TO-DEPLOY.md).

**What gets deployed:**
| Component | Snowflake Object | Purpose |
|-----------|------------------|---------|
| Orchestrator | Task | Sweeps for approved proposals — a scheduler, not a workflow engine |
| Tools | Stored procedures | `EXECUTE AS OWNER`, so no caller role holds a table privilege |
| State | Hybrid tables | Row-locked execution state and approvals |
| Approval Gate | Procedures + role grants | The write boundary is the role graph |
| Knowledge | Cortex Search | Indexes a query, not a copy — nothing to fall behind |
| Archive | Table + internal stage | Cold traces and exports |
| Observability | Event table + traces | A stored procedure has no stdout anyone will read |

**Note:** the write boundary here is role inheritance, which makes it the easiest of the four
to break with a valid grant. Rehearse it after applying — authenticate as the orchestrator and
confirm a write procedure refuses you.

---

## Step 7: Run All Examples Locally

All examples run without cloud dependencies (except where noted):

| Example | Command | Dependencies | Purpose |
|---------|---------|--------------|---------|
| hermes-agent | `python3 agent.py "query"` | None | Write boundary in app code |
| trace-eval | `python3 eval.py` | None | Trace-level evaluation |
| starter-agent | `python3 agent.py "query"` | None | Minimal agent loop |
| harness-agent | `python3 agent.py "query"` | None | Continuity across context windows |
| checkpoint-agent | `python3 agent.py "deploy-model"` | None | Resuming after a crash, idempotently |
| multi-agent-debate | `python3 agent.py` | None | Several agents argue; none of them approves |
| context-compaction | `python3 compact.py` | None | Context management |
| graph-agent | `python3 graph_agent.py "query"` | LangGraph | Read/write split as a graph |
| e2e-agent | `python3 app.py` | FastAPI | Full HTTP agent with tracing |
| rag-faiss | `python3 build_index.py` then `query.py` | faiss-cpu, sentence-transformers | Local vector search |
| rag-langchain | `python3 build_index.py` then `query_and_answer.py` | langchain, sentence-transformers | LangChain vector search |
| langchain-agent | `python3 agent.py "query"` | langchain | Minimal LangChain agent |
| ray-orchestrator | `python3 orchestrator.py` | ray | Parallel task execution |

---

## Step 8: Development Workflow

### Install Pre-commit Hooks (Optional but Recommended)

```bash
# Install pre-commit
python3 -m pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Run Tests

```bash
# Run all example tests
python3 -m unittest discover -s tests -v

# Run infrastructure tests
for cloud in aws azure gcp; do
  python3 -m unittest discover -s infra/terraform-$cloud/tests -v
done
```

### Make Changes

1. Edit code in `examples/` or `infra/`
2. Update tests if needed
3. Run `pre-commit run` (if installed)
4. Run `python3 -m unittest discover -s tests`
5. For Terraform: `terraform validate` and `terraform fmt -check`

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | `pip install -r examples/<name>/requirements.txt` |
| Terraform: "no such file or directory" | Run from the correct directory (e.g., `infra/terraform-aws/`) |
| AWS: "InvalidClientTokenId" | Verify AWS credentials with `aws sts get-caller-identity` |
| Azure: "Authentication Failed" | Verify `ARM_*` environment variables are set |
| GCP: "Permission denied" | Verify `GOOGLE_CLOUD_KEYFILE_JSON` points to valid service account |
| Python: "SyntaxError" | Check Python version is 3.9+ |

### Get Help

- **FAQ:** [docs/FAQ.md](docs/FAQ.md) — including the three questions whose common answer is wrong
- **Architecture:** [docs/agentic-system-architecture/](docs/agentic-system-architecture/README.md)
- **Threat Model:** [docs/THREAT-MODEL.md](docs/THREAT-MODEL.md)
- **How to Recover:** [docs/HOW-TO-RECOVER.md](docs/HOW-TO-RECOVER.md) — locked or lost Terraform state, a corrupted execution-state row, a stuck approval claim, per cloud
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **GitHub Issues:** [github.com/somesh-ghaturle/Agentic-AI-Systems/issues](https://github.com/somesh-ghaturle/Agentic-AI-Systems/issues)

---

## Next Steps

Once you've completed this quickstart:

1. **Read the architecture docs:** [docs/agentic-system-architecture/](docs/agentic-system-architecture/README.md)
2. **Review the threat model:** [docs/THREAT-MODEL.md](docs/THREAT-MODEL.md)
3. **Try deploying to production:** See the `envs/prod` directories in each cloud tree
4. **Explore multi-agent patterns:** [docs/agentic-system-architecture/ARCHITECTURE-PATTERNS.md](docs/agentic-system-architecture/ARCHITECTURE-PATTERNS.md)
5. **Contribute:** See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Security Notes

⚠️ **IMPORTANT:** The write boundary is **enforced at the identity platform level**, not by the prompt or model behavior. This means:

- Even if a model is compromised or misbehaves, it **cannot** perform write actions without explicit human approval
- The approval is **bound to a specific action fingerprint** — changing any parameter invalidates the approval
- Approval tokens **expire after 24 hours** by default
- All write actions are **logged and auditable**

See [docs/THREAT-MODEL.md](docs/THREAT-MODEL.md) for the full security analysis.
