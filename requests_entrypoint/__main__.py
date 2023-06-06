import json
import os
import sys
import logging
import subprocess

from requests_entrypoint.utils import decode_job, get_args_and_env, producer
from requests_entrypoint.log import init_logging

logging.basicConfig(level=logging.INFO)   

def execute(args, hdlr):
    """Execute the spider from the command line.
    
    It should imitates the command line execution of the spider.

    python spider.py
    """
    command = " ".join(args)
    print("Running commands:", command)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=os.environ)
    for line in process.stdout:
        logging.info("Subprocess output: %s", line)
    for line in process.stderr:
        logging.error("Subprocess error: %s", line)
    returncode = process.wait()

    print("Codigo de Salida: ", returncode)

def run_spider(argv, settings):
    sys.argv = argv
    execute(settings=settings)

def setup_and_launch():
    try:
        print("Sigo que te sigo")
        job = decode_job()
        assert job,  "JOB_INFO must be set"
        args, env = get_args_and_env(job)
        print("doing things")
        print(args)
        os.environ.update(env)
        loghdlr = init_logging()
        loghdlr.setLevel(logging.DEBUG)

    except Exception:
        logging.exception("Environment variables were not defined properly.")
        raise

    # run code.
    execute(args, None)

def describe_project():
    result = {
            "project_type": "requests",
            "spiders": ["spider.py", "spider2.py"],
    }
    return json.dumps(result)

def main():
    try:
        if producer.get_connection():
            logging.debug("Successful connection to the queue platform.")
        else:
            raise Exception("Could not connect to the queue platform.")
        setup_and_launch()
        code = 0
    except SystemExit as ex:
        code = ex.code
    except:
        code = 1
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    sys.exit(main())
