import subprocess
import sys

def run_agent(args):
    cmd = [sys.executable, "examples/starter-agent/agent.py"] + args
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def test_agent_basic():
    rc, out, err = run_agent(["hello"])
    assert rc == 0
    assert "Agent received" in out


def test_agent_actions():
    rc, out, err = run_agent(["please", "search", "for", "X"])
    assert rc == 0
    assert "Action: search" in out
