import os
import csv

from utils import run_linux_cmd, run_linux_system


# parse activate.txt and stapL.txt
# get: (function, file_path) list which been activated by workload
# mutate above functions and dump them to mutate dir
# dump fault.csv


def get_fun_file_lst():
	tmp_fun_lst = list()
	activate_fun_file_lst = list()

	with open("activate.txt", "r") as fd:
		for line in fd.readlines():
			line = line.strip()
			if len(line) > 0 and line not in tmp_fun_lst:
				tmp_fun_lst.append(line)

	with open("stapL.txt", "r") as fd:
		for line in fd.readlines():
			line = line.strip()
			if len(line) == 0:
				continue
			
			fun = line.split("@")[0]
			fun = fun.split('"')[-1]

			file = line.split("@")[1]
			file = file.split(':')[0]

			if fun in tmp_fun_lst:
				 activate_fun_file_lst.append([fun, file])

	return activate_fun_file_lst


def check_dir(dir_path):
	if not os.path.exists(dir_path):
		print('mkdir ' + dir_path)
		os.mkdir(dir_path)


def loop_and_mutate(activate_fun_file_lst):
	m_file_info_lst = list()

	for fun, file in activate_fun_file_lst:
		# check file exist
		if not os.path.exists(file):
			print("mutate: the file not exist: ", file, fun)
			continue

		# prepare dir for the mutated file
		filename = file.split('/')[-1]
		basedir = file[:file.rfind('/')+1] + 'mutate'
		check_dir(basedir)

		basedir = basedir + '/' + filename
		check_dir(basedir)

		basedir = basedir + '/' + fun
		check_dir(basedir)

		# do mutate
		mutate_op = ["omfc", "omviv", "omvav", "omvae", "omia", "omifs", "omieb", "omlc", "omlpa", "owvav", "owpfv", "owaep"]
		for op in mutate_op:
			mutate_dir = basedir + '/' + op
			cmd = op + ' ' + file + ' -f ' + fun + ' -d ' + mutate_dir  + ' --'
			run_linux_cmd(cmd)

			# scan the mutation dir
			r = run_linux_cmd("ls " + mutate_dir).stdout
			if r != None and r.strip() != "":
				m_files = r.strip().split('\n')
				for mfile in m_files:
					m_file_info_lst.append([op + '-' + fun + '-' + mfile, mutate_dir + '/' + mfile, file])

	return m_file_info_lst


def dump_mutate_csv(m_file_info_lst):
	headers = ['fault name','mutate file path','target file path']

	with open('fault.csv', 'w', encoding='utf8', newline='') as fd :
		writer = csv.writer(fd)
		writer.writerow(headers)
		for name, mfile, tfile in m_file_info_lst:
			writer.writerow([name, mfile, tfile])


def dump_called_csv(m_file_info_lst):
	headers = ['target function', 'target file', 'called functions']
	with open('called.csv', 'w', encoding='utf8', newline='') as fd :
		writer = csv.writer(fd)
		writer.writerow(headers)
		
		tfunction_set = set()
		for name, mfile, tfile in m_file_info_lst:
			tfunction = name.split('-')[1]
			tfunction_set.add((tfile, tfunction))

		for tfile, tfunction in tfunction_set:
			called_lst = list()
			# called tfile -f tfunction --
			cmd = 'called ' + tfile + ' -f ' + tfunction + ' --'
			r = run_linux_cmd(cmd).stdout
			if r != None and r.strip() != "":
				called_lst = r.strip().split('\n')
			writer.writerow([tfunction, tfile, called_lst])


if __name__ == '__main__':
	print("*** start to mutate.")

	activate_fun_file_lst = get_fun_file_lst()
	m_file_info_lst = loop_and_mutate(activate_fun_file_lst)
	dump_mutate_csv(m_file_info_lst)
	dump_called_csv(m_file_info_lst)

	print(m_file_info_lst)
	print("fault number: ", len(m_file_info_lst))

	print("*** end to mutate.")

