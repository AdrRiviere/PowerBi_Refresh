import os
from datetime import datetime

import prefect as pf
from dotenv import load_dotenv

from utils.utils import (
    close,
    connect,
    create_embed_report,
    export_screenshot_aws,
    get_driver,
    get_paths,
)


@pf.flow(
    name="[iTools][Power BI] Screenshot Power BI Dashboard",
    log_prints=True,
    flow_run_name="PowerBI_Screenshot_" + datetime.today().strftime("%Y%m%d_%H%M%S"),
)
def main_screenshot_dashboard(name_screenshot, url="", headless=True):
    load_dotenv()

    user = os.environ.get("microsoft_data_analytics_login")
    passwd = os.environ.get("microsoft_data_analytics_passwd")
    aws_access_key_id = os.environ.get("aws_access_key_id")
    aws_secret_access_key = os.environ.get("aws_secret_access_key")
    region_name = os.environ.get("region_name")

    path_driver, path_chrome, path_downloads = get_paths()
    driver = get_driver(url, path_driver, path_chrome, path_downloads, headless)
    driver = connect(driver, user, passwd)
    driver = create_embed_report(driver, name_screenshot)
    close(driver)
    export_screenshot_aws(region_name, aws_access_key_id, aws_secret_access_key, name_screenshot)
