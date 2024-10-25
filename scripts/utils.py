import argparse
import dataclasses
import itertools
import os
import re
import subprocess
import tqdm
import yaml


class Formatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawTextHelpFormatter
): pass


@dataclasses.dataclass(init = True)
class DetectorModule :
    
    barcode: str = None
    id: str = None
    feb: str = None
    sm1: str = None
    sm2: str = None
    
    def dict(self) :
        
        return dataclasses.asdict(self)


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


def parse_string_regex(
    s,
    regexp
) :
    
    rgx = re.compile(regexp)
    result = [m.groupdict() for m in rgx.finditer(s)][0]
    
    return result


def get_part_id(barcode) :
    """
    Get part ID for given barcode
    """
    
    dbquery_output = subprocess.run([
        "./scripts/rhapi.py",
        "-u", "http://localhost:8113",
        f"select s.ID from mtd_cmsr.parts s where s.BARCODE = '{barcode}'"
    ], stdout = subprocess.PIPE)
    
    id = dbquery_output.stdout.decode("utf-8").split()[1].strip()
    
    return id


def get_dm_barcodes(location_id = None) :
    """
    Get list of DM barcodes
    Caltech location: 5023
    """
    
    query = "select s.BARCODE from mtd_cmsr.parts s where s.KIND_OF_PART = 'DetectorModule'"
    
    if (location_id is not None) :
        
        query = f"{query} AND s.LOCATION_ID = {location_id}"
    
    dbquery_output = subprocess.run([
        "./scripts/rhapi.py",
        "-u", "http://localhost:8113",
        query
    ], stdout = subprocess.PIPE)
    
    l_dm_barcode = dbquery_output.stdout.decode("utf-8").split()[1:]
    l_dm_barcode = [_barcode.strip() for _barcode in l_dm_barcode]
    
    return l_dm_barcode


def get_dm_sm_barcodes(barcode) :
    """
    Get list of SM barcodes for a given DM barcode
    """
    
    dbquery_output = subprocess.run([
        "./scripts/rhapi.py",
        "-u", "http://localhost:8113",
        f"select s.BARCODE from mtd_cmsr.parts s where s.KIND_OF_PART = 'SensorModule' AND s.PART_PARENT_ID = (select s.ID from mtd_cmsr.parts s where s.BARCODE = '{barcode}')"
    ], stdout = subprocess.PIPE)
    
    l_sm_barcode = dbquery_output.stdout.decode("utf-8").split()[1:]
    l_sm_barcode = [_barcode.strip() for _barcode in l_sm_barcode]
    
    return l_sm_barcode


def get_dm_feb_barcode(barcode) :
    """
    Get FEB barcode for a given DM barcode
    """
    
    dbquery_output = subprocess.run([
        "./scripts/rhapi.py",
        "-u", "http://localhost:8113",
        f"select s.BARCODE from mtd_cmsr.parts s where s.KIND_OF_PART = 'FE' AND s.PART_PARENT_ID = (select s.ID from mtd_cmsr.parts s where s.BARCODE = '{barcode}')"
    ], stdout = subprocess.PIPE)
    
    feb_barcode = dbquery_output.stdout.decode("utf-8").split()[1].strip()
    
    return feb_barcode


def get_used_sm_barcodes(location_id = None, yamlfile = None, d_dms = None) :
    """
    Get list of all used (assembled into DMs) SM barcodes
    If yamlfile is provided, will load existing information from there
    If fetch additional DM info from the database if they are not in the file
    """
    
    # Show all columns:
    # ./rhapi.py -u http://localhost:8113 "select s.* from mtd_cmsr.parts s where s.KIND_OF_PART = 'DetectorModule'"
    
    d_dms = get_all_dm_info(
        yamlfile = yamlfile,
        location_id = location_id,
    )
    
    l_sm_barcodes = list(itertools.chain(*[[_dm.sm1, _dm.sm2] for _dm in d_dms.values()]))
    
    return l_sm_barcodes


def get_dm_info(barcode) :
    """
    Get DM information
    """
    
    id = get_part_id(barcode)
    feb = get_dm_feb_barcode(barcode)
    l_sms = sorted(get_dm_sm_barcodes(barcode))
    
    dm = DetectorModule(
        id = id,
        barcode = barcode,
        feb = feb,
        sm1 = l_sms[0],
        sm2 = l_sms[1],
    )
    
    return dm


def get_all_dm_info(location_id = None, yamlfile = None) :
    """
    Get the information for all DMs
    If yamlfile is provided, will load the information from there
    Will fetch the information of addtional DMs from the database if they are not in the file
    """
    
    l_dm_barcode = get_dm_barcodes(location_id = location_id)
    
    d_dms = load_dm_info(yamlfile) if yamlfile else {}
    
    print("Fetching DM information from the database ... ")
    
    for barcode in tqdm.tqdm(l_dm_barcode) :
        
        if barcode in d_dms :
            
            continue
            
        d_dms[barcode] = get_dm_info(barcode)#.dict()
    
    print(f"Fetched information for {len(d_dms)} from the database.")
    
    return d_dms


def load_dm_info(yamlfile) :
    """
    Load DM info from yamlfile
    """
    
    d_dms = {}
    
    if (os.path.exists(yamlfile)) :
        
        print(f"Loading DM information from file: ({yamlfile}) ...")
        
        with open(yamlfile, "r") as fopen :
            
            d_dms = yaml.load(fopen.read(), Loader = yaml.FullLoader)
        
        # Convert dict to DetectorModule object
        d_dms = {_key: DetectorModule(**_val) for _key, _val in d_dms.items()}
        
        print(f"Loaded information for {len(d_dms)} DMs.")
    
    else :
        
        print(f"DM information file ({yamlfile}) does not exist. No DM information loaded.")
    
    return d_dms


def save_all_dm_info(outyamlfile, inyamlfile = None, location_id = None, ret = False) :
    """
    Load existing DM info from inyamlfile
    Fetch additional DM info from database
    Save all DM info into outyamlfile
    """
    
    d_dms_orig = get_all_dm_info(yamlfile = inyamlfile, location_id = location_id)
    
    # Convert DetectorModule object to dict
    d_dms = {_key: _val.dict() for _key, _val in d_dms_orig.items()}
    
    outdir = os.path.dirname(outyamlfile)
    
    if len(outdir) :
        
        os.system(f"mkdir -p {outdir}")
    
    print(f"Saving DM information to file: {outyamlfile} ...")
    
    with open(outyamlfile, "w") as fopen :
        
        fopen.write(yaml.dump(d_dms))
    
    print(f"Saved information for {len(d_dms)} DMs.")
    
    if ret :
        
        return d_dms_orig