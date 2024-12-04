import dataclasses

@dataclasses.dataclass(frozen = True)
class SIPM:
    KIND_OF_PART = "SiPMArray"

@dataclasses.dataclass(frozen = True)
class LYSO:
    KIND_OF_PART = "LYSOMatrix #1"

@dataclasses.dataclass(frozen = True)
class SM:
    KIND_OF_PART = "SensorModule"

@dataclasses.dataclass(frozen = True)
class DM:
    KIND_OF_PART = "DetectorModule"

@dataclasses.dataclass(frozen = True)
class FE:
    KIND_OF_PART = "FE"

@dataclasses.dataclass(frozen = True)
class LOCATION:
    CIT = 5023
    MIB = 5380
    PKU = 3800
    UVA = 1003

