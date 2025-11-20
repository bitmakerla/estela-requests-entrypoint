# estela-requests-entrypoint

Requests entrypoint for Estela job runner. This package provides the execution layer for running requests-based spiders on the Estela platform, serving as an alternative to Scrapy-based projects.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Available Commands](#available-commands)
- [Recent Changes](#recent-changes)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/bitmakerla/estela-requests-entrypoint.git
   ```

2. Change into the repository's directory:

   ```bash
   cd estela-requests-entrypoint
   ```

3. (Optional) Create and activate a virtual environment:

   ```bash
   python3 -m venv env
   source env/bin/activate
   ```

4. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

This package provides console script entrypoints for managing Estela requests-based spider projects.

### Running Spiders

The main entrypoint executes spider jobs within the Estela platform:

```bash
estela-crawl
```

This command:
- Connects to the Estela queue platform (Kafka)
- Parses job information from environment variables
- Executes the specified spider
- Handles logging and error reporting

### Project Description

To list all available spiders in a requests project:

```bash
estela-describe-project
```

Returns JSON output:
```json
{
  "project_type": "requests",
  "spiders": ["spider1", "spider2"]
}
```

## Available Commands

After installation, the following console commands are available:

### `estela-crawl`
Main job runner for executing requests-based spiders on Estela platform.

**Environment Variables Required:**
- `JOB_INFO` - JSON with job configuration (api_host, spider name, etc.)
- Queue connection parameters (Kafka)

### `estela-describe-project`
Lists all spiders in the current requests project.

**Usage:**
```bash
estela-describe-project
```

**Output:** JSON with project type and spider list

### `estela-report-deploy`
Reports deployment status to Estela API and manages ECR Docker images.

**Environment Variables Required:**
- `KEY` - Format: `project_id.deploy_id`
- `JOB_INFO` - JSON with `api_host`
- `TOKEN` - Authentication token for Estela API
- `REPOSITORY_NAME` - ECR repository name (default: "estela")
- `CLEANUP_CANDIDATE_IMAGES` - Set to "true" to cleanup candidate images (default: "false")

**What it does:**
1. Detects spiders in the project
2. Promotes candidate Docker image (`estela_{project_id}_candidate`) to production (`estela_{project_id}`) in ECR
3. Reports deployment status (SUCCESS/FAILURE) to Estela API
4. Optionally cleans up candidate images after deployment

**Usage:**
```bash
estela-report-deploy
```

## Recent Changes

### December 2024 - Added `estela-report-deploy` Command

**New Features:**
- ✅ Added `estela-report-deploy` console command for deployment reporting
- ✅ Implemented ECR image promotion (candidate → production)
- ✅ Added deployment status reporting to Estela API
- ✅ Optional candidate image cleanup after deployment
- ✅ Added `boto3` dependency for AWS ECR operations

**Files Modified:**
- `requests_entrypoint/__main__.py` - Added `report_deploy()` function
- `requests_entrypoint/report_deploy_handler.py` - New handler class (created)
- `setup.py` - Added `estela-report-deploy` entry point and boto3 dependency
- `requirements.txt` - Added boto3

**Migration from estela-entrypoint:**
This implementation mirrors the `report-deploy` functionality from the Scrapy-based `estela-entrypoint` package, adapted for requests-based spider projects. The API contracts and ECR image management patterns remain consistent across both implementations.
