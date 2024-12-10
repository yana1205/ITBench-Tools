# Copyright (c) 2024 IBM Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import logging

import agent_bench_automation.agent_harness.agent
from agent_bench_automation.app.config import DEFAULT_MINIBENCH_HOST, DEFAULT_MINIBENCH_PORT


logger = logging.getLogger(__name__)
log_format = "[%(asctime)s %(levelname)s %(name)s] %(message)s"


def main():
    parser = argparse.ArgumentParser(description="Compliance Assessment Agent (CAA) Benchmark")
    parser.add_argument("-v", "--verbose", help="Display verbose output", action="count", default=0)

    # caa agent harness
    parser.add_argument(
        "--host", type=str, default=DEFAULT_MINIBENCH_HOST, help=f"The hostname or IP address (default: {DEFAULT_MINIBENCH_HOST})."
    )
    parser.add_argument(
        "--port", type=int, default=-1, help=f"The port number (Set -1 if you don't use port number)."
    )
    parser.add_argument("-ad", "--agent_directory", type=str, default="caa-agent", help=f"Path to root directory of Agent project")
    parser.add_argument("-i", "--input", type=str, help="Path to MiniBenchResult", required=True)

    args = parser.parse_args()

    if args.verbose > 0:
        logging.basicConfig(format=log_format, level=logging.DEBUG)
    else:
        logging.basicConfig(format=log_format, level=logging.INFO)

    agent_bench_automation.agent_harness.agent.run(args)


if __name__ == "__main__":
    main()
