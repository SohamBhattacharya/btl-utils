#!/bin/bash

./python/compare_sms.py \
--srcs \
  "CIT:../data/QAQC_SM/module_calibrations/sm/inter-bac/qaqc-at_CIT_v3.1/**:module_(?P<barcode>\\d+)_analysis_both_calibs.*.root" \
  "MIB:../data/QAQC_SM/module_calibrations/sm/inter-bac/qaqc-at_MIB/**:module_(?P<barcode>\\d+)_analysis.*.root" \
  "PKU:../data/QAQC_SM/module_calibrations/sm/inter-bac/qaqc-at_PKU/**:module_(?P<barcode>\\d+)_analysis.*.root" \
  "UVA:../data/QAQC_SM/module_calibrations/sm/inter-bac/qaqc-at_UVA/**:module_(?P<barcode>\\d+)_analysis.*.root" \
--plotcfg \
  configs/config_compare_sms.yaml \
--outdir results/compare_sms
