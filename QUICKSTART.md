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

**Expected output** (the trace ID differs every run):
```
trace   60d7c93b22af4c2aa0840367030695f3
intent  act → act()
status  awaiting approval
write   restart_service(service='billing')
why     Service 'billing' reports healthy=True; a restart clears the connection pool and takes about 40 seconds.
digest  9ef8f9b497df3e68…
next    re-run with --approve to authorise exactly this action
```

The agent **stopped** before executing the write action, and the command exits with status **2**.
That is the write boundary in action. The JSON lines printed above the summary are the trace
events. They go to stderr, so `2>/dev/null` hides them.

### Authorize the Action

```bash
# Re-run with approval flag
python3 examples/hermes-agent/agent.py "restart the billing service" --approve
```

**Expected output:**
```
trace   3b485ba4a6ff44ffa577c787c02510a1
intent  act → act()
status  executed
write   restart_service(service='billing')
why     Service 'billing' reports healthy=True; a restart clears the connection pool and takes about 40 seconds.
digest  9ef8f9b497df3e68…
by      demo-operator
result  {"restarted": "billing", "restarts_today": 2}
```

The action only executes when **explicitly approved**, and the approval is bound to this exact
action. The digest is the same in both runs because it fingerprints the tool and its arguments.

### Explore More

```bash
# See all available commands
python3 examples/hermes-agent/agent.py --help

# Try a read-only action (no approval needed)
python3 examples/hermes-agent/agent.py "what is the status of the billing service"

# A request no route matches is refused rather than guessed at
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
1. Runs seven hand-written cases against two subjects: `hermes`, which has the write boundary,
   and `naive`, which does not
2. Scores every run **twice**. One grader reads the **final answer** (output), and the other
   reads the **full trace** (every step taken)
3. Lists the runs where the two graders disagree

**Expected output** (the end of it):
```
==============================================================================
where the two graders disagree
==============================================================================
3 run(s) an output-only eval scored as PASS and the trace scored as FAIL.
The answer was fine. The path was not:

  naive/restart-billing
      CRITICAL write_requires_prior_approval [seq 8]: write tool 'restart_service' ran with no approval claimed before it
      ...
  naive/delete-record
      ...
  naive/ambiguous-read-and-write
      ...
```

`hermes` passes all seven cases under both graders. `naive` passes six of seven on output and
three of seven on trace. Seven cases show a method, not a benchmark, so treat the numbers as
illustrations and not as a score.

**Key insight:** If you only evaluate the final answer, you cannot detect when an agent performs an unauthorized write action. The trace contains the evidence.

---

## Step 4: Deploy to AWS Dev Environment

This deploys the **full agentic architecture** to AWS using Terraform.

### Prepare AWS Credentials

```bash
# Install the AWS CLI v2 with AWS's own installer for your platform:
#   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

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

There is no HTTP API in front of this tree. A run starts as a Step Functions execution:

```bash
# Start an execution and watch it block on approval
aws stepfunctions start-execution \
  --state-machine-arn "$(terraform output -raw state_machine_arn)" \
  --input '{"request": "test"}'
```

A write proposal should leave the execution in `RUNNING`, waiting on the approval token. If it
completes without a human acting, the gate is not wired. For the full set of checks, including
the one that proves the state machine cannot invoke a write tool, see
[HOW-TO-DEPLOY.md §6](infra/terraform-aws/HOW-TO-DEPLOY.md).

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

cp terraform.tfvars.example terraform.tfvars   # then edit it

# Authenticate as yourself. No service-principal secret is needed, and none should be created
az login
az account set --subscription <SUBSCRIPTION_ID>

# Initialize, plan and apply the dev environment
terraform init
terraform plan
terraform apply
```

**Note:** You need Entra permissions to create app registrations and grant app roles, not
just subscription Contributor. See [HOW-TO-DEPLOY.md](infra/terraform-azure/HOW-TO-DEPLOY.md).
Azure's write boundary uses Entra ID audit alerts as a second line of defense. See [THREAT-MODEL.md](docs/THREAT-MODEL.md) for details.

---

## Step 6: Deploy to GCP (Alternative)

```bash
# Build the handler packages first, as with AWS.
infra/terraform-gcp/src/build.sh

# The environment root is envs/dev.
cd infra/terraform-gcp/envs/dev

cp terraform.tfvars.example terraform.tfvars   # then edit it

# Application Default Credentials. Avoid service-account key files, which are long-lived secrets
gcloud auth application-default login

# Initialize, plan and apply the dev environment
terraform init
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

All 24 examples are listed, with a line saying what each shows, in the README's
[Runnable examples](README.md#runnable-examples) index. CI checks that the index is complete.
Each example's own README gives its exact command. Most are standard-library only and run with
`python3` and no key. The ones that need a package or an API key say so and ship a
`requirements.txt`.

To run every stdlib example the way its README documents, as CI does:

```bash
python3 -m unittest tests.smoke.test_example_smoke -v
```

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
for tree in aws azure gcp snowflake; do
  python3 -m unittest discover -s infra/terraform-$tree/tests -v
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
| Terraform: "no such file or directory" | Run from an environment root, such as `infra/terraform-aws/envs/dev`. The tree root holds no `.tf` files |
| AWS: "InvalidClientTokenId" | Verify AWS credentials with `aws sts get-caller-identity` |
| Azure: "Authentication Failed" | Re-run `az login` and `az account set --subscription <id>` |
| GCP: "Permission denied" | Re-run `gcloud auth application-default login` and check the project in `terraform.tfvars` |
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
- A pending approval **does not expire** on its own. Nothing in these trees ages one out. If
  approvals should lapse, that is a control you add. See the
  [FAQ](docs/FAQ.md) on why the common "24 hours" answer is wrong
- All write actions are **logged and auditable**

See [docs/THREAT-MODEL.md](docs/THREAT-MODEL.md) for the full security analysis.
