from dagster import Definitions, load_assets_from_modules, AssetSelection, define_asset_job, ScheduleDefinition, with_resources

from . import assets
import os
from github import Github
from dotenv import load_dotenv
load_dotenv('E:\python\airflow\dagster\thisnewproject\thisnewproject\.env')

all_assets = load_assets_from_modules([assets])



# Define a job that will materialize the assets
drive_api_job = define_asset_job("drive_api_job", selection=AssetSelection.all())

drive_api_schedule = ScheduleDefinition(
    job=drive_api_job,
    cron_schedule = "0 * * * *",
)

defs = Definitions(
    assets=all_assets,
    schedules=[drive_api_schedule],
    resources={"github_api": Github(os.environ.get('GITHUB_ACCESS_TOKEN'))}, #github_api variable declaration.. all resources belongs to 'context'
)