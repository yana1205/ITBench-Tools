import argparse
import logging
import time
from requests.exceptions import ConnectionError

from agent_bench_automation.bench_runner.taker import run as mini_bench_run
# TODO: fix circular import of `app.runner`
# from agent_bench_automation.app.runner import run as bench_run
from agent_bench_automation.app.config import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_MINIBENCH_HOST, DEFAULT_MINIBENCH_PORT

logger = logging.getLogger(__name__)
log_format = "[%(asctime)s %(levelname)s %(name)s] %(message)s"


def main():
    parser = argparse.ArgumentParser(description="Compliance Assessment Agent (CAA) Benchmark")
    parser.add_argument("-v", "--verbose", help="Display verbose output", action="count", default=0)

    # normal bench runner
    parser.add_argument("-c", "--config", type=str, help="Path to the application configuration.")
    parser.add_argument("-i", "--runner_id", type=str, help="Unique identifier for the runner.")

    # mini bench runner
    parser.add_argument("--mini", action="store_true", help="If specified, run in the old mode i.e. \"mini bench runner\"")
    parser.add_argument(
        "--remote_host", type=str, default=DEFAULT_HOST, help=f"The hostname or IP address to remote Benchmark Server (default: {DEFAULT_HOST})."
    )
    parser.add_argument(
        "--remote_port", type=int, default=DEFAULT_PORT, help=f"The port number to remote Benchmark Server (default: {DEFAULT_PORT})."
    )
    parser.add_argument("--remote_token", type=str, help=f"Bearer token of Benchmark Server.")
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
            if args.mini:
                mini_bench_run(args)
            else:
                raise Exception("not implemented")
                # bench_run(args)
                # NOTE: Until circular import issue is fixed, we use `main.py` in the project root for remote runner
        except ConnectionError as e:
            print(f"Connection Error: {e}")
            print(f"It seems that some endpoints are not ready. Retrying in {wait_interval} seconds...")
            time.sleep(wait_interval)
        except Exception:
            raise


if __name__ == "__main__":
    main()
