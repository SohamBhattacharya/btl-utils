#!/usr/bin/env python3


import constants
import utils

utils.save_all_part_info(
    parttype = constants.DM.KIND_OF_PART,
    outyamlfile = "info/dm_info.yaml",
    inyamlfile = "info/dm_info.yaml",
    location_id = constants.LOCATION.CIT,
    ret = False
)
