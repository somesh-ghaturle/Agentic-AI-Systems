# How to deploy

Read [ARCHITECTURE.md](ARCHITECTURE.md) first, particularly section 2. This document assumes you
know what the two locks are and why one of them cannot be verified by `terraform validate`.

---

## Before you start

**One GCP project per environment.** This is not a preference. Three things in this tree
are project-scoped and cannot be name-prefixed apart: `roles/datastore.user` covers every
Firestore database in the project, service account IDs are unique per project, and an IAM
Deny policy attaches to the project rather than to a resource. Sharing one project between
dev and prod means dev's grants reach prod's data.

**Permissions.** Beyond project Owner or Editor, you need one thing that is not included in
either:

- `roles/iam.denyAdmin`, at the project or organization level, to create the IAM Deny
  policy. Without it the apply fails at the very last resource, after everything else
  exists.

**APIs.** Only `aiplatform.googleapis.com` is enabled by this tree, via
`modules/model-integration`. Enable the rest yourself:

```bash
gcloud services enable \
  cloudfunctions.googleapis.com run.googleapis.com cloudbuild.googleapis.com \
  workflows.googleapis.com firestore.googleapis.com cloudkms.googleapis.com \
  storage.googleapis.com pubsub.googleapis.com logging.googleapis.com \
  monitoring.googleapis.com secretmanager.googleapis.com \
  --project=<your-project>
```

**Model Garden terms.** Claude models on Vertex AI require accepting Anthropic's terms in
the target project, in the Model Garden console. There is no Terraform resource for it and
no API. Skip it and every model call returns 403 with a message that does not obviously say
"go click a button."

**Authentication.** Application Default Credentials:

```bash
gcloud auth application-default login
```

From CI, prefer Workload Identity Federation over a service account key. A key file is a
long-lived credential in a repository secret, and rotating it means coordinating every
consumer.

---

## 1 · Remote state

Uncomment the backend block in the env root and fill it in before the first apply. GCS
backends lock by default — there is no separate lock table to forget.

```hcl
backend "gcs" {
  bucket = "<your-tf-state-bucket>"
  prefix = "agentic/dev"
}
```

Create the bucket out of band, with versioning on. Local state for shared infrastructure
means two people applying at once corrupt each other's work, and the corruption is only
visible later.

---

## 2 · Build the handler packages

**This does not exist yet.** There is no `src/` tree here. The AWS handlers in
`infra/terraform-aws/src` are written against boto3, DynamoDB, OpenSearch, and Step
Functions task tokens, and will not run on Cloud Functions unmodified.

Every `package_path` in `terraform.tfvars` is read at plan time to compute a deployment
hash, so **until that source exists these roots validate but do not plan.**

When you write them, the expected layout is one zip per handler:

```
build/
  retrieve.zip
  reason.zip
  process_refund.zip
  approval_validator.zip
  approval_executor.zip
  emit_trace.zip
```

Each zip has the handler at its root with a `requirements.txt` beside it — the gen2 build
runs `pip install` from that file during deployment. The exported symbol must match the
tool's `entry_point`.

The object name in GCS carries the package hash. Without that, uploading a changed zip
under the same name leaves the deployed function untouched: Cloud Functions keys its build
on the object path, so a same-named object is a no-op and the fix you just deployed is not
running. `modules/tools` handles this; if you stage packages yourself, do the same.

---

## 3 · Configure

```bash
cd envs/dev
cp terraform.tfvars.example terraform.tfvars
```

The example file is annotated. Three things there deserve more than a glance.

### `access` on each tool

This decides the invocation path and nothing else in the file matters more:

- `read` → the orchestrator holds `run.invoker` and calls the function directly
- `write` → only the approval executor holds it, and the orchestrator is separately denied
  it

Classify by what the handler **does**, not by what it is called. A tool named
`lookup_account` that also writes an audit row is a write tool. Terraform cannot check
this — it is a property of your code, and getting it wrong makes the entire gate
decorative while every output still says it is intact.

### `project` is capped at 10 characters

Service account IDs cap at 30, and this root derives them as
`<project>-<env>-<tool name>`. With `prod` and a 14-character tool name like
`process_refund`, ten is what fits. The identity module fails at plan time rather than
letting the API reject a half-finished apply.

