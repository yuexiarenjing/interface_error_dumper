# Overview

This is a function call interface tracing tool for collecting interface data. It can be used with the code muation tool to get the interface data under fault injection.

# Requirements

SystemTap 4.0/0.176

Python 3.8

code mutation tool: [GitHub - yuexiarenjing/code_mutation_tool: This is a code mutation based fault injection tool for C/C++ programs.](https://github.com/yuexiarenjing/code_mutation_tool) Note: configure $PATH for the 12 fault injector.

# Userage` `example

Configre the following files for the target program (the example files were given for SPECint 2006:astar).

1. build.sh：the build cmd for the target program, please add -g option and remove optimization like -O2;

2. run.sh：cmd for running the workload for the target program;

3. run_fault.py：configure out_err_files and out_byte_size in line 14 and line 15. For exmaple, for SPECint 2006:astar, it output  program output to lake.out, output errors to lake.err. For out_byte_size = [779] , 779 bits is the size of output (obtained in fault-free run).

How to use (example for SPECint 2006:astar).

Note: How to configure SPECint 2006 benchmark program reference to https://www.spec.org/cpu2006/docs/runspec-avoidance.html.

```bash
# gen activate.txt and stapL.txt
python activate.py /root/workload/astar/astar  
# run the workload
./run.sh
# when the workload run complete, Ctrl+C for python activate.py cmd
# generate code mutations into mutate directory
python mutate.py  # gen fault.csv:fault list, called.csv:activiated funcions list
# generate normal_traces directory and files
python spec.py /root/workload/astar/astar  
# run the fault-free experiments
python run_normal.py 
# run the fault injection experiments
python run_fault.py /root/workload/astar/astar
```

The experiments results will be dump to normal_traces and fault_traces directories.
