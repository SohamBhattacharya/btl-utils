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

