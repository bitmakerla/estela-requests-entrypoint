import json
import os
import re
import sys
import logging
import subprocess

logger = logging.getLogger("requests_entrypoint")

def execute(args, hdlr):
    """Execute the spider from the command line.
    
    It should imitates the command line execution of the spider.

    python spider.py
    """
    command = " ".join(args)
    print("Running commands:", command)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=os.environ)
    for line in process.stdout:
        logger.info("Subprocess output: %s", line)
    for line in process.stderr:
        logger.error("Subprocess error: %s", line)
    returncode = process.wait()

    print("Codigo de Salida: ", returncode)

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

    # run code.
    execute(args, None)


def describe_project():
    from requests_entrypoint.spider_file_helpers import get_spider_names
    result = {
            "project_type": "requests",
            "spiders": get_spider_names(os.getcwd()),
    }
    print(json.dumps(result))
    return 0
    

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
