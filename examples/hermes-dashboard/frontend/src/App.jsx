import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [approvals, setApprovals] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/approvals`)
      .then((response) => response.json())
      .then(setApprovals)
      .catch(() => setError("Approval service is unavailable."));
    const socket = new WebSocket(API.replace(/^http/, "ws") + "/ws");
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.event === "snapshot") setApprovals(message.approvals);
      if (message.event === "approval.created")
        setApprovals((items) => [...items, message.approval]);
      if (message.event === "approval.decided")
        setApprovals((items) =>
          items.map((item) => (item.id === message.approval.id ? message.approval : item)),
        );
    };
    return () => socket.close();
  }, []);

  async function decide(id, decision) {
    const response = await fetch(`${API}/approvals/${id}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, actor: "dashboard-operator" }),
    });
    if (!response.ok) setError("That approval was already decided.");
  }

  return (
    <main>
      <h1>Hermes approvals</h1>
      <p className="notice">Review the exact action and fingerprint before deciding.</p>
      {error && <p className="error">{error}</p>}
      {approvals.length === 0 && <p>No pending approvals.</p>}
      {approvals.map((approval) => (
        <article key={approval.id} className={approval.status}>
          <header>
            <strong>{approval.tool}</strong>
            <span>{approval.status}</span>
          </header>
          <p>{approval.rationale}</p>
          <pre>{JSON.stringify(approval.arguments, null, 2)}</pre>
          <code>{approval.fingerprint}</code>
          {approval.status === "pending" && (
            <div className="actions">
              <button onClick={() => decide(approval.id, "approve")}>Approve</button>
              <button onClick={() => decide(approval.id, "reject")}>Reject</button>
            </div>
          )}
        </article>
      ))}
    </main>
  );
}
