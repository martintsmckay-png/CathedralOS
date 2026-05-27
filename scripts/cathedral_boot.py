from core.amber_core import AmberCore
from core.bluepinkcore import BluePinkCore
from core.noodle_core import NoodleCore
from core.kitten_core import KittenCore

def boot():
    amber = AmberCore()
    bluepink = BluePinkCore()
    noodle = NoodleCore()
    kitten = KittenCore()

    return {
        "status": "CathedralOS Online",
        "cores": [amber, bluepink, noodle, kitten]
    }
