#!/usr/bin/env python3

import argparse
import pyvisa

import python.utils as utils
from utils import logging


def main() :
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class = utils.Formatter,
        description = "Control power supply",
    )
    
    parser.add_argument(
        "--res",
        help = "Resource path",
        type = str,
        required = False,
        default = "/dev/ttyACM0",
    )
    
    parser.add_argument(
        "--state",
        help = "Power state of the power supply",
        type = str,
        required = True,
        choices = ["OFF", "ON"],
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    resource_name = f"ASRL{args.res}::INSTR"
    visa_rm = pyvisa.ResourceManager()
    l_visa_resources = visa_rm.list_resources()
    
    if resource_name in l_visa_resources:
        try:
            visa_vm = visa_rm.open_resource(resource_name)
            visa_vm.write(args.state)
        
        except Exception as exc:
            logging.error(f"Error with resource {resource_name}: {exc}")
            
            if "Permission denied" in str(exc) :
                logging.error(f"Permission denied for resource {args.res}. Run: sudo chmod 666 {args.res}")
    
    else :
        logging.error(f"Resource {resource_name} not found in available resources:")
        print("\n".join(utils.natural_sort(l_visa_resources)))
        return 1
    
    return 0

if __name__ == "__main__":
    main()
