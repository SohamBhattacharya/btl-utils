import dataclasses
#import ROOT

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
class CC:
    KIND_OF_PART = "CC"
    LABEL = "CC"

@dataclasses.dataclass(frozen = True)
class PCC1P2:
    KIND_OF_PART = "PCCIv1.2"
    LABEL = "PCCi 1.2 V"

@dataclasses.dataclass(frozen = True)
class PCC2P5:
    KIND_OF_PART = "PCCIv2.5"
    LABEL = "PCCi 2.5 V"

@dataclasses.dataclass(frozen = True)
class RU:
    KIND_OF_PART = "RU"
    LABEL = "RU"

@dataclasses.dataclass(frozen = True)
class TRAY:
    KIND_OF_PART = "Tray"
    LABEL = "Tray"

@dataclasses.dataclass(frozen = True)
class LOCATION:
    CERN = 1005
    CIT = 5023
    MIB = 5380
    PKU = 3800
    UVA = 1003

@dataclasses.dataclass(frozen = True)
class COLORS:
    
    import ROOT
    
    CIT = ROOT.TColor.GetColor("#f89c20")
    MIB = ROOT.TColor.GetColor("#3f90da")
    PKU = ROOT.TColor.GetColor("#bd1f01")
    UVA = ROOT.TColor.GetColor("#964a8b")
    CERN = 4
    ALL = ROOT.TColor.GetColor("#e42536")
