#!/usr/bin/env python3


import constants
import utils

utils.save_all_part_info(
    parttype = constants.SIPM.KIND_OF_PART,
    outyamlfile = "info/sipm_info.yaml",
    inyamlfile = "info/sipm_info.yaml",
    location_id = constants.LOCATION.CIT,
    ret = False
)