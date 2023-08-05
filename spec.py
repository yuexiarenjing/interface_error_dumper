import argparse
import csv
import subprocess
import os

from utils import run_linux_cmd, run_linux_system


# 根据生成的fault.csv, called.csv生成追踪spec


# define error handler functions for the target program, plz fill it manually
err_funs = []  # for astar, no error handler function
		
def get_switch_script():
	script = 'global activate = 0\n'
	script += 'global ccount = 0'
	return script


def get_fun_script(bin_path, fun):
	script = 'probe process("' + bin_path + '").function("' + fun + '")\n'
	script += '{\n'
	script += '\tccount += 1\n'
	script += '\tif(ccount >= 1000) {\n'
	script += '\t\texit()\n'
	script += '\t}\n'
	script += '\tprintf("' + fun + ',call,%s\\n", $$parms$$$)\n'
	script += '}\n'
	return script


def get_call_script(bin_path, fun, is_target_function):
	script = 'probe process("' + bin_path + '").function("' + fun + '").call\n'
	script += '{\n'
	script += '\tccount += 1\n'
	script += '\tif(ccount >= 1000) {\n'
	script += '\t\texit()\n'
	script += '\t}\n'
	if is_target_function:
		script += '\tactivate = 1\n'
	script += '\tprintf("' + fun + ',call,%s\\n", $$parms$$$)\n'
	script += '}\n'
	return script


def get_statement_script(bin_path, fun, file, line):
	script = 'probe process("' + bin_path + '").statement("' + fun + '@' + file + ':' + line + '")\n'
	script += '{\n'
	script += '\tprintf("' + fun + ',statement,%s\\n", $$parms$$$)\n'
	script += '}\n'
	return script


def get_return_script(bin_path, fun, is_target_function):
	script = 'probe process("' + bin_path + '").function("' + fun + '").return\n'
	script += '{\n'
	if is_target_function:
		script += '\tactivate = 0\n'
	script += '\tprintf("' + fun + ',return,%s\\n", $$return$$$)\n'
	# if is_target_function:
	# 	script += '\texit()\n'
	script += '}\n'
	return script


def get_global_script(execname):
	script = 'probe syscall.open.return, syscall.openat.return\n'
	script += '{\n'
	script += '\tif (execname() == "' + execname + '" && activate == 1) {\n'
	script += '\t\tsbuf = user_string_quoted(@entry($filename))\n'
	script += '\t\tif (!isinstr(sbuf, "so")) {\n'
	script += '\t\t\tprintf("open(%d): filename = %s\\n", $return, sbuf)\n'
	script += '\t\t}\n'
	script += '\t}\n'
	script += '}\n\n'

	script += 'probe syscall.read.return, syscall.pread.return\n'
	script += '{\n'
	script += '\tif (execname() == "' + execname + '" && activate == 1) {\n'
	script += '\t\tsbuf = user_string_quoted(@entry($buf))\n'
	script += '\t\tif (!isinstr(sbuf, "ELF")) {\n'
	script += '\t\t\tprintf("read(%d): buf = %s\\n", @entry($fd), sbuf)\n'
	script += '\t\t}\n'
	script += '\t}\n'
	script += '}\n\n'

	script += 'probe syscall.write, syscall.pwrite\n'
	script += '{\n'
	script += '\tif (execname() == "' + execname + '" && activate == 1) {\n'
	script += '\t\tprintf("write(%d): buf = %s\\n", $fd, user_string_quoted($buf))\n'
	script += '\t}\n'
	script += '}\n\n'

	script += 'probe syscall.connect\n'
	script += '{\n'
	script += '\tif (execname() == "' + execname + '" && activate == 1) {\n'
	script += '\t\tprintf("connect(%d): ip = %s, address = %s\\n", sockfd, uaddr_ip, uaddr_ip_port)\n'
	script += '\t}\n'
	script += '}\n\n'

	script += 'probe kernel.function("sys_recvfrom").return, kernel.function("sys_recv").return\n'
	script += '{\n'
	script += '\tif (execname() == "' + execname + '" && activate == 1) {\n'
	script += '\t\tif ($return >= 0) {\n'
	script += '\t\t\tprintf("recv(%d): buf = %s\\n", @entry($fd), kernel_string_quoted(@entry($ubuf)))\n'
	script += '\t\t}\n'
	script += '\t}\n'
	script += '}\n\n'

	script += 'probe syscall.sendto, syscall.send\n'
	script += '{\n'
	script += '\tif (execname() == "' + execname + '" && activate == 1) {\n'
	script += '\t\tprintf("send(%d): buf = %s\\n", s, kernel_string_quoted(buf_uaddr))\n'
	script += '\t}\n'
	script += '}\n\n'

	return script


def get_signal_script(bin_path, execname):
	# for exit code
	script = 'probe syscall.exit_group\n'
	script += '{\n'
	script += '\tif(execname() == "' + execname + '") {\n'
	script += '\t\tprintf("error_code:%ld\\n", $error_code)\n'
	script += '\t}\n'
	script += '}\n\n'

	# for signal (OS Exception)
	script += 'probe signal.send\n'
	script += '{\n'
	script += '\tif(pid_name == "' + execname + '") {\n'
	script += '\t\tprintf("sig_name:%s\\n", sig_name)\n'
	script += '\t}\n'
	script += '}\n\n'

	# for error handler functions
	for e_fun in err_funs:
		script += 'probe process("' + bin_path + '").function("' + e_fun + '")\n'
		script += '{\n'
		script += '\tprintf("error_handler_function: ' + e_fun + ' is called\\n")\n'
		script += '}\n\n'

	script += 'probe process("/lib64/libc.so.6").function("abort")\n'
	script += '{\n'
	script += '\tif(execname() == "' + execname + '") {\n'
	script += '\t\tprintf("error_handler_function: assert fail, abort occor\\n")\n'
	script += '\t}\n'
	script += '}\n\n'

	return script


