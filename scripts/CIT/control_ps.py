#!/usr/bin/env python3

import argparse
import numpy
import os
import pyvisa
import time

import utils
from utils import logging
from utils import yaml


TIME_INTERVAL = 2 # Seconds
VOLT_INTERVAL = 5 # Volts
VOLT_TOLERANCE = 0.1 # Volts

TRIES_MAX = 5 # Maximum number of tries to reach target voltage


def set_voltage_ch(visa_vm, channel, volt_target, curr_max = None) :
    
    if curr_max is None and volt_target > 0 :
        
        logging.error(f"Max current must be set if target voltage is greater than 0 V")
        return 1
    
    volt_start = float(visa_vm.query(f"MEAS:VOLT? CH{channel}").strip())
    
    volt_steps = numpy.arange(
        start = volt_start,
        stop = volt_target,
        step = (-1)**int(volt_target < volt_start) * VOLT_INTERVAL
    )
    
    if len(volt_steps):
        
        if volt_steps[-1] != volt_target :
        
            volt_steps = numpy.append(volt_steps, [volt_target])
        
        logging.info(f"Voltage steps: {' , '.join([str(_v) for _v in volt_steps])}")
        
        for volt_set in volt_steps :
            
            if curr_max is not None:
                logging.info(f"Setting CH{channel} voltage to {volt_set} V (target {volt_target} V), and maximum current to {curr_max} A ...")
                visa_vm.write(f"APPL CH{channel}, {volt_set} V, {curr_max} A")
            else:
                logging.info(f"Setting CH{channel} voltage to {volt_set} V (target {volt_target} V) ...")
                visa_vm.write(f"APPL CH{channel}, {volt_set} V")

            time.sleep(TIME_INTERVAL)
            
            ntries = 0
            
            while True :
                
                ntries += 1
                
                if ntries > TRIES_MAX :
                    
                    logging.error(f"Failed to reach target voltage {volt_target} V on CH{channel} after {TRIES_MAX-1} attempts")
                    return 1
                
                print_vi_ch(visa_vm, channel)
                volt_read = float(visa_vm.query(f"MEAS:VOLT? CH{channel}").strip())
                
                if abs(volt_read - volt_set) < VOLT_TOLERANCE :
                    break
                
                time.sleep(TIME_INTERVAL)
    
    return 0


def set_voltage(visa_vm, volt_target, curr_max, channel_voltage_limits, channels = []) :
    """
    All channels if channels is empty
    """

    # Set the voltage limit to 0 for unselected channels
    for ichannel in range(len(channel_voltage_limits)) :
        
        channel = ichannel + 1
        
        if channels and (channel not in channels) :
            
            channel_voltage_limits[ichannel] = 0
    
    volt_targets_ch = [
        min(channel_voltage_limits[0], volt_target),
        min(channel_voltage_limits[1], max(0, volt_target-sum(channel_voltage_limits[:1]))),
        min(channel_voltage_limits[2], max(0, volt_target-sum(channel_voltage_limits[:2]))),
    ]
    
    for ichannel, volt_target_ch in enumerate(volt_targets_ch) :
        
        channel = ichannel + 1
        
        if channels and channel not in channels :
            
            continue
        
        retval = set_voltage_ch(
            visa_vm = visa_vm,
            channel = channel,
            volt_target = volt_target_ch,
            curr_max = curr_max,
        )
        
        if retval :
            
            return retval
    
    return 0


def print_vi_ch(visa_vm, channel) :
    
    volt_read = float(visa_vm.query(f"MEAS:VOLT? CH{channel}").strip())
    curr_read = float(visa_vm.query(f"MEAS:CURR? CH{channel}").strip())
    logging.info(f"CH{channel}: {volt_read} V, {curr_read} A")


def print_vi_all(visa_vm, nchannels) :
    
    for channel in range(1, nchannels+1) :
        
        print_vi_ch(
            visa_vm = visa_vm,
            channel = channel,
        )


def reset(visa_vm) :
    
    retval = set_voltage(
        visa_vm = visa_vm,
        volt_target = 0,
        curr_max = None
    )
    
    if retval :
        return retval
    
    visa_vm.write("*RST")
    visa_vm.write("APP:VOLT 0, 0 ,0")
    visa_vm.write("APP:CURR 0, 0 ,0")
    time.sleep(TIME_INTERVAL)
    
    return 0


