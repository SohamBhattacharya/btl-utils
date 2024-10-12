import argparse
import os
import re

class Formatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawTextHelpFormatter
): pass

def run_cmd_list(l_cmd, debug = False) :
    
    for cmd in l_cmd :
        
        if (debug) :
            
            print(f"Trying command: {cmd}")
        
        retval = os.system(cmd)
        
        if (retval) :
            
            exit()


def natural_sort(l):
    
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key = alphanum_key)