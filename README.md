Quick simple helper scripts for extending Grist functionality.
Very early work in progress at the moment.

## Device Inventory

Supports logging of devices asset information based on MAC address and account.
Up to 2 mac addresses (`mac_primary` and `mac_secondary`) can be provided,
and either can match either `Mac_Primary` OR `Mac_Secondary` in the Grist database.

If `mac_primary` matches `Mac_Secondary`, then the fields are swapped in the data so
primary is saved as secondary and vice versa.
This applies to `ip_primary` and `ip_secondary` as well based on the mac address logic.

This is done because a host-based scan will provide both interfaces whereas a network scan
will provide 2 device entries for the same device, one for each interface.

### Fields Tracked

* hostname
* manufacturer
* model
* serial
* hardware_version
* board_manufacturer
* board_model
* board_serial
* cpu_model
* cpu_threads
* mem_type
* mem_speed
* mem_size
* mem_model
* os_name
* os_version
* ip_primary
* ip_secondary
* mac_primary
* mac_secondary

### Endpoint

* Path: `/scripts/device_inventory`
* Method: `POST`
* Required Header: `X-Token: <AccountToken>`
* Content-Type: `application/json`
* Body: JSON object with the device data

### Authentication

This script uses the `Account Token` for basic device authentication and account tracking.
This field should be a random unique string stored in the `Account`.

### Client Libraries

Any script which can generate JSON data and publish to an HTTPS endpoint can be used,
but here are some pre-made scripts which support this collector:

[Device-run collector](https://github.com/eVAL-Agency/ScriptsCollection/tree/main/dist/inventory).
Meant to be run with [TacticalRMM](https://docs.tacticalrmm.com/) but can run standalone.
Features a Python collector for Linux and Powershell for Windows.


## Requirements

* Python 3.10 or newer
* Python venv
* Nginx or other reverse proxy


## Installation

This middleware is designed to work alongside Grist and can be installed behind the same Nginx reverse proxy
that runs Grist.
You **do not** need to install the scripts within Grist or in any specific directory.
Take note that it should be installed with a non-privileged user however, (eg: do not use root).

Example directory structure:

```
/home
  /grist
    /grist-core
    /docs
    /grist-scripts
```

### Obtain Middleware

To install the middleware, just clone the repo ie:

```bash
cd /home/grist
sudo -u grist git clone https://github.com/eVAL-Agency/Grist-Scripts.git grist-scripts
```

The middleware can be run manually for testing by running `./run.sh --dev` from the installation directory
of grist-scripts.
The first run (in either production or dev) will set up the virtual environment for the middleware application.

### Configuration

Copy `config.ini.example` to `config.ini` and edit as necessary.

Notably:

* `host`: URL of your Grist installation without a trailing slash
* `api_key`: User API key from Grist (Profile Settings -> API Key) to use for connecting
* `doc_id`: Document ID of the Grist document to use for storing device data (Document -> Settings -> Document ID)


### Set Up Nginx Proxy

In your nginx config, add the following block inside your https server block:

```nginx
	location ^~ /scripts/ {
		proxy_pass http://127.0.0.1:5000;
		proxy_set_header Host $host;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Forwarded-Proto $scheme;
		proxy_set_header Upgrade $http_upgrade;
		proxy_set_header Connection "upgrade";
		proxy_http_version 1.1;
	}
```

### Set Up SystemD

In order to run this server automatically, a service file needs to be created.

Create a file at `/etc/systemd/system/grist-scripts.service` with the following content:

```ini
[Unit]
Description=Grist-Scripts

[Service]
ExecStart=/home/grist/grist-scripts/run.sh
Restart=always
User=grist
Group=grist
WorkingDirectory=/home/grist/grist-scripts

[Install]
WantedBy=multi-user.target
```

Then enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable grist-scripts
sudo systemctl start grist-scripts
```

Ensure to edit your locations as necessary.