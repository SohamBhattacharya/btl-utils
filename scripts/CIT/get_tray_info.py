#!/usr/bin/env python3

import python.constants as constants
import python.utils as utils

utils.save_all_part_info(
    parttype = constants.TRAY.KIND_OF_PART,
    outyamlfile = "info/CIT/tray_info.yaml",
    inyamlfile = "info/CIT/tray_info.yaml",
    location_id = constants.LOCATION.CERN,
    ret = False
)
