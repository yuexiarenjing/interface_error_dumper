import sys
import argparse

from utils import run_linux_cmd, run_linux_system


# 获取目标程序被触发的所有函数，写入activate.txt
# python activate.py <bin_path>

# global functions
# functions[ppfunc()] <<< 1
# probe end { foreach (func in functions) { printf("%s\n") } }


def get_activate_funs(bin_path):
	stp_s = 'global functions\n\nprobe process("' + bin_path + '").function("*") { functions[ppfunc()] <<< 0 }\n\nprobe end { foreach (func in functions) { printf("%s\\n", func) } }'
	stp_cmd = "stap -o activate.txt -e '" + stp_s + "'"
	run_linux_system(stp_cmd)


def get_stap_L(bin_path):
	stp_s = 'process("' + bin_path + '").function("*@*")'
	stp_cmd = "stap -L '" + stp_s + "' > stapL.txt"
	run_linux_system(stp_cmd)


if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='A tool for tracing activate functions for a userspace bin.')
	parser.add_argument('bin_path', help='bin path')
	args = parser.parse_args()

	print("*** start to trace, press ctrl^c to exit.")

	try:
		get_stap_L(args.bin_path)
		get_activate_funs(args.bin_path)
	except KeyboardInterrupt:
		print("*** ctrl^c pressed, exit.")
		sys.exit()
	
