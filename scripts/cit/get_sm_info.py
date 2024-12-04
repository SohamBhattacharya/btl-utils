#!/usr/bin/env python3

import python.constants as constants
import python.utils as utils

import constants
import utils

utils.save_all_part_info(
    parttype = constants.SM.KIND_OF_PART,
    outyamlfile = "info/cit/sm_info.yaml",
    inyamlfile = "info/cit/sm_info.yaml",
    location_id = constants.LOCATION.CIT,
    ret = False
)