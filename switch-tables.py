#!/usr/bin/env python3

from ibm_vpc import VpcV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from multiprocessing import Process
import os
import time
import config

# Configuration values
vpc_name = "vpn-test-temp"
failover_subnets = [{'sn_name': "vpn-failover-test-subnet",
					 'primary_route_name': "vpn-route",
					 'secondary_route_name': "direct-link-and-vpn",
					 'target_host': "193.38.60.239"
					},
					{'sn_name': "vpn-test-sub2",
					 'primary_route_name': "new-test",
					 'secondary_route_name': "vpn-route",
					 'target_host': "8.8.8.8"
					}
				   ]

def monitor_process(vpc_nm, sn_info):
	
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
		if vpc['name'] == vpc_nm:remote-monitoring.py
			vpc_id = vpc['id']
	# TODO FAILURE CODE

	# Get the IDs for the two routing tables
	try:
		route_tables = service.list_vpc_routing_tables(vpc_id).get_result()['routing_tables']
	except ApiException as e:
		print("list_routing_tables() failed with status code " + str(e.code) + ": " + e.message)

	primary_table_id = ''
	secondary_table_id = ''
	for route_table in route_tables:
		if route_table['name'] == sn_info['primary_route_name']:
			primary_table_id = route_table['id']
		if route_table['name'] == sn_info['secondary_route_name']:
			secondary_table_id = route_table['id']
	print("Obtained tables " + primary_table_id + ", " + secondary_table_id)

	# Determine which routing table is currently in use
	using_primary_table = False
	try:
		subnet_collection = service.list_subnets().get_result()['subnets']
	except ApiException as e:
		print("list_subnets() failed with status code " + str(e.code) + ": "+ e.message)

	subnet_id = ''
	for subnet in subnet_collection:
		if subnet['name'] == sn_info['sn_name']:
			subnet_id = subnet['id']
			try:
				table_in_use = service.get_subnet_routing_table(subnet['id']).get_result()['id']
			except ApiException as e:
				print("get_subnet_routing_table() failed with status code " + str(e.code) + ": " + e.message)
			using_primary_table = table_in_use == primary_table_id

	while 1:

		#we set success_count to 0
		success_count = 0

		#here we check if ping is successful and collect statistics
		for count in range(0, 4):
			response = os.system("ping -c 1 " + sn_info['target_host'])
			if response == 0:
				success_count +=1
			else:
				success_count -=1

		if success_count < 4:
			print("HOST is DOWN")
			if using_primary_table:
				routing_table_identity_model = {
					'id': secondary_table_id,
				}

				try:
					response = service.replace_subnet_routing_table(
						id=subnet_id,
						routing_table_identity=routing_table_identity_model
					).get_result()
				except ApiException as e:
					print("replace_subnet_routing_table() failed with status code " + str(e.code) + ": "+ e.message)
				using_primary_table = False
			
		else:
			print("HOST IS UP")
			if not using_primary_table:
				routing_table_identity_model = {
					'id': primary_table_id,
				}

				try:
					response = service.replace_subnet_routing_table(
						id=subnet_id,
						routing_table_identity=routing_table_identity_model
					).get_result()
				except ApiException as e:
					print("replace_subnet_routing_table() failed with status code " + str(e.code) + ": "+ e.message)
				using_primary_table = True

	
		#we are sleeping 5 sec before new cycle
		time.sleep(5)
		
if __name__ == '__main__':		
	# Get the ID of the VPC
	
	#Start a process to handle each subnet
	for sn in failover_subnets:
		Process(target=monitor_process, args=(vpc_name, sn)).start()







