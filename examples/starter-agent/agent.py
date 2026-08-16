#!/usr/bin/env python3
import sys


def respond(prompt: str) -> str:
    p = prompt.lower()
    if "search" in p:
        return f"Action: search — simulated results for: {prompt}"
    if "plan" in p:
        return f"Action: plan — simulated plan for: {prompt}"
    if "deploy" in p:
        return f"Action: deploy — simulated deploy steps for: {prompt}"
    return f"Agent received: {prompt}"


def main():
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter prompt for agent: ")
    print(respond(prompt))


if __name__ == "__main__":
    main()
