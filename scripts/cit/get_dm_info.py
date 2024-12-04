#!/usr/bin/env python3

import python.constants as constants
import python.utils as utils

utils.save_all_part_info(
    parttype = constants.DM.KIND_OF_PART,
    outyamlfile = "info/cit/dm_info.yaml",
    inyamlfile = "info/cit/dm_info.yaml",
    location_id = constants.LOCATION.CIT,
    ret = False
)