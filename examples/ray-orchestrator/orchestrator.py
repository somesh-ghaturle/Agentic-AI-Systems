#!/usr/bin/env python3
"""Simple Ray orchestration example.

Requirements: pip install -r requirements.txt

This demonstrates parallel tasks and result aggregation using Ray.
"""
import ray
import time


@ray.remote
def work(x):
    time.sleep(0.5)
    return x * x


def main():
    ray.init(ignore_reinit_error=True)
    inputs = list(range(1, 9))
    futures = [work.remote(x) for x in inputs]
    results = ray.get(futures)
    print("Inputs:", inputs)
    print("Results:", results)


if __name__ == "__main__":
    main()
