from configparser import ConfigParser

from libs.grist import Grist


def device_inventory(config: ConfigParser, grist: Grist, account: dict, data: dict):
	"""
	Process device inventory data for a given account.

	:param config: System configuration settings, loaded from config.ini
	:param grist: An instance of the Grist class for database operations.
	:param account: A dictionary representing the account information.
	:param data: A dictionary containing device inventory data.
	:return: A string indicating the result of the operation.
	"""

	if 'mac_primary' not in data and 'mac_secondary' not in data:
		return "No MAC address provided", 400

	macs = []
	if 'mac_primary' in data:
		macs.append(data['mac_primary'])
	if 'mac_secondary' in data:
		macs.append(data['mac_secondary'])

	# List of fields which should not trigger a change note
	silent_keys = ['discover_log', 'account', 'status']

	# Override a few fields on the incoming data
	data['status'] = 'Active'
	data['account'] = account['id']

	# Assemble the payload to send to the spreadsheet
	fields = {}
	log = ''

	# Find the device under the given account with one of the MAC addresses as either its primary or secondary.
	id = None
	device = grist.get('Devices', filter={
		config.get('devices', 'account'): [account['id']],
		config.get('devices', 'mac_primary'): macs,
	}, limit=1)
	if device:
		id = device['id']
	else:
		device = grist.get('Devices', filter={
			config.get('devices', 'account'): [account['id']],
			config.get('devices', 'mac_secondary'): macs,
		}, limit=1)
		if device:
			id = device['id']

	if device:
		# Allow MAC and IP addresses to change between primary and secondary, based on the sheet.
		# This is because a scan may retrieve a wired NIC and WIFI card and log them both as primary.
		if ('mac_primary' in data and
			config.get('devices', 'mac_secondary') in device['fields'] and
			data['mac_primary'] == device['fields'][config.get('devices', 'mac_secondary')]
		):
			if 'mac_secondary' in data:
				m = data['mac_secondary']
				data['mac_secondary'] = data['mac_primary']
				data['mac_primary'] = m
			else:
				data['mac_secondary'] = data['mac_primary']
				del data['mac_primary']

			if 'ip_secondary' in data:
				m = data['ip_secondary']
				data['ip_secondary'] = data['ip_primary']
				data['ip_primary'] = m
			else:
				data['ip_secondary'] = data['ip_primary']
				del data['ip_primary']
		elif ('mac_secondary' in data and
		      config.get('devices', 'mac_primary') in device['fields'] and
		      data['mac_secondary'] == device['fields'][config.get('devices', 'mac_primary')]
		):
			if 'mac_primary' in data:
				m = data['mac_primary']
				data['mac_primary'] = data['mac_secondary']
				data['mac_primary'] = m
			else:
				data['mac_primary'] = data['mac_secondary']
				del data['mac_secondary']

			if 'ip_primary' in data:
				m = data['ip_primary']
				data['ip_primary'] = data['ip_secondary']
				data['ip_secondary'] = m
			else:
				data['ip_primary'] = data['ip_secondary']
				del data['ip_secondary']

	if device:
		# Device exists, selectively update changed records and keep a tally of changes.
		changes = []
		for k, v in data.items():
			db_k = config.get('devices', k)
			if v is not None and db_k and db_k in device['fields']:
				if device['fields'][db_k] != v:
					if k not in silent_keys:
						changes.append(f"{db_k} changed from [{device['fields'][db_k]}] to [{v}]")
					fields[db_k] = v

		if len(changes) > 0:
			log = 'Detected changes from inventory update:\n\n* ' + '\n* '.join(changes)

		if len(fields) > 0:
			grist.update(config.get('devices', '_table'), id, fields)
	else:
		log = 'New device added from inventory update.'
		for k, v in data.items():
			db_k = config.get('devices', k)
			if v is not None and db_k:
				fields[db_k] = v

		id = grist.add(config.get('devices', '_table'), fields)

	# Create a note entry of the changes
	if log:
		log_data = {
			config.get('notes', 'device'): id,
			config.get('notes', 'note'): log,
		}
		grist.add(config.get('notes', '_table'), log_data)
	return 'Saved device inventory successfully', 200
