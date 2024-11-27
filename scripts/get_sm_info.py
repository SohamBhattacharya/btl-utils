#!/usr/bin/env python3


import constants
import utils

utils.save_all_part_info(
    parttype = constants.SM.KIND_OF_PART,
    outyamlfile = "info/sm_info.yaml",
    inyamlfile = "info/sm_info.yaml",
    location_id = constants.LOCATION.CIT,
    ret = False
)