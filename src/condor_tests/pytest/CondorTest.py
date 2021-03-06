import atexit
import sys
import time

from Globals import *
from Utils import Utils
from PersonalCondor import PersonalCondor

class CondorTest(object):

    #
    # Personal Condor management
    #
    _personal_condors = { }

    # @return A PersonalCondor object.  The corresponding master daemon
    # has been started.
    #
    # (FIXME) In the default case, locate the "current"/"default" personal
    # condor that the test suite should have already started for us.
    # Also, if CONDOR_CONFIG is not set already, complain.
    #
    # (The above may indicate that this class should really be CondorInstance,
    # instead.  We also may want to allow a CondorInstance to be constructed
    # by passing it a (full) filepath to a CONDOR_CONFIG.)
    #
    # Otherwise, construct a new personal condor and register an
    # atexit function to make sure we shut it down (FIXME: aggressively).
    #
    # Make the returned PersonalCondor the 'active' object (that is, set
    # its CONDOR_CONFIG in the enviroment).
    #
    @staticmethod
    def StartPersonalCondor(name, params=None, ordered_params=None):
        pc = CondorTest._personal_condors.get( name )
        if pc is None:
            pc = PersonalCondor( name, params, ordered_params )
            CondorTest._personal_condors[ name ] = pc
        pc.Start()
        return pc

    @staticmethod
    def StopPersonalCondor(name):
        pc = CondorTest._personal_condors.get( name )
        if pc is not None:
            pc.Stop()

    @staticmethod
    def StopAllPersonalCondors():
        for name, pc in CondorTest._personal_condors.keys():
            pc.Stop()


    #
    # Subtest reporting.  The idea here is two-fold: (1) to abstract away
    # reporting (e.g., for Metronome or for CTests or for Jenkins) and
    # (2) to help test authors catch typos and accidentally skipped tests.
    #
    _tests = { }

    # @param subtest An arbitrary string denoting which part of the test
    #                passed or failed, or the name of test if it's indivisible.
    # @param message An arbitrary string explaining why the (sub)test failed.
    @staticmethod
    def RegisterFailure( subtest, message ):
        Utils.TLog( "[" + subtest + "] FAILURE: " + message )
        CondorTest._tests[ subtest ] = ( TEST_FAILURE, message )
        return None

    @staticmethod
    def RegisterSuccess( subtest, message ):
        Utils.TLog( "[" + subtest + "] SUCCESS: " + message )
        CondorTest._tests[ subtest ] = ( TEST_SUCCESS, message )
        return None

    # @param list A list of arbitrary strings corresponding to parts of the
    #             test.  The test will fail if any member of this list has
    #             not been the first argument to RegisterSuccess().
    @staticmethod
    def RegisterTests( list ):
        for test in list:
            CondorTest._tests[ test ] = ( TEST_SKIPPED, "[initial state]" )


    #
    # Exit handling.
    #

    _exit_code = None

    @staticmethod
    def ExitHandler():
        # We're headed out the door, start killing our PCs.
        for name, pc in CondorTest._personal_condors.items():
            pc.BeginStopping()

        # The reporting here is a trifle simplicistic.
        rv = CondorTest._exit_code
        for subtest in CondorTest._tests.keys():
            record = CondorTest._tests[subtest]
            if record[0] != TEST_SUCCESS:
                Utils.TLog( "[" + subtest + "] did not succeed, failing test!" )
                rv = TEST_FAILURE

        # Make sure the PCs are really gone.
        Utils.TLog( "Waiting for personal condor(s) to finish stopping..." )
        time.sleep(5)
        for name, pc in CondorTest._personal_condors.items():
            pc.FinishStopping()

        # If we're the last registered exit handler to raise an exception,
        # this would determine the interpreter's exit code, but instead
        # causes a scary-looking KeyError warning from the threading module.
        #
        # To avoid that, if we've imported the threading module, remove it
        # from the sys.modules dictionary.  This is probably wildly unsafe,
        # but since we're in the exit handler, that probably doesn't matter.
        if sys.modules.get("threading") is not None:
        	del sys.modules["threading"]
        sys.exit(rv)

    # The 'early-out' method.  Records the intended exit code, because
    # Python doesn't.  We could skip using the atexit library, but this
    # is more-obviously correct.
    @staticmethod
    def Exit( code ):
        CondorTest._exit_code = code
        return CondorTest._original_exit( code )


# Register the exit handler and wrap sys.exit on module load.
atexit.register( CondorTest.ExitHandler )
CondorTest._original_exit = sys.exit
sys.exit = CondorTest.Exit
