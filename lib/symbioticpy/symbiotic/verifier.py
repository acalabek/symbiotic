#!/usr/bin/python

import sys

from . utils import dbg
from . utils.process import runcmd
from . utils.watch import ProcessWatch, DbgWatch
from . utils.utils import print_stderr
from . exceptions import SymbioticException, SymbioticExceptionalResult

def initialize_verifier(opts):
    if opts.tool_name == 'klee':
        if opts.full_instrumentation:
            from . tools.klee_symbiotic import SymbioticTool
        else:
            from . tools.klee import SymbioticTool
        return SymbioticTool(opts)
    elif opts.tool_name == 'ceagle':
        from . tools.ceagle import SymbioticTool
        return SymbioticTool()
    elif opts.tool_name == 'ikos':
        from . tools.ikos import SymbioticTool
        return SymbioticTool(opts)
    elif opts.tool_name == 'cbmc':
        from . tools.cbmc import SymbioticTool
        return SymbioticTool(opts)
    elif opts.tool_name == 'map2check':
        from . tools.map2check import SymbioticTool
        return SymbioticTool(opts)
    elif opts.tool_name == 'cpachecker':
        opts.explicit_symbolic = True
        from . tools.cpachecker import SymbioticTool
        return SymbioticTool(opts)
    elif opts.tool_name == 'skink':
        from . tools.skink import SymbioticTool
        return SymbioticTool(opts)
    elif opts.tool_name == 'smack':
        from . tools.smack import SymbioticTool
        return SymbioticTool(opts)
    elif opts.tool_name == 'seahorn':
        from . tools.seahorn import SymbioticTool
        return SymbioticTool(opts)
    elif opts.tool_name == 'nidhugg':
        from . tools.nidhugg import SymbioticTool
        return SymbioticTool(opts)
    elif opts.tool_name == 'divine':
        from . tools.divine import SymbioticTool
        return SymbioticTool(opts)
    elif opts.tool_name == 'uautomizer':
        from . tools.ultimateautomizer import SymbioticTool
        return SymbioticTool(opts)
    elif opts.tool_name == 'cc':
        from . tools.cc import SymbioticTool
        return SymbioticTool(opts)
    else:
        raise SymbioticException('Unknown verifier: {0}'.format(opts.tool_name))

class ToolWatch(ProcessWatch):
    def __init__(self, tool):
        # store the whole output of a tool
        ProcessWatch.__init__(self, None)
        self._tool = tool

    def parse(self, line):
        if b'ERROR' in line or b'WARN' in line or b'Assertion' in line\
           or b'error' in line or b'warn' in line:
            sys.stderr.write(line.decode('utf-8'))
        else:
            dbg(line.decode('utf-8'), 'all', print_nl=False,
                prefix='', color=None)

class SymbioticVerifier(object):
    """
    Instance of symbiotic tool. Instruments, prepares, compiles and runs
    symbolic execution on given source(s)
    """

    def __init__(self, bitcode, sources, tool, opts, env=None, params=None):
        # original sources (needed for witness generation)
        self.sources = sources
        # source compiled to llvm bitecode
        self.curfile = bitcode
        # environment
        self.env = env
        self.options = opts

        self.override_params = params

        # definitions of our functions that we linked
        self._linked_functions = []

        # tool to use
        self._tool = tool

    def command(self, cmd):
        return runcmd(cmd, DbgWatch('all'),
                      "Failed running command: {0}".format(" ".join(cmd)))

    def _run_verifier(self, cmd):
        returncode = 0
        watch = ToolWatch(self._tool)
        try:
            runcmd(cmd, watch, 'Running the verifier failed')
        except SymbioticException as e:
            print_stderr(str(e), color='RED')
            returncode = 1

        res = self._tool.determine_result(returncode, 0,
                                          watch.getLines(), False)
        return res

    def run_verification(self):
        params = self.override_params or self.options.tool_params
        cmd = self._tool.cmdline(self._tool.executable(),
                                 params, [self.curfile],
                                 self.options.property.getPrpFile(), [])

        return self._run_verifier(cmd)

    def run(self):
        try:
            return self.run_verification()
        except KeyboardInterrupt as e:
            raise SymbioticException('interrupted')
        except SymbioticExceptionalResult as res:
            # we got result from some exceptional case
            return str(res)

