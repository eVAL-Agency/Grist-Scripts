from flask import Flask
from flask import request
import configparser
import json

from libs.grist import Grist
from libs.device import device_inventory

app = Flask(__name__)

config = configparser.ConfigParser()
# Read default settings from mappings first
config.read('mappings.ini')
# Allow user to override everything in their custom config.
config.read('config.ini')
grist = Grist(config)


def generate_response(status: int, message: str, data: dict = None):
	if data is None:
		data = {}

	data['status'] = status
	if 200 <= status <= 299:
		data['success'] = message
	else:
		data['error'] = message

	return app.response_class(
		status=status,
		mimetype='application/json',
		response=json.dumps(data)
	)


@app.route('/scripts/device_inventory', methods=['POST'])
def run_device_inventory():
	if request.content_type != 'application/json':
		return generate_response(401, 'Script only supports application/json')

	if 'X-Token' not in request.headers:
		return generate_response(400, 'Missing X-Token header')

	# Lookup the account for this token
	account = grist.get('Accounts', filter={'Token': [request.headers['X-Token']]}, limit=1)
	if account is None:
		return generate_response(403, 'Invalid / unauthorized token')

	try:
		request_data = request.json
	except Exception:
		return generate_response(415, 'Invalid or corrupt JSON data provided')

	code, message, data = device_inventory(config, grist, account, request_data)
	return generate_response(code, message, data)
