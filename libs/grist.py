from configparser import ConfigParser
import requests
import json


class Grist:
	def __init__(self, config: ConfigParser):
		self.api_key = config.get('grist', 'api_key')
		self.host = config.get('grist', 'host')
		self.doc_id = config.get('grist', 'doc_id')

	def get(self, table: str, filter: dict = None, sort: str = None, limit: int = None):
		"""
		Get records from a Grist document and table.

		:param table: The table name.
		:param filter: A dictionary to filter records (e.g., {"ColumnName": "Value"}).
		:param sort: A string to sort records (e.g., "ColumnName" or "-ColumnName" for descending).
		:param limit: An integer to limit the number of records returned.
		:return: A list of records matching the criteria.
		:see: https://support.getgrist.com/api/#tag/records/operation/listRecords
		"""

		base_url = f"{self.host}/api/docs/{self.doc_id}/tables/{table}/records"
		headers = {
			"Authorization": f"Bearer {self.api_key}",
			"Content-Type": "application/json"
		}

		params = {}

		if filter:
			params['filter'] = json.dumps(filter)

		if sort:
			params['sort'] = sort

		if limit:
			params['limit'] = limit

		response = requests.get(base_url, headers=headers, params=params)

		if response.status_code == 200:
			records = response.json().get('records', [])
			if limit == 1:
				return records[0] if records else None
			else:
				return records
		else:
			response.raise_for_status()

	def add(self, table: str, fields: dict):
		"""
		Add a new record to a Grist document and table.

		:param table: The table name.
		:param fields: A dictionary of field names and their values for the new record.
		:return: The created record ID upon a successful creation.
		:see: https://support.getgrist.com/api/#tag/records/operation/addRecords
		"""

		url = f"{self.host}/api/docs/{self.doc_id}/tables/{table}/records"
		headers = {
			'Authorization': f"Bearer {self.api_key}",
			'Content-Type': 'application/json'
		}
		payload = {
			'records': [{'fields': fields}]
		}

		response = requests.post(url, headers=headers, json=payload)

		if response.status_code == 200 or response.status_code == 201:
			return response.json()['records'][0]['id']
		else:
			response.raise_for_status()

	def update(self, table: str, id: int, fields: dict):
		"""
		Add a new record to a Grist document and table.

		:param table: The table name.
		:param fields: A dictionary of field names and their values for the new record.
		:return: The created record.
		:see: https://support.getgrist.com/api/#tag/records/operation/addRecords
		"""

		url = f"{self.host}/api/docs/{self.doc_id}/tables/{table}/records"
		headers = {
			'Authorization': f"Bearer {self.api_key}",
			'Content-Type': 'application/json'
		}
		payload = {
			'records': [{'id': id, 'fields': fields}]
		}

		response = requests.patch(url, headers=headers, json=payload)

		if response.status_code == 200 or response.status_code == 201:
			return response.json()
		else:
			response.raise_for_status()