#!/usr/bin/env python3

import python.constants as constants
import python.utils as utils

import constants
import utils

utils.save_all_part_info(
    parttype = constants.SIPM.KIND_OF_PART,
    outyamlfile = "info/PKU/sipm_info.yaml",
    inyamlfile = "info/PKU/sipm_info.yaml",
    location_id = constants.LOCATION.PKU,
    ret = False
)