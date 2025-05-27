import os
import requests
import sys
import json
import urllib3
from dotenv import load_dotenv

load_dotenv("config.env.local")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SEMS_URL = os.getenv("SEMS_URL")
SEMS_USER = os.getenv("SEMS_USER")
SEMS_PW = os.getenv("SEMS_PW")
SEMS_SEALMAN_CONFIG_NAME = os.getenv("SEMS_SEALMAN_CONFIG_NAME")
SEMS_SEALMAN_TEMPLATE_NAME = os.getenv("SEMS_SEALMAN_TEMPLATE_NAME")

IOTHUB_URL = os.getenv("IOTHUB_URL")
IOTHUB_SAS_TOKEN = os.getenv("IOTHUB_SAS_TOKEN")
IOTHUB_REGISTRY_URL = os.getenv("IOTHUB_REGISTRY_URL")
IOTHUB_REGISTRY_NAME = os.getenv("IOTHUB_REGISTRY_NAME")
IOTHUB_REGISTRY_USER = os.getenv("IOTHUB_REGISTRY_USER")
IOTHUB_REGISTRY_PASSWORD = os.getenv("IOTHUB_REGISTRY_PASSWORD")

def create_sealman_iothub_deployment():
    print("➡️  Creating IoTHub base deployment for sealman...")

    with open("configs/sealman-iothub-base-deployment.json", "r") as file:
        template = file.read()

    deployment_config = template.format(
        REGISTRY_URL=IOTHUB_REGISTRY_URL,
        REGISTRY_NAME=IOTHUB_REGISTRY_NAME,
        REGISTRY_USER=IOTHUB_REGISTRY_USER,
        REGISTRY_PASSWORD=IOTHUB_REGISTRY_PASSWORD
    )

    if IOTHUB_REGISTRY_NAME == "" or IOTHUB_REGISTRY_USER == "" or IOTHUB_REGISTRY_PASSWORD == "":
        temp = json.loads(deployment_config)
        temp["content"]["modulesContent"]["$edgeAgent"]["properties.desired"]["runtime"]["settings"] = {}
        deployment_config = json.dumps(temp)

    headers = {
        "Authorization": IOTHUB_SAS_TOKEN,
        "Content-Type": "application/json"
    }

    response = requests.put(f"https://{IOTHUB_URL}/configurations/base-deployment?api-version=2024-03-31",
                            headers=headers, data=deployment_config)

    if response.status_code not in [200, 409]:
        print(f"❌  Could not create IoTHub base deployment for sealman: {response.status_code}")
        sys.exit(2)
    elif response.status_code == 409:
        print("ℹ️  Base deployment already exists.")
    else:
        print("✅  IoTHub base deployment for sealman successfully created.")

def create_sealman_sems_config():
    print(f"➡️  Creating SEMS SEALMAN config...")
    auth_payload = {
        "username": SEMS_USER,
        "password": SEMS_PW
    }
    try:
        auth_response = requests.post(f"{SEMS_URL}/web/api/authentication/login_check",
                                      json=auth_payload, verify=False)
        auth_response.raise_for_status()
        token = auth_response.json().get("token")
    except Exception as e:
        print(f"❌  Failed to authenticate with SEMS: {e}")
        sys.exit(2)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    search_response= requests.post(f"{SEMS_URL}/web/api/config/list", headers=headers, verify=False,
                  json={"page":1,"rowsPerPage":10,"sorting":[{"field":"createdAt","direction":"desc"}],"filters":{"name":{"filterBy":"name","filterType":"equal","filterValue":SEMS_SEALMAN_CONFIG_NAME}}})

    if search_response.status_code != 200:
        print(f"❌  Failed to connect SEMS. HTTP status code: {search_response.status_code}")
        sys.exit(2)
    if search_response.json().get("rowCount") == 1:
        print("ℹ️  SEMS SEALMAN config already exists.")
        return

    with open("configs/sealman-sems-base-config.json", "r") as base_config:
        config_payload = json.loads(base_config.read())
        config_payload["name"] = SEMS_SEALMAN_CONFIG_NAME
    response = requests.post(f"{SEMS_URL}/web/api/config/create",
                             headers=headers, json=config_payload, verify=False)

    if response.status_code == 200:
        print("✅  SEMS SEALMAN config successfully created.")
        return response.json()["id"]
    else:
        print(f"❌  Failed to create SEMS SEALMAN config. HTTP status code: {response.status_code}")
        sys.exit(2)


