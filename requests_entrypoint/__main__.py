import json
import os
import re
import sys
import logging
import subprocess
from requests_entrypoint.exceptions import SpiderCodeException

logger = logging.getLogger("requests_entrypoint")

def execute(args, hdlr):
    """Execute the spider from the command line.
    
    It should imitates the command line execution of the spider.

    python spider.py
    """
    command = " ".join(args)
    logger.info("Running command: %s", command)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=os.environ)
    for line in process.stdout:
        logger.info("%s", line)
    for line in process.stderr:
        logger.error("%s", line)
    returncode = process.wait()
    if returncode != 0:
        raise SpiderCodeException(f"Spider code returned non-zero exit code: {returncode}")
    logger.info("Successful Spider Requests execution.")

def setup_and_launch():
    from requests_entrypoint.utils import decode_job, get_args_and_env
    from requests_entrypoint.log import init_logging
    from requests_entrypoint.spider_file_helpers import get_file_by_spider_name
    try:
        job = decode_job()
        assert job,  "JOB_INFO must be set"
        job["spider"] = get_file_by_spider_name(os.getcwd(), job["spider"])  # get file name.
        args, env = get_args_and_env(job)
        os.environ.update(env)
        loghdlr = init_logging()
        loghdlr.setLevel(logging.DEBUG)

    except Exception:
        logging.exception("Environment variables were not defined properly.")
        raise

    _start_proxy_tunnel_if_needed()
    # run code.
    execute(args, None)

# Temporary workaround to support authenticated proxies in Selenium/Chrome.
# This will be replaced by a proper solution in future versions.
def _start_proxy_tunnel_if_needed():
    import shutil

    if not os.environ.get("ESTELA_PROXIES_ENABLED"):
        return
    if not shutil.which("mitmdump"):
        logger.info("[proxy] mitmdump not found, skipping tunnel (requests-only project).")
        return
    proxy_user = os.environ.get("ESTELA_PROXY_USER", "")
    proxy_pass = os.environ.get("ESTELA_PROXY_PASS", "")
    proxy_url  = os.environ.get("ESTELA_PROXY_URL", "")
    proxy_port = os.environ.get("ESTELA_PROXY_PORT", "")
    if not all([proxy_user, proxy_pass, proxy_url]):
        logger.warning("[proxy] Incomplete proxy variables, skipping tunnel.")
        return
    logger.info("[proxy] Starting mitmproxy tunnel -> %s:%s", proxy_url, proxy_port)
    subprocess.Popen(
        [
            "mitmdump",
            "--listen-host", "127.0.0.1",
            "--listen-port", "8888",
            "--mode", f"upstream:http://{proxy_url}:{proxy_port}",
            "--upstream-auth", f"{proxy_user}:{proxy_pass}",
            "--ssl-insecure",
            "--set", "http2=false",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    import socket
    import time
    for _ in range(20):
        try:
            s = socket.create_connection(("127.0.0.1", 8888), timeout=1)
            s.close()
            logger.info("[proxy] Tunnel ready on 127.0.0.1:8888")
            return
        except OSError:
            time.sleep(0.5)
    logger.warning("[proxy] Tunnel did not start after 10s, proceeding anyway.")

def describe_project():
    from requests_entrypoint.spider_file_helpers import get_spider_names
    result = {
            "project_type": "requests",
            "spiders": get_spider_names(os.getcwd()),
    }
    print(json.dumps(result))
    return 0


def report_deploy():
    """Report deployment status to Estela API and manage ECR images."""
    from requests_entrypoint.report_deploy_handler import ReportDeployHandler

    handler = ReportDeployHandler()
    return handler.run()


def main():
    from requests_entrypoint.utils import producer
    try:
        if producer.get_connection():
            logging.debug("Successful connection to the queue platform.")
        else:
            raise Exception("Could not connect to the queue platform.")
        setup_and_launch()
        code = 0
    except SystemExit as ex:
        code = ex.code
    except Exception as ex:
        logger.exception("Unknown Exception: %s", ex)
        code = 1
    finally:
        producer.flush()
        producer.close()
    
    return code


if __name__ == "__main__":
    sys.exit(main())