def read_called_csv():
	fun_called_lst = list()
	with open('called.csv', "r", encoding='utf8', newline='') as fd:
		reader = csv.reader(fd)
		isheader = True
		for row in reader:
			if isheader:
				isheader = False
				continue  # skip header
			tfunction, tfile, called_lst = row
			called_lst = called_lst[1:-1].split(',')
			if len(called_lst) == 1 and called_lst[0] == '':
				called_lst = list()
			for i in range(len(called_lst)):
				called_lst[i] = called_lst[i].strip("'")
			fun_called_lst.append([tfunction, tfile, called_lst])
	return fun_called_lst 


def is_call_return_valid(bin_path, fun):
	probe = "'" + 'process("' + bin_path + '").function("' + fun + '").return' + "'"
	cmd = 'stap -L ' + probe
	r = run_linux_cmd(cmd).stdout
	if r != None and r.find(fun) != -1:
		return True
	return False


def gen_script4fun(bin_path, function, is_target_function, file, lines):
	script = ""
	if is_target_function:
		script += get_switch_script() + "\n"
	if is_call_return_valid(bin_path, function):
		script += get_call_script(bin_path, function, is_target_function) + "\n"
		script += get_return_script(bin_path, function, is_target_function) + "\n"
	else:
		script += get_fun_script(bin_path, function) + "\n"
	if len(lines) == 1 and lines[0] == -1:
		pass  # no statement point
	else: 
		for line in lines:
			script += get_statement_script(bin_path, function, file, str(line)) + "\n"
	return script


def gen_script4global(bin_path):
	execname = bin_path.split('/')[-1]
	script = get_global_script(execname)
	script += get_signal_script(bin_path, execname)
	return script


def get_line(bin_path, function, file):
	# get stapL list 
	line_lst = list()
	cmd = 'stap -L ' + "'" +  'process("' + bin_path + '").statement("' + function + '@*:*")' + "'"
	r = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
	out = r.stdout.decode('utf-8')
	for ele in out.split('\n'):
		if ele.strip() != "" and ele.find(file) != -1:
			line = ele.split(':')[1].split('"')[0]
			line_lst.append(int(line))
	line_lst.sort()

	# get statement list
	last_line = -1
	return_line_lst = list()
	cmd = 'statement ' + file + ' -f ' + function + ' --'
	print(cmd)
	r = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
	out = r.stdout.decode('utf-8')
	for ele in out.split('\n'):
		if ele.find("last line") != -1:
			last_line = int(ele.split(':')[1].strip())
			if last_line not in line_lst:
				last_line = -1
		elif ele.find("Return at line") != -1:
			return_line = int(ele.split(':')[1].strip())
			if return_line in line_lst:
				return_line_lst.append(return_line)

	# check whether last stapL line is }
	if len(line_lst) != 0 and last_line != -1:
		if line_lst[-1] == last_line:
			return [last_line]

	# check if return exist
	if len(return_line_lst) != 0:
		return return_line_lst

	# other: last stapL line
	if len(line_lst) != 0:
		return [line_lst[-1]]

	# no statement point
	return [-1]


def get_file(function):
	file = ""
	with open('called.csv', "r", encoding='utf8', newline='') as fd:
		reader = csv.reader(fd)
		for row in reader:
			tfunction, tfile, called_lst = row
			if function == tfunction:
				file = tfile
	return file


# gen the normal trace script list
def get_normal_script_lst(bin_path):
	normal_script_lst = list()
	for tfunction, tfile, called_lst in read_called_csv():
		# fill target function script
		lines = get_line(bin_path, tfunction, tfile)
		script = gen_script4fun(bin_path, tfunction, True, tfile, lines)
		# fill called function script
		for called in called_lst:
			file = get_file(called)
			if file == "":
				continue
			lines = get_line(bin_path, called, file)
			script += gen_script4fun(bin_path, called, False, file, lines)
		# fill global script
		script += gen_script4global(bin_path)
		filename = tfile.split('/')[-1]
		script_name = tfunction + '-' + filename + '.stp'
		normal_script_lst.append([script_name, script])
	return normal_script_lst


def dump_normal_script_lst(bin_path):
	if not os.path.exists("normal_scripts"):
		os.mkdir("normal_scripts")
	for script_name, script in get_normal_script_lst(bin_path):
		with open("normal_scripts/" + script_name, "w") as fd:
			fd.write(script)


def get_fault_script(bin_path, tfunction, tfile):
	# fill target function script
	lines = get_line(bin_path, tfunction, tfile)
	script = gen_script4fun(bin_path, tfunction, True, tfile, lines)
	# fill called function script	
	for function, file, called_lst in read_called_csv():
		if function != tfunction or file != tfile:
			continue
		for called in called_lst:
			file = get_file(called)
			if file == "":
				continue
			lines = get_line(bin_path, called, file)
			script += gen_script4fun(bin_path, called, False, file, lines)
		break
	# fill global script
	script += gen_script4global(bin_path)
	return script


def dump_fault_script(bin_path, tfunction, tfile, script_name):
	if not os.path.exists("fault_scripts"):
		os.mkdir("fault_scripts")
	script = get_fault_script(bin_path, tfunction, tfile)
	with open("fault_scripts/" + script_name, "w") as fd:
		fd.write(script)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='A tool for gen trace spec.')
	parser.add_argument('bin_path', help='bin path')
	args = parser.parse_args()

	print("*** start to generate trace specification.")

	dump_normal_script_lst(args.bin_path)

	print("*** end to generate trace specification.")
