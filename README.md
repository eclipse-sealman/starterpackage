# Introduction 
Sealman and SmartEMS docker-compose file startup for local development

# Prerequisites 
#### Azure Cloud
- Azure IoTHub (Standard Tier)
- Azure Blob-Storage
  - Create ``Data-Storage -> Container`` with the name ``iotedge-device-twin``
  - Generate a Blob SAS token for ``iotedge-device-twin`` container (recommendation: make use of access policies)
#### Local Machine (Windows + WSL)
- Python 3 for setup scripts
- For Edge-Device Simulation:
  - VirtualBox (Version 7.1.8) for Windows for simulating Edge-Devices
  - [EG500Mk2](https://stsealiottest.blob.core.windows.net/share/VirtualEG500Mk2-sealman.ova?sp=r&st=2025-05-26T09:18:55Z&se=2025-05-30T17:18:55Z&spr=https&sv=2024-11-04&sr=b&sig=B8w7aK%2Faz8yM5THG1Rly8C5vGtNb%2Ff6BmfOjldDQAx4%3D)


# Start Sealman Platform locally

### Start Infrastructure
- Navigate to ``sealman-iot-platform``
- Make an ``.env.local`` file as copy of the ``.env`` file: 
```shell
cp .env .env.local
```
- Fill missing secrets in ``.env.local``
    
| Variable                      | Description                                                                                         | Example                                                             |
|------------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| `IOT_HUB_NAME`               | Name of your previously created IoT Hub                                                             | `my-iot-hub.azure-devices.net`                                      |
| `SAS_TOKEN`                  | SAS Token of the IoTHub with all permissions                                                        | `SharedAccessSignature <signature>`                                 |
| `BLOB_STORAGE_ACCOUNT`       | Account name of your previously generated storage account                                           | `myaccount.blob.core.windows.net`                                   |
| `BLOB_SAS_TOKEN_MODULE_CONF` | Token to access your previously generated `iotedge-device-twin` container on the storage account   | `si=<access-policy>&spr=https&sv=2024-11-04&sr=c&sig=<signature-key>` |

- Start docker compose with ``.env.local``:

 ```shell
  docker-compose --env-file .env.local -f sealman.yml up
  ```
### Initialize Platform
- Navigate to ``setup``
- Make a ``config.env.local`` file as copy of the ``config.env`` file:
```shell 
cp config.env config.env.local
```
- Fill missing secrets in config.env.local
  Environmentals which need to be set in addition to defaults:
  
| Variable                    | Description                                                                                         | Example                                                        |
|----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| `IOTHUB_URL`               | Name of your previously created IoT Hub                                                             | `my-iot-hub.azure-devices.net`                                 |
| `IOTHUB_SAS_TOKEN`          | SAS Token of the IoTHub with all permissions     | `SharedAccessSignature <signature>` |

- Install missing python requirements if needed
  ```shell
  pip install -r requirements.txt
  ```
- Start init:
```shell
python3 initial_setup.py
```

### Test
Visit:
- SEALMAN API: http://localhost:5000/docs
- SEALMAN UI: http://localhost:3000/
- SEMS: https://localhost:4443/


# Add virtual Edge-Devices
- Navigate to ``setup``
- Make sure that config.env.local has set all required keys
- - Get you local machines WSL IP-Address and note your``WSL-IP``: 
  ```bash
  wsl 
  ip address 
  ```
  ![img.png](docs/img/wsl-ip-address.png)
- Open VirtualBox
  - Import Appliance ``VirtualEG500Mk2-sealman`` from your previous download [EG500Mk2](https://stsealiottest.blob.core.windows.net/share/VirtualEG500Mk2-sealman.ova?sp=r&st=2025-05-26T09:18:55Z&se=2025-05-30T17:18:55Z&spr=https&sv=2024-11-04&sr=b&sig=B8w7aK%2Faz8yM5THG1Rly8C5vGtNb%2Ff6BmfOjldDQAx4%3D)
  ![img.png](docs/img/virtual-box-import.png)
  - Start VM and wait until ready
  - Note that the VM attaches to the Windows host by using NAT and is accessable by SSH via port forwarding on port ``2222`` 

- Configure SEMS for virtual Edge-Device using ``WSL-IP`` and reading the devices serial number ``device-servial-number`` - the default SSH password is ``123456``:
  ```bash
  ssh admin@localhost -p 2222 "device smartems config -U https://<WSL-IP>:4443 -u edgeGateway -p 123456 -s; device get_serialnumber"
  ```
  ![img_1.png](docs/img/get-serial-number.png)


- Add device with previous received``device-serial-number``:
   ```shell
  python3 register_device.py <device-serial-number>
  ```
  ![img.png](docs/img/register-device.png)
- Start sync of virtual edge-device with cloud:
  ```bash
  ssh admin@localhost -p 2222 device smartems check
  ```
  
- wait until it reports OK
  ![img_1.png](docs/img/sems-check-resp.png)
- Visit http://localhost:3000 to explore the status of sync

