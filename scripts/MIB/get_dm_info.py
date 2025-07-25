#!/usr/bin/env python3

import python.constants as constants
import python.utils as utils

utils.save_all_part_info(
    parttype = constants.DM.KIND_OF_PART,
    outyamlfile = "info/MIB/dm_info.yaml",
    inyamlfile = "info/MIB/dm_info.yaml",
    location_id = [constants.LOCATION.CERN, constants.LOCATION.MIB, constants.LOCATION.UVA, constants.LOCATION.CIT, constants.LOCATION.PKU],
    barcode_min = 32110040000100,
    barcode_max = 32110040001400,
    ret = False
)
