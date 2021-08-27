#!/usr/bin/env python3

from ibm_vpc import VpcV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from multiprocessing import Process
import os
import time
import sys
import config

# Configuration values
vpc_name = sys.argv[1]
failover_subnets = []
#failover_subnets = [{'primary_route_name': "vpn-route",
#					 'secondary_route_name': "direct-link-and-vpn",
#					 'target_host': "193.38.60.239"
#					},
#					{'primary_route_name': "new-test",
#					 'secondary_route_name': "vpn-route",
#					 'target_host': "8.8.8.8"
#					}
#				   ]

class SnItem:
	def __init__(self, primary_table, secondary_table, trigger):
		self.primary_route_name = primary_table
		self.secondary_route_name = secondary_table
		self.target_host = trigger

def switch_table(vpc_nm, sn_info):
	
	authenticator = IAMAuthenticator(config.api_key)
	service = VpcV1(authenticator=authenticator)
	service.set_service_url(config.base_url)

	try:
		vpc_collection = service.list_vpcs().get_result()['vpcs']

	except ApiException as e:
		print("list_vpcs() failed with status code " + str(e.code) + ": "+ e.message)

	vpc_id = ''
	for vpc in vpc_collection:
		print(vpc['name'], vpc['id'])
		if vpc['name'] == vpc_nm:
			vpc_id = vpc['id']
	# TODO FAILURE CODE

	# Build a map of routing tables available
	try:
		route_tables = service.list_vpc_routing_tables(vpc_id).get_result()['routing_tables']
	except ApiException as e:
		print("list_routing_tables() failed with status code " + str(e.code) + ": " + e.message)

	route_table_map = {}
	for route_table in route_tables:
		route_table_map[route_table['name']] = route_table['id']
	print(route_table_map)

	# Get the list of subnets for the primary table
	primary_table_name = sn_info.primary_route_name
	primary_route_id = route_table_map[primary_table_name]
	print(primary_route_id)
	secondary_table_name = sn_info.secondary_route_name
	secondary_table_id = route_table_map[secondary_table_name]
	print(secondary_table_id)
	
	try:
		attached_subnet_list = service.get_vpc_routing_table(vpc_id, primary_route_id).get_result()['subnets']
	except ApiException as e:
		print("get_vpc_routing_table(): failed with status code " + str(e.code) + ": " + e.message)
	print(attached_subnet_list)
	
	# Switch all subnets to the alternate table
	routing_table_identity_model = {
		'id': secondary_table_id,
	}

	for subnet in attached_subnet_list:
		try:
			response = service.replace_subnet_routing_table(
				id=subnet['id'],
				routing_table_identity=routing_table_identity_model
			).get_result()
		except ApiException as e:
			print("replace_subnet_routing_table() failed with status code " + str(e.code) + ": "+ e.message)
		
		
if __name__ == '__main__':		
	# Get the name of the subnets to switch primary, secondary_route_name
	failover_subnets.append(SnItem(sys.argv[2], sys.argv[3], "8.8.8.8"))
	
	#Start a process to handle each subnet
	for sn in failover_subnets:
	#	Process(target=monitor_process, args=(vpc_name, sn)).start()
		result = switch_table(vpc_name, sn)







