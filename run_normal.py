import os
import subprocess
import time
import signal
import logging
import csv

from utils import run_linux_cmd, run_linux_system


logging.basicConfig(filename='trace.log', level=logging.DEBUG, format='[%(asctime)s]-%(levelname)s: %(message)s')


def trace_and_execute(trace_script_path, index):
	trace_file_name = trace_script_path.split('/')[-1][:-4] + '-' + str(index)
	cmd_lst = list()
	cmd_lst.append('stap')
	cmd_lst.append('-v')
	cmd_lst.append(trace_script_path)
	cmd_lst.append('-o')
	cmd_lst.append('normal_traces/' + trace_file_name)
	cmd_lst.append('-DMAXSTRINGLEN=51200')

	print('cmd: ', cmd_lst)

	p = subprocess.Popen(cmd_lst, cwd='.', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	
	pass5 = False
	cnt, maxcnt = 0, 30
	while cnt < maxcnt:  # max wait 30s for pass5
		cnt += 1
		if pass5:
			print(f'trace process start, pid: {p.pid}')
			break
		time.sleep(1)
		outerr = str(p.stderr.readline(), 'utf-8')
		while outerr != "":
			if outerr.find("Pass 5: starting run.") != -1:
				pass5 = True
				break
			if outerr.find("error") != -1:
				cnt = 30  # error occur break
				break
			outerr = str(p.stderr.readline(), 'utf-8')

	# then execute the bin
	time.sleep(1)
	cmd = './run.sh'
	run_linux_cmd(cmd)

	# after the execute close the trace
	os.kill(p.pid, signal.SIGINT)

	# True for success
	return pass5


def get_script():
	script_lst = list()
	for root, dirs, files in os.walk("normal_scripts"):
		for file in files:
			path = root + '/' + file
			script_lst.append(path)
	return script_lst


def dump_runtime_csv(time_lst):
	headers = ['trace function','trace file','max runtime under fault-free (s)']

	with open('runtime.csv', 'w', encoding='utf8', newline='') as fd :
		writer = csv.writer(fd)
		writer.writerow(headers)
		for fun, file, maxtime in time_lst:
			writer.writerow([fun, file, maxtime])


def run():
	if not os.path.exists("normal_traces"):
		os.mkdir("normal_traces")
	time_lst = list()
	for path in get_script():
		maxtime = 0
		for i in range(5):
			logging.info(path + " " + str(i))
			start = time.time()
			ret = trace_and_execute(path, i)
			end = time.time()
			if end-start > maxtime:
				maxtime = end-start
			print("ret: ", ret)
			print("run time (s): ", end-start)
			if not ret:
				logging.error("trace failed.")
		script_name = path.split('/')[-1][:-4]
		fun, file = script_name.split('-')
		time_lst.append([fun, file, maxtime])
	dump_runtime_csv(time_lst)


if __name__ == '__main__':
	print("*** start to run normal experiments.")
	logging.info('start to run normal experiments.')

	run()

	print("*** normal experiments run finished.")
	logging.info('normal experiments run finished.')
