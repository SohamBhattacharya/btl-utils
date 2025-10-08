import dataclasses
#import ROOT

@dataclasses.dataclass(frozen = True)
class LOCATION:
    CERN = 1005
    CIT = 5023
    MIB = 5380
    PKU = 3800
    UVA = 1003

@dataclasses.dataclass(frozen = True)
class SIPM:
    KIND_OF_PART = "SiPMArray"
    LABEL = "SiPM"
    BARCODE_RANGES = {}

@dataclasses.dataclass(frozen = True)
class LYSO:
    KIND_OF_PART = "LYSOMatrix #1"
    LABEL = "LYSO"
    BARCODE_RANGES = {}

@dataclasses.dataclass(frozen = True)
class SM:
    KIND_OF_PART = "SensorModule"
    LABEL = "SM"
    BARCODE_RANGES = {
        LOCATION.CIT: [("32110020008401", "32110020011200")],
        LOCATION.MIB: [("32110020000001", "32110020002800")],
        LOCATION.PKU: [("32110020002801", "32110020005600")],
        LOCATION.UVA: [("32110020005601", "32110020008400")],
    }

@dataclasses.dataclass(frozen = True)
class DM:
    KIND_OF_PART = "DetectorModule"
    LABEL = "DM"
    BARCODE_RANGES = {
        LOCATION.CIT: [("32110040004201", "32110040005600")],
        LOCATION.MIB: [("32110040000001", "32110040001400")],
        LOCATION.PKU: [("32110040001401", "32110040002800")],
        LOCATION.UVA: [("32110040002801", "32110040004200")],
    }

@dataclasses.dataclass(frozen = True)
class FE:
    KIND_OF_PART = "FE"
    LABEL = "FEB"
    BARCODE_RANGES = {}

@dataclasses.dataclass(frozen = True)
class CC:
    KIND_OF_PART = "CC"
    LABEL = "CC"
    BARCODE_RANGES = {}

@dataclasses.dataclass(frozen = True)
class PCC1P2:
    KIND_OF_PART = "PCCIv1.2"
    LABEL = "PCCi 1.2 V"
    BARCODE_RANGES = {}

@dataclasses.dataclass(frozen = True)
class PCC2P5:
    KIND_OF_PART = "PCCIv2.5"
    LABEL = "PCCi 2.5 V"
    BARCODE_RANGES = {}

@dataclasses.dataclass(frozen = True)
class RU:
    KIND_OF_PART = "RU"
    LABEL = "RU"
    BARCODE_RANGES = {
        LOCATION.CIT: [(str(32110060000500+_i*1000), str(32110060000695+_i*1000)) for _i in range(0, 10)],
        LOCATION.MIB: [(str(32110060000100+_i*1000), str(32110060000295+_i*1000)) for _i in range(0, 10)],
        LOCATION.PKU: [(str(32110060000700+_i*1000), str(32110060000895+_i*1000)) for _i in range(0, 10)],
        LOCATION.UVA: [(str(32110060000300+_i*1000), str(32110060000495+_i*1000)) for _i in range(0, 10)],
    }

@dataclasses.dataclass(frozen = True)
class COLDTRAY:
    KIND_OF_PART = "Cold Tray"
    LABEL = "Cold Tray"
    BARCODE_RANGES = {}

@dataclasses.dataclass(frozen = True)
class TRAY:
    KIND_OF_PART = "Tray"
    LABEL = "Tray"
    BARCODE_RANGES = {
        #LOCATION.CIT: ("32110070000039", "32110070000956"),
        LOCATION.CIT: [(str(32110070000039+_i*100), str(32110070000056+_i*100)) for _i in range(0, 10)],
        LOCATION.MIB: [(str(32110070000003+_i*100), str(32110070000020+_i*100)) for _i in range(0, 10)],
        LOCATION.PKU: [(str(32110070000057+_i*100), str(32110070000074+_i*100)) for _i in range(0, 10)],
        LOCATION.UVA: [(str(32110070000021+_i*100), str(32110070000038+_i*100)) for _i in range(0, 10)],
    }

@dataclasses.dataclass(frozen = True)
class COLORS:
    
    import ROOT
    
    CIT = ROOT.TColor.GetColor("#f89c20")
    MIB = ROOT.TColor.GetColor("#3f90da")
    PKU = ROOT.TColor.GetColor("#bd1f01")
    UVA = ROOT.TColor.GetColor("#964a8b")
    CERN = 4
    ALL = ROOT.TColor.GetColor("#e42536")