def main() :
    """
    https://iotexpert.com/pyvisa-first-use/
    """    
    
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class = utils.Formatter,
        description = "Control power supply",
    )
    
    parser.add_argument(
        "--mode",
        help = "Power supply mode", 
        type = str,
        required = True,
        choices = ["HV", "TEC", "LED"],
    )
    
    parser.add_argument(
        "--pscfg",
        help = "Power supply details",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--voltage",
        help = "Set voltage",
        type = float,
        required = False,
        default = None
    )
    
    parser.add_argument(
        "--current",
        help = "Set maximum current",
        type = float,
        required = False,
        default = None
    )
    
    parser.add_argument(
        "--channels",
        help = "If provided, will only use the specified channels. Syntax: <channel1> <channel2> ...",
        type = int,
        required = False,
        default = [],
        nargs = "+"
    )
    
    parser.add_argument(
        "--noreset",
        help = "Will not safely reset the power supply before setting voltage",
        action = "store_true",
        default = False,
    )
    
    parser.add_argument(
        "--poff",
        help = "Power off the power supply",
        action = "store_true",
        default = False,
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    with open(args.pscfg, "r") as fopen :
        
        d_pscfgs = yaml.load(fopen.read())
    
    pscfg = d_pscfgs[args.mode]
    
    channel_voltage_limits = pscfg["channel_voltage_limits"]
    nchannels = len(channel_voltage_limits)
    
    if not args.poff :
        
        assert (args.voltage is not None), "Voltage must be set if not powering off"
        assert (args.current is not None), "Current must be set if not powering off"
        
        assert (args.voltage >= 0 and args.voltage <= pscfg["max_voltage"]), f"Voltage must be between 0 and {pscfg['max_voltage']} V"
        assert (args.current >= 0 and args.current <= pscfg["max_current"]), f"Current must be between 0 and {pscfg['max_current']} A"
        
        assert all([ch <= nchannels for ch in args.channels]), f"Channels must be >=1 and <={nchannels}"
    
    visa_rm = pyvisa.ResourceManager()
    l_visa_resources = visa_rm.list_resources()
    resource = None
    
    for res in l_visa_resources :
        
        try:
            
            visa_vm = visa_rm.open_resource(res)
            
            if res.startswith("ASRL") :
                
                ps_id = visa_vm.query("*IDN?").strip().split(",")
                ps_mfr = str(ps_id[0].strip())
                ps_model = str(ps_id[1].strip())
                ps_sn = str(ps_id[2].strip())
                
                if ps_mfr == str(pscfg["manufacturer"]) and ps_model == str(pscfg["model"]) and ps_sn == str(pscfg["serial_number"]) :
                    
                    resource = res
                    break
        
        except Exception as exc:
            
            logging.warning(f"Error opening resource {res}: {exc}")
            
            if "Permission denied" in str(exc) :
                
                logging.info(f"Permission denied for resource {res}. Run: sudo chmod 666 {res}")
            
            continue
    
    if resource is None :
        
        logging.error(f"Power supply {pscfg['manufacturer']} {pscfg['model']} {pscfg['serial_number']} not found in available resources: {' , '.join(l_visa_resources)}")
        exit(1)
    
    logging.info(f"Found power supply on resource {resource}: {ps_mfr}, {ps_model}, {ps_sn}")
    
    visa_vm.write("SYST:REM")
    
    retval = 0
    
    if not args.noreset :
        
        # Ramp down to 0 V safely
        retval = reset(visa_vm = visa_vm)
    
    if args.poff :
        
        visa_vm.write("OUTP OFF")
        time.sleep(TIME_INTERVAL)
    
    else :
        
        visa_vm.write("OUTP ON")
        
        retval = set_voltage(
            visa_vm = visa_vm,
            volt_target = args.voltage,
            curr_max = args.current,
            channel_voltage_limits = channel_voltage_limits,
            channels = args.channels,
        )
    
    print_vi_all(
        visa_vm = visa_vm,
        nchannels = nchannels,
    )
    
    if retval :
        
        logging.error("Failed to set voltage and current on power supply. Powering down ...")
        reset(visa_vm = visa_vm)
        visa_vm.write("OUTP OFF")
    
    else :
        
        logging.info(f"Done setting voltage to {args.voltage} V and maximum current to {args.current} A")
    
    return retval

if __name__ == "__main__" :

    main()