def create_sealman_sems_template(config_id):
    print(f"➡️  Creating SEMS SEALMAN template...")
    auth_payload = {
        "username": SEMS_USER,
        "password": SEMS_PW
    }
    try:
        auth_response = requests.post(f"{SEMS_URL}/web/api/authentication/login_check",
                                      json=auth_payload, verify=False)
        auth_response.raise_for_status()
        token = auth_response.json().get("token")
    except Exception as e:
        print(f"❌  Failed to authenticate with SEMS: {e}")
        sys.exit(2)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    search_response = requests.post(f"{SEMS_URL}/web/api/template/list", headers=headers, verify=False,
                                    json={"page": 1, "rowsPerPage": 10,
                                          "sorting": [{"field": "createdAt", "direction": "desc"}], "filters": {
                                            "name": {"filterBy": "name", "filterType": "equal",
                                                     "filterValue": SEMS_SEALMAN_TEMPLATE_NAME}}})

    if search_response.status_code != 200:
        print(f"❌  Failed to connect SEMS. HTTP status code: {search_response.status_code}")
        sys.exit(2)
    if search_response.json().get("rowCount") == 1:
        print("ℹ️  SEMS SEALMAN template already exists.")
        return

    create_template_response = requests.post(f"{SEMS_URL}/web/api/template/create",
                             headers=headers, json={"name":SEMS_SEALMAN_TEMPLATE_NAME,"deviceType":"10"}, verify=False)

    if create_template_response.status_code == 200:
        print("✅  SEMS SEALMAN template successfully created.")
        template_id = create_template_response.json()["id"]
    else:
        print(f"❌  Failed to create SEMS SEALMAN template. HTTP status code: {create_template_response.status_code}")
        sys.exit(2)


    create_staging_response = requests.post(f"{SEMS_URL}/web/api/templateversion/create/staging/{template_id}",
                                             headers=headers, json={"name": SEMS_SEALMAN_TEMPLATE_NAME, "variables": [], "config1": config_id}, verify=False)

    if create_staging_response.status_code == 200:
        print("✅  SEMS SEALMAN template successfully initialized.")
        staging_id = create_staging_response.json()["id"]
    else:
        print(f"❌  Failed to initialized SEMS SEALMAN template. HTTP status code: {create_staging_response.status_code}")
        sys.exit(2)

    select_stating_response = requests.post(f"{SEMS_URL}/web/api/templateversion/select/staging/{staging_id}",
                                         headers=headers, json={},
                                         verify=False)

    if select_stating_response.status_code == 200:
        print("✅  SEMS SEALMAN template successfully set to staging.")
    else:
        print(
            f"❌  Failed to set SEMS SEALMAN template to staging. HTTP status code: {select_stating_response.status_code}")
        sys.exit(2)


    select_prod_response = requests.post(f"{SEMS_URL}/web/api/templateversion/select/production/{staging_id}",
                                            headers=headers, json={},
                                            verify=False)


    if select_prod_response.status_code == 200:
        print("✅  SEMS SEALMAN template successfully set to production.")
    else:
        print(
            f"❌  Failed to set SEMS SEALMAN template to production. HTTP status code: {select_prod_response.status_code}")
        sys.exit(2)



def main():
    config_id = create_sealman_sems_config()
    create_sealman_sems_template(config_id)
    create_sealman_iothub_deployment()
    # TODO register SEMS VPN user + VPN container client

if __name__ == "__main__":
    main()