import dataclasses
import ROOT

@dataclasses.dataclass(frozen = True)
class SIPM:
    KIND_OF_PART = "SiPMArray"
    LABEL = "SiPM"

@dataclasses.dataclass(frozen = True)
class LYSO:
    KIND_OF_PART = "LYSOMatrix #1"
    LABEL = "LYSO"

@dataclasses.dataclass(frozen = True)
class SM:
    KIND_OF_PART = "SensorModule"
    LABEL = "SM"

@dataclasses.dataclass(frozen = True)
class DM:
    KIND_OF_PART = "DetectorModule"
    LABEL = "DM"

@dataclasses.dataclass(frozen = True)
class FE:
    KIND_OF_PART = "FE"
    LABEL = "FEB"

@dataclasses.dataclass(frozen = True)
class LOCATION:
    CIT = 5023
    MIB = 5380
    PKU = 3800
    UVA = 1003

@dataclasses.dataclass(frozen = True)
class COLORS:
    CIT = ROOT.TColor.GetColor("#f89c20")
    MIB = ROOT.TColor.GetColor("#3f90da")
    PKU = ROOT.TColor.GetColor("#bd1f01")
    UVA = ROOT.TColor.GetColor("#964a8b")
    ALL = ROOT.TColor.GetColor("#e42536")
