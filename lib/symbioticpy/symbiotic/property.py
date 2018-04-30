#!/usr/bin/python

from . exceptions import SymbioticException
from os.path import abspath, join

class Property:
    def __init__(self, prpfile = None):
        self._prpfile = prpfile
        # property as LTL formulae (if available)
        self._ltl = []

    def memsafety(self):
        """ Check for memory safety violations """
        return False

    def signedoverflow(self):
        """ Check for signed integer overflows """
        return False

    def assertions(self):
        """ Check for assertion violations """
        return False

    def undefinedness(self):
        """ Check for undefined behavior """
        return False

    def ltl(self):
        """ Is the property described by a generic LTL formula(e)? """
        return False

    def getPrpFile(self):
        return self._prpfile

    def getLTL(self):
        return self._ltl


class PropertyMemSafety(Property):
    def __init__(self, prpfile = None):
        Property.__init__(self, prpfile)

    def memsafety(self):
        return True


class PropertyNoOverflow(Property):
    def __init__(self, prpfile = None):
        Property.__init__(self, prpfile)

    def signedoverflow(self):
        return True


class PropertyDefBehavior(Property):
    def __init__(self, prpfile = None):
        Property.__init__(self, prpfile)

    def undefinedness(self):
        return True


class PropertyUnreachCall(Property):
    def __init__(self, prpfile = None):
        Property.__init__(self, prpfile)

    def assertions(self):
        return True

supported_ltl_properties = {
    'CHECK( init(main()), LTL(G ! call(__VERIFIER_error())) )' : 'REACHCALL',
    'CHECK( init(main()), LTL(G valid-free) )'                 : 'MEMSAFETY',
    'CHECK( init(main()), LTL(G valid-deref) )'                : 'MEMSAFETY',
    'CHECK( init(main()), LTL(G valid-memtrack) )'             : 'MEMSAFETY',
    'CHECK( init(main()), LTL(G ! overflow) )'                 : 'SIGNED-OVERFLOW',
    'CHECK( init(main()), LTL(G def-behavior) )'               : 'UNDEF-BEHAVIOR',
}

supported_properties = {
    'valid-deref'                                              : 'MEMSAFETY',
    'valid-free'                                               : 'MEMSAFETY',
    'valid-memtrack'                                           : 'MEMSAFETY',
    'null-deref'                                               : 'NULL-DEREF',
    'undefined-behavior'                                       : 'UNDEF-BEHAVIOR',
    'undef-behavior'                                           : 'UNDEF-BEHAVIOR',
    'signed-overflow'                                          : 'SIGNED-OVERFLOW',
    'memsafety'                                                : 'MEMSAFETY',
}

def _get_prp(prp):
    from os.path import expanduser, isfile
    # if property is given in file, read the file
    epath = abspath(expanduser(prp))
    if isfile(epath):
        prp_list = []
        f = open(epath, 'r')
        for line in f.readlines():
            line = line.strip()
            # ignore empty lines
            if line:
                prp_list.append(line)
        f.close()
        return (prp_list, epath)

    # it is not a file, so it is given as a string
    # FIXME: this does not work for properties given
    # as LTL (there are spaces)
    return (prp.split(), None)


def _map_property(prps):
    mapped_prps = []
    ltl_prps = []
    for prp in prps:
        prp_key = supported_properties.get(prp)
        if not prp_key:
            prp_key = supported_ltl_properties.get(prp)
            if prp_key:
                ltl_prps.append(prp)

        if prp_key:
            mapped_prps.append(prp_key)
        else:
            raise SymbioticException('Unknown or unsupported property: {0}'.format(ke.message))

    return (mapped_prps, ltl_prps)

def get_property(symbiotic_dir, prp):
    if prp is None:
        prop = PropertyUnreachCall()
        prop._prpfile = abspath(join(symbiotic_dir, 'specs/PropertyUnreachCall.prp'))
        return prop

    prps, prpfile = _get_prp(prp)
    prps, ltl_prps = _map_property(prps)
    prop = None

    if 'REACHCALL' in prps:
        prop = PropertyUnreachCall(prpfile)
        if prpfile is None:
            prop._prpfile = abspath(join(symbiotic_dir, 'specs/PropertyUnreachCall.prp'))
    elif 'MEMSAFETY' in prps:
        prop = PropertyMemSafety(prpfile)
        if prpfile is None:
            prop._prpfile = abspath(join(symbiotic_dir, 'specs/PropertyMemSafety.prp'))

    elif 'UNDEF-BEHAVIOR' is prps:
        prop = PropertyDefBehavior(prpfile)
        if prpfile is None:
            prop._prpfile = abspath(join(symbiotic_dir, 'specs/PropertyDefBehavior.prp'))

    elif 'SIGNED-OVERFLOW' in prps:
        prop = PropertyNoOverflow(prpfile)
        if prpfile is None:
            prop._prpfile = abspath(join(symbiotic_dir, 'specs/PropertyNoOverflow.prp'))

    if prop:
        prop._ltl = ltl_prps
    return prop
