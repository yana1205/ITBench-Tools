import argparse
import logging
import time
from requests.exceptions import ConnectionError

import agent_bench_automation.bench_runner.taker
from agent_bench_automation.app.config import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_MINIBENCH_HOST, DEFAULT_MINIBENCH_PORT

logger = logging.getLogger(__name__)
log_format = "[%(asctime)s %(levelname)s %(name)s] %(message)s"


def main():
    parser = argparse.ArgumentParser(description="Compliance Assessment Agent (CAA) Benchmark")
    parser.add_argument("-v", "--verbose", help="Display verbose output", action="count", default=0)

    # bm taker --> bench_runner
    parser.add_argument(
        "--remote_host", type=str, default=DEFAULT_HOST, help=f"The hostname or IP address to remote Benchmark Server (default: {DEFAULT_HOST})."
    )
    parser.add_argument(
        "--remote_port", type=int, default=DEFAULT_PORT, help=f"The port number to remote Benchmark Server (default: {DEFAULT_PORT})."
    )
    parser.add_argument("--remote_token", type=str, help=f"Bearer token of Benchmark Server.", required=True)
    parser.add_argument(
        "--minibench_host",
        type=str,
        default=DEFAULT_MINIBENCH_HOST,
        help=f"The hostname or IP address to remote Mini Benchmark Server (default: {DEFAULT_MINIBENCH_HOST}).",
    )
    parser.add_argument(
        "--minibench_port",
        type=int,
        default=DEFAULT_MINIBENCH_PORT,
        help=f"The port number to remote Mini Benchmark Server (default: {DEFAULT_MINIBENCH_PORT}).",
    )

    args = parser.parse_args()

    if args.verbose > 0:
        logging.basicConfig(format=log_format, level=logging.DEBUG)
    else:
        logging.basicConfig(format=log_format, level=logging.INFO)

    wait_timeout = 600
    wait_interval = 20
    start = time.time()
    while time.time() - start < wait_timeout:
        try:
            agent_bench_automation.bench_runner.taker.run(args)
        except ConnectionError as e:
            print(f"Connection Error: {e}")
            print(f"It seems that some endpoints are not ready. Retrying in {wait_interval} seconds...")
            time.sleep(wait_interval)
        except Exception:
            raise


if __name__ == "__main__":
    main()
