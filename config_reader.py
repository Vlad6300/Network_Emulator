#!/usr/bin/env python3


import argparse
import subprocess
import os
import yaml

def read_config(f):
	yaml_file = open(f)
	yaml_config = yaml.load(yaml_file, Loader=yaml.FullLoader)
	infrastructure = yaml_config['infrastructure']
	return infrastructure['routers'], infrastructure['bridges'], infrastructure['hosts'], infrastructure['links']


def start_hosts(hosts, clean):
	for i in range(len(hosts)):
		cmd = "docker run -d --privileged --name={} --net=none {}:latest tail -f /dev/null".format(hosts[i]['host'],hosts[i]['image'])
		clean.write("docker container stop {}\n".format(hosts[i]['host']))
		clean.write("docker container rm {}\n".format(hosts[i]['host']))
		out = subprocess.run(cmd.split(' '))
		
		


def start_bridges(bridges, clean):
	for i in range(len(bridges['bridge'])):
		cmd = "ovs-vsctl add-br {}".format(bridges['bridge'][i])
		clean.write("ovs-vsctl del-br {}\n".format(bridges['bridge'][i]))
		out = subprocess.run(cmd.split(' '))



def start_links(links):
	for link in links:
		cmd = "sudo ovs-docker add-port {} {} {} --ipaddress={}".format(link['bridge'],link['interface'],link['host'],link['ip'])
		out = subprocess.run(cmd.split(' '))





def start_routers(routers, clean):
	for router in routers:
		cmd = "docker run -d --privileged --name={} --net=none {}:latest tail -f /dev/null".format(router['router'],router['image'])
		clean.write("docker container stop {}\n".format(router['router']))
		clean.write("docker container rm {}\n".format(router['router']))
		out = subprocess.run(cmd.split(' '))
		cmd = "sudo docker exec {} sysctl net.ipv4.ip_forward=1".format(router['router'])
		out = subprocess.run(cmd.split(' '))


def add_routes(hosts):
	for i in range(len(hosts)):
		for route in hosts[i]['routes']:
			cmd = "docker exec {} route add -net {} gw {} dev {}".format(hosts[i]['host'], route['destination_network'], route['gateway'], route['interface'])
			print("Route cmd: ",cmd,"\n")
			out = subprocess.run(cmd.split(' '))

def get_restrictions(host):
	cmd= ['python3','py_sniffer_class.py']
	for rule in host['restrictions']:
		cmd.append('--'+rule['name'])
		cmd.append(rule['argument'])
		print("INNER CMD: ",cmd)
	return cmd

def start_sniffers(hosts):
	for i in range(len(hosts)):
		if hosts[i]['type'] == 'sniffer':
			cmd = ['docker','exec',hosts[i]['host']]
			cmd = cmd +get_restrictions(hosts[i])
			print("CMD: ",cmd)
			out = subprocess.Popen(cmd)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-f','--file',default='config.yml',help='Set input yaml file')

	parser.add_argument('-cf','--cleanup', default='clean.sh', help='Set output clean-up file')

	args = parser.parse_args()
	
	routers, bridges, hosts, links = read_config(args.file)

	
	
	clean = open(args.cleanup, 'w')
	clean.write('#!/bin/bash\n')


	start_hosts(hosts, clean)
	start_bridges(bridges, clean)
	start_routers(routers, clean)
	start_links(links)
	add_routes(hosts)
	start_sniffers(hosts)

	clean.close()
	

if __name__ == '__main__':
	main()
