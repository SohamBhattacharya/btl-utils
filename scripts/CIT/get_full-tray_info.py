#!/usr/bin/env python3

import os
import python.constants as constants
import python.utils as utils

location = "CIT"

#location_id = [constants.LOCATION.CERN, constants.LOCATION.MIB]
#location_id = constants.LOCATION.CERN
#location_id = constants.LOCATION.MIB
location_id = getattr(constants.LOCATION, location)

d_sipms = utils.save_all_part_info(
    parttype = constants.SIPM.KIND_OF_PART,
    outyamlfile = f"info/{location}/sipm_info.yaml",
    inyamlfile = f"info/{location}/sipm_info.yaml",
    location_id = location_id,
    ret = True,
    use_location_barcode_range = False,
)

d_sms = utils.save_all_part_info(
    parttype = constants.SM.KIND_OF_PART,
    outyamlfile = f"info/{location}/sm_info.yaml",
    inyamlfile = f"info/{location}/sm_info.yaml",
    location_id = location_id,
    ret = True,
)

d_dms =  utils.save_all_part_info(
    parttype = constants.DM.KIND_OF_PART,
    outyamlfile = f"info/{location}/dm_info.yaml",
    inyamlfile = f"info/{location}/dm_info.yaml",
    location_id = location_id,
    ret = True,
)

d_rus = utils.save_all_part_info(
    parttype = constants.RU.KIND_OF_PART,
    outyamlfile = f"info/{location}/ru_info.yaml",
    inyamlfile = f"info/{location}/ru_info.yaml",
    location_id = location_id,
    ret = True,
)

d_trays = utils.save_all_part_info(
    parttype = constants.TRAY.KIND_OF_PART,
    outyamlfile = f"info/{location}/tray_info.yaml",
    inyamlfile = f"info/{location}/tray_info.yaml",
    location_id = location_id,
    ret = True,
)

utils.combine_parts(
    d_sipms = d_sipms,
    d_sms = d_sms,
    d_dms = d_dms,
    d_rus = d_rus,
    d_trays = d_trays,
)

d_parts = {_key: _val.dict() for _key, _val in d_trays.items() if _val}

outyamlfile = f"info/{location}/full-tray_info.yaml"
outdir = os.path.dirname(outyamlfile)

if len(outdir) :
    
    os.system(f"mkdir -p {outdir}")

print(f"Saving information to file: {outyamlfile} ...")

with open(outyamlfile, "w") as fopen :
    
    utils.yaml.dump(d_parts, fopen)

print(f"Saved information.")