Do not work around this by truncating. Two truncated IDs that collide produce one service
account shared by two tools, which quietly undoes one-identity-per-workload.

### The embedding dimension is one decision written twice

`dimensions` on the knowledge module and `EMBEDDING_MODEL` on the retrieve tool must agree
— 768 for `text-embedding-004`, 3072 for `gemini-embedding-001`. A mismatch is accepted at
index-create time and fails on every query afterwards.

---

## 4 · Apply

```bash
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

Read the plan. Specifically, check that:

- Every service account you expect appears, and no more.
- `google_cloud_run_service_iam_member` for the write tool names the **executor**.
- `google_iam_deny_policy` appears at all. Its absence means no tool is classified `write`.

First applies take a while. The Vector Search deployed index is the slow one — twenty to
forty minutes is normal, and it is not stuck.

**In prod, one resource is irreversible.** `lock_retention_policy = true` on the archive
bucket cannot be undone by anyone, including the project owner and Google support. After it
applies, the retention period can only be increased and the bucket cannot be deleted while
anything is still under retention. Decide on the period before the apply, not after.

---

## 5 · What the handlers must do

Terraform draws the boundary; these are the properties it cannot draw. See ARCHITECTURE.md
Section 7 for what each failure looks like from the outside.

### All handlers

Write structured entries to the log named in `TRACE_LOG_NAME`, through the Cloud Logging
API — not to stdout. Anything printed to stdout is captured, appears in the console looking
healthy, and lands in the function's own log where no metric is watching.

The fields the metrics expect:

```json
{
  "event": "execution_completed",
  "execution_id": "...",
  "terminal": true,
  "cost_usd": 0.0412,
  "total_tokens": 8134
}
```

`event` drives three of the four metrics. `terminal` and `cost_usd` drive the fourth, and
`cost_usd` must appear **only** on the terminal record — the metric sums whatever it is
given.

### Read tools

Return quickly and do not mutate anything. `retrieve` applies tenant scoping as a namespace
restrict inside the Vector Search query, not as a filter on the results: filtering after
the fact means the neighbours were already chosen across tenants, so the result set comes
back short rather than wrong-tenant. That reads as poor recall and hides a real problem.

### The reason handler

Returns `action_type` (`write`, `continue`, or anything else for terminal), a `proposal`
when writing, and `cost_usd` / `total_tokens` for the terminal record. Classified `read`
because it proposes and never executes.

### The validator

Deterministic checks only — ownership, permission, limits — and they run **before** any
human is notified. Two entry paths: a validation call returning `{valid, reason,
approval_id}`, and a `notify` call that publishes to Pub/Sub with the callback URL.

Its policy limit and the write tool's own ceiling are two checks in two places on purpose.
The validator can be bypassed by a bug; the tool cannot.

### The executor

Claims the approval with a conditional write before invoking anything, invokes the write
tool, records the outcome, then resolves the workflow callback.

**Write tools must be idempotent on the approval ID.** The stale-claim reaper lets another
executor reclaim a record stuck in `executing` past `STALE_CLAIM_SECONDS`. If the tool is
not idempotent, that reclaim is a second refund.

Resolving the callback is not optional. Skip it and the write happens while the
orchestrator waits out its full timeout, which is recorded as an abandoned approval.

### The trace emitter

Takes `{event, payload}` and writes it to `TRACE_LOG_NAME`. It is the only way the
orchestrator's own records reach the metrics. It needs `roles/logging.logWriter`; without
it the function returns 200 and writes nothing.

---

## 6 · Verify the deployment

Terraform applying cleanly does not mean the boundary holds. Run these.

**The static checks** — no credentials needed, and they run in CI:

```bash
python3 -m unittest discover -s infra/terraform-gcp/tests -v
```

**Lock 1 — the orchestrator cannot invoke a write tool:**

```bash
ORCH=$(terraform output -raw service_accounts | python3 -c \
  'import json,sys; print([v for k,v in json.load(sys.stdin).items() if "orchestrator" in k][0])')
WRITE_URL=$(terraform output -json write_tools | python3 -c \
  'import json,sys; print(list(json.load(sys.stdin).values())[0])')

# Should print an empty policy — no run.invoker for the orchestrator.
gcloud run services get-iam-policy "$(basename "${WRITE_URL}" | cut -d. -f1)" \
  --region=<region> --format=json | grep -c "${ORCH}"
