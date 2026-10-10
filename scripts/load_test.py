#!/usr/bin/env python3
"""Test de charge simple pour déclencher l'autoscaling (HPA) de Kubernetes.

Il envoie des requêtes concurrentes à /api/stress (qui consomme du CPU) et
affiche chaque seconde le débit, les erreurs et la répartition par pod.

Usage :
    python3 scripts/load_test.py --url http://localhost:8080
    python3 scripts/load_test.py --url http://<load-balancer> --concurrency 40 --duration 180

Bibliothèque standard uniquement : rien à installer.
"""
import argparse
import json
import threading
import time
import urllib.error
import urllib.request
from collections import Counter


def worker(url, stop_event, stats, lock):
    while not stop_event.is_set():
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                body = json.loads(response.read())
            with lock:
                stats["ok"] += 1
                stats["pods"][body.get("hostname", "?")] += 1
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            with lock:
                stats["errors"] += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://localhost:8080", help="URL du frontend ou de l'API")
    parser.add_argument("--concurrency", type=int, default=20, help="nombre de requêtes simultanées")
    parser.add_argument("--duration", type=int, default=120, help="durée du test en secondes")
    parser.add_argument("--iterations", type=int, default=400_000, help="travail demandé par requête (CPU)")
    args = parser.parse_args()

    target = f"{args.url.rstrip('/')}/api/stress?iterations={args.iterations}"
    stats = {"ok": 0, "errors": 0, "pods": Counter()}
    lock = threading.Lock()
    stop_event = threading.Event()

    print(f"Cible        : {target}")
    print(f"Concurrence  : {args.concurrency} | Durée : {args.duration}s")
    print("Pendant ce temps, observe : kubectl get hpa -w  et  kubectl get pods -w\n")

    threads = [
        threading.Thread(target=worker, args=(target, stop_event, stats, lock), daemon=True)
        for _ in range(args.concurrency)
    ]
    for thread in threads:
        thread.start()

    start = time.time()
    last_ok = 0
    try:
        while time.time() - start < args.duration:
            time.sleep(1)
            with lock:
                ok, errors, pods = stats["ok"], stats["errors"], len(stats["pods"])
            elapsed = int(time.time() - start)
            print(f"[{elapsed:>4}s] requêtes/s : {ok - last_ok:>4} | total : {ok:>6} | erreurs : {errors:>4} | pods vus : {pods}")
            last_ok = ok
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur.")
    finally:
        stop_event.set()

    print("\nRépartition des réponses par pod :")
    for pod, count in stats["pods"].most_common():
        print(f"  {pod:<45} {count}")
    print(f"\nTotal : {stats['ok']} requêtes réussies, {stats['errors']} erreurs")


if __name__ == "__main__":
    main()
