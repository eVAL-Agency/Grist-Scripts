from flask import Flask
from flask import request
import configparser

from libs.grist import Grist
from libs.device import device_inventory

app = Flask(__name__)

config = configparser.ConfigParser()
# Read default settings from mappings first
config.read('mappings.ini')
# Allow user to override everything in their custom config.
config.read('config.ini')
grist = Grist(config)

@app.route('/scripts/device_inventory', methods=['POST'])
def run_device_inventory():
	if 'X-Token' not in request.headers:
		return "Missing X-Token header", 400

	# Lookup the account for this token
	account = grist.get('Accounts', filter={'Token': [request.headers['X-Token']]}, limit=1)
	if account is None:
		return "Invalid token", 403

	return device_inventory(config, grist, account, request.json)
