import os
import subprocess
import time
import signal
import logging
import csv
import argparse

from utils import run_linux_cmd, run_linux_system
from spec import dump_fault_script


# .out and .err file which outputted by the target program for astar
out_err_files = ['lake.out', 'lake.err']
out_byte_size = [779]

logging.basicConfig(filename='trace.log', level=logging.DEBUG, format='[%(asctime)s]-%(levelname)s: %(message)s')


def read_fault_csv():
	fault_lst = list()
	with open('fault.csv', "r", encoding='utf8', newline='') as fd:
		reader = csv.reader(fd)
		isheader = True
		for row in reader:
			if isheader:
				isheader = False
				continue  # skip header
			name, mfile, tfile = row
			fault_lst.append([name, mfile, tfile])
	return fault_lst


def backup_file(c_file):
	# if bak not found, then backup.
	filename = c_file.split('/')[-1]
	basedir = c_file[:c_file.rfind(filename)]
	if not os.path.exists(c_file + ".bak"):
		run_linux_system("cp " + c_file + " " + c_file + ".bak")
	

def recover_file(c_file):
	if os.path.exists(c_file):
		run_linux_system("rm -rf " + c_file)
	if not os.path.exists(c_file + ".bak"):
		print("back up file not found for:", c_file)
		exit(0)
	run_linux_system("cp " + c_file + ".bak " + c_file)


def instead_file(tfile, mfile):
	if os.path.exists(tfile) and os.path.exists(mfile):
		run_linux_system("rm -rf " + tfile)
		run_linux_system("cp " + mfile + " " + tfile)
		return 0
	return -1


def compile():
	cmd = './build.sh'
	r = run_linux_cmd(cmd)
	if r.returncode != 0 or r.stderr.find("error") != -1:
		print("compile failed.")
		print(r.stderr)
		logging.error("compile error.")
		return -1
	else:
		print("compile successfull.")
		return 0


# False for timeout (hang)
def execute(max_time):
	cmd_lst = list()
	cmd_lst.append('bash')
	cmd_lst.append('run.sh')
	print('cmd: ', cmd_lst)

	p = subprocess.Popen(cmd_lst, cwd='.', preexec_fn=os.setsid)
	print(f'target process start, pid: {p.pid}')
	# wait
	start = time.time()
	while True:
		end = time.time()
		if end-start > 2*max_time:  # timeout
			os.killpg(os.getpgid(p.pid), signal.SIGTERM)
			return False
		# check if run finished
		if p.poll() is not None:
			break
		time.sleep(0.5)

	return True


def trace_and_execute(trace_script_path, max_time):
	trace_file_name = trace_script_path.split('/')[-1][:-4]
	cmd_lst = list()
	cmd_lst.append('stap')
	cmd_lst.append('-v')
	cmd_lst.append(trace_script_path)
	cmd_lst.append('-o')
	cmd_lst.append('fault_traces/' + trace_file_name)
	cmd_lst.append('-DMAXSTRINGLEN=51200')

	print('cmd: ', cmd_lst)

	p = subprocess.Popen(cmd_lst, cwd='.', stderr=subprocess.PIPE)
	
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
	execute(max_time)

	# after the execute close the trace
	os.kill(p.pid, signal.SIGINT)

	# True for success
	return pass5


def clean_out_err_file(files):
	for file in files:
		if os.path.exists(file):
			run_linux_system("rm -rf " + file)


# False for wrong
def check_wrong_terminated(files):
	for file in files:
		if file.find('.err') != -1:  # is .err and exits
			if (os.path.exists(file) and os.path.getsize(file) > 0) or not os.path.exists(file):
				print(".err size:", os.path.getsize(file))
				return False
		if file.find('.out') != -1:
			if (os.path.exists(file) and os.path.getsize(file) not in out_byte_size) or not os.path.exists(file):
				print(".out size not correct:", os.path.getsize(file))
				return False
	return True


def load_runtime_csv():
	runtime_lst = list()
	with open('runtime.csv', "r", encoding='utf8', newline='') as fd:
		reader = csv.reader(fd)
		isheader = True
		for row in reader:
			if isheader:
				isheader = False
				continue  # skip header
			fun, file, maxtime = row
			runtime_lst.append([fun, file, maxtime])
	return runtime_lst 


# read max timeout from runtime.csv
def get_max_time(fun, file, runtime_lst):
	filename = file.split('/')[-1]
	for normal_fun, normal_file, normal_maxtime in runtime_lst:
		if normal_fun == fun and normal_file == filename:
			return float(normal_maxtime)
	return -1


# if not hang, check crash
# False for crash
def check_crash(fun, file, fault_trace_file_name):
	fault_trace_size = os.path.getsize("fault_traces/" + fault_trace_file_name)
	filename = file.split('/')[-1]
	normal_trace_file_name_prefix = fun + '-' + filename
	for wroot, wdirs, wfiles in os.walk("normal_traces"):
		for wfile in wfiles:
			if wfile.find(normal_trace_file_name_prefix) != -1:
				# compare the file size
				normal_trace_size = os.path.getsize("normal_traces/" + wfile)
				if fault_trace_size < 0.5 * normal_trace_size:
					return False
	return True


def run(bin_path):
	if not os.path.exists("fault_traces"):
		os.mkdir("fault_traces")

	# load normal runtime list for fun,file pair
	runtime_lst = load_runtime_csv()

	for name, mfile, tfile in read_fault_csv():
		logging.info(name)

		# backup tfile
		backup_file(tfile)

		# instead tfile with mfile
		if instead_file(tfile, mfile) == -1:
			print("instead file failed:", tfile, mfile)
			exit(0)

		# compile
		if compile() == -1:
			recover_file(tfile)
			continue

		# gen trace script
		tfunction = name.split('-')[1]
		script_name = name + '.stp'
		script = dump_fault_script(bin_path, tfunction, tfile, script_name)
		script_path = "fault_scripts/" + script_name

		# clean .out and .err file
		clean_out_err_file(out_err_files)

		# trace and execute
		max_time = get_max_time(tfunction, tfile, runtime_lst)
		start = time.time()
		ret = trace_and_execute(script_path, max_time)
		end = time.time()

		# chech hang (timeout)
		if end-start > 2*max_time:
			print(end-start)
			print(max_time)
			logging.error("hang (timeout).")
		else:
			# check crash
			# if trace records short than fault-free and not hang, then classify it to crash
			if not check_crash(tfunction, tfile, name):
				logging.error("program crashed.")

		# check wrong terminated
		if not check_wrong_terminated(out_err_files):
			logging.error("wrong terminated.")

		print("ret: ", ret)
		if not ret:
			logging.error("trace failed.")

		# recover tfile from backup
		recover_file(tfile)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='A tool for run fault experiments.')
	parser.add_argument('bin_path', help='bin path')
	args = parser.parse_args()

	print("*** start to run fault experiments.")
	logging.info('start to run fault experiments.')

	run(args.bin_path)

	print("*** fault experiments run finished.")
	logging.info('fault experiments run finished.')