```

**Lock 2 — rehearse the deny policy.** This is the one that matters most, because a deny
policy naming a wrong-but-valid permission applies cleanly, appears in the console, and
denies nothing. Do this once, against a throwaway service account:

```bash
# 1. Grant the throwaway account run.invoker on a write tool DIRECTLY.
gcloud run services add-iam-policy-binding <write-tool-service> \
  --region=<region> --member="serviceAccount:${THROWAWAY}" \
  --role=roles/run.invoker

# 2. Confirm it CAN invoke. If it cannot, your test is wrong, not the policy.
curl -H "Authorization: Bearer $(gcloud auth print-identity-token \
  --impersonate-service-account="${THROWAWAY}")" "${WRITE_URL}"

# 3. Add the throwaway to the deny policy's principals, apply, and repeat step 2.
#    It must now fail with 403.

# 4. Remove it from the deny policy and repeat step 2. It must succeed again.
```

Steps 2 and 4 are the ones people skip, and they are the ones that distinguish "the deny
works" from "something else was refusing all along." A control nobody has seen refuse, and
then seen stop refusing, is a hypothesis.

**The round trip — start an execution and watch it block:**

```bash
gcloud workflows run "$(terraform output -raw workflow_name)" \
  --location=<region> \
  --data='{"query":"refund order 12345","tenant_id":"t1"}'
```

It should suspend at `await_approval`. Resolve it through the executor and confirm the
execution resumes. An execution that completes without suspending means the reason handler
never returned `action_type: "write"` — the gate was not exercised.

**The metrics are receiving data:**

```bash
gcloud logging read \
  "logName=projects/<project>/logs/$(terraform output -raw trace_log_name)" \
  --limit=5 --format=json
```

Empty after a successful execution means the handlers are writing to stdout instead. Every
alert in the system is at zero and will stay there.

---

## 7 · Prod

Same commands, different consequences. `envs/prod/main.tf` annotates every difference; the
ones to read before applying:

- **The archive retention lock is irreversible.** Seven years by default.
- **Firestore delete protection is on** for both databases, so `terraform destroy` abandons
  them rather than deleting. That is deliberate; removing them is a two-step act.
- **`call_log_level` is `LOG_ERRORS_ONLY`.** Dev's `LOG_ALL_CALLS` records step arguments,
  and in prod those carry customer data. The cost is that a stuck execution has to be
  reconstructed from the trace log rather than read off the step history.
- **`approver_members` must not be empty.** An empty map means every gated write sits until
  its 24-hour window closes and is then abandoned. The system stays safe and stops doing
  anything. Prefer a group over named individuals: a person leaves, and the approval path
  fails closed at whatever hour that becomes apparent.

---

## Troubleshooting

**`Error 403` on every model call.** Model Garden terms not accepted in this project. There
is no Terraform resource for it. See "Before you start."

**The apply fails at `google_iam_deny_policy` with everything else created.** Missing
`roles/iam.denyAdmin`. The policy is last in the graph, so this surfaces after the
expensive resources exist. Re-running after the grant is safe.

**Every Vector Search query returns nothing, or fewer results than expected.** Two
candidates, in order: the embedding dimension does not match the model (accepted at create
time, fails forever after), or the tenant namespace is being applied as a post-filter
rather than as a restrict inside the query.

**A tool returns 403 to the orchestrator.** Check the role. `roles/cloudfunctions.invoker`
on the function resource applies cleanly and controls nothing — gen2 needs
`roles/run.invoker` on the underlying Cloud Run service. This is the most common
GCP-specific mistake in this tree and `tests/test_write_boundary.py` guards it.

**Alerts sit at zero while the system is clearly running.** In order of likelihood: the
handlers are writing to stdout rather than to `TRACE_LOG_NAME`; the trace emitter is
missing `roles/logging.logWriter`; or the trace emitter was omitted, so the orchestrator's
own records never existed. The third is why `modules/orchestration` refuses to plan without
it.

**The archive bucket is empty.** The log sink's writer identity does not have
`objectCreator`. The sink reports no error in this state. `sink_writer_identity` is the
output that wires it.

**An approval was executed but the workflow timed out anyway.** The executor is missing
`roles/workflows.invoker` and cannot resolve the callback. The write succeeded; every
signal says it was abandoned.
