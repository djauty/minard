import couchdb
from minard import app
from .db import engine

def import_HLDQ_runnumbers(limit=10, offset=0):
    """
    Returns the latest PHYSICS runs.
    """
    conn = engine.connect()
    # select all runs which are physics runs
    result = conn.execute("SELECT run FROM run_state WHERE (run_type & 4) = 4 ORDER BY run DESC LIMIT %s OFFSET %s", (limit,offset))
    return [row[0] for row in result.fetchall()]

def import_HLDQ_ratdb(runs):
    server = couchdb.Server("https://snoplus:"+app.config["COUCHDB_PASSWORD"]+"@"+app.config["COUCHDB_HOSTNAME"])

    db = server["data-quality"]

    results = {}
    for row in db.view('_design/data-quality/_view/runs'):
        run = row.key
        if run in runs:
            runDocId = row['id']
            try:
                results[run] = dict(db.get(runDocId))
            except KeyError:
                app.logger.warning("Code returned KeyError searching for dqtellie proc information in the couchDB. Run Number: %d" % runNumber)

    return [results[run] if run in results else -1 for run in runs]

def generateHLDQProcStatus(ratdbDict):
    """
    Method to generate pass/fail flags for all processors
    Code will return a dict of bools indexed by processor name
    Values will be logical & of all checks.
    """
    procNames = ["dqrunproc","dqtimeproc","dqtriggerproc","dqpmtproc"]
    outDict = {}
    for proc in procNames:
        checkDict = ratdbDict["checks"][proc]
        outDict[proc] = 1
        for entry in checkDict.keys():
            # Skip over processors we no longer check
            if entry == "run_length" or entry == "delta_t_comparison":
                continue
            if type(checkDict[entry]) is not dict:
                # If a run fails set flag to 0 and break
                if checkDict[entry] == 0:
                    outDict[proc] = 0
                    break
    return outDict

#TELLIE Tools
def import_TELLIE_runnumbers(limit=10, offset=0):
    """
    Returns the latest TELLIE runs.
    """
    conn = engine.connect()
    # select all runs which have the external source and tellie bits checked
    result = conn.execute("SELECT run FROM run_state WHERE (run_type & 2064) = 2064 ORDER BY run DESC LIMIT %s OFFSET %s", (limit,offset))
    return [row[0] for row in result.fetchall()]

def import_TELLIEDQ_ratdb(runs):
    if type(runs) == int:
        runs = [runs]
    else:
        pass
    server = couchdb.Server("http://snoplus:"+app.config["COUCHDB_PASSWORD"]+"@"+app.config["COUCHDB_HOSTNAME"])
    db = server["data-quality"]
    data = {}
    checkDict = {}
    runInformationDict = {}
    for row in db.view('_design/data-quality/_view/runs'):
        run = row.key
        if run in runs:
            runDocId = row['id']
            try:
                data[run] = dict(db.get(runDocId)["checks"]["dqtellieproc"])
            except KeyError:
                app.logger.warning("Code returned KeyError searching for dqtellie proc information in the couchDB. Run Number: %d" % runNumber)

    if data == {}:
        return runs, -1, -1

    for run in runs:
        try:
            run_dict = {}
            run_dict["fibre"] = data[run]["fibre"]
            run_dict["pulse_delay"] = data[run]["pulse_delay"]
            run_dict["avg_nhit"] = data[run]["avg_nhit"]
            run_dict["peak_amplitude"] = data[run]["peak_amplitude"]
            run_dict["max_nhit"] = data[run]["max_nhit"]
            run_dict["trigger"] = data[run]["trigger"]
            run_dict["run_length"] = data[run]["run_length"]
            run_dict["peak_number"] = data[run]["peak_number"]
            run_dict["prompt_time"] = data[run]["prompt_time"]
            run_dict["peak_time"] = data[run]["peak_time"]

            checkDict[run] = run_dict

            #Get the runinformation from the tellie dq output
            runInformation = {}
            runInformation["expected_tellie_events"] = data[run]["check_params"]["expected_tellie_events"]
            runInformation["actual_tellie_events"] = data[run]["check_params"]["actual_tellie_events"]
            runInformation["average_nhit"] = data[run]["check_params"]["average_nhit"]
            runInformation["greaterThanMaxNHitEvents"] = data[run]["check_params"]["more_max_nhit_events"]
            runInformation["fibre_firing"] = data[run]["check_params"]["fibre_firing"]
            runInformation["fibre_firing_guess"] = data[run]["check_params"]["fibre_firing_guess"]
            runInformation["peak_number"] = data[run]["check_params"]["peak_numbers"]
            runInformation["prompt_peak_adc_count"] = data[run]["check_params"]["prompt_peak_adc_count"]
            runInformation["pre_peak_adc_count"] = data[run]["check_params"]["pre_peak_adc_count"]
            runInformation["late_peak_adc_count"] = data[run]["check_params"]["late_peak_adc_count"]
            runInformation["subrun_run_times"] = data[run]["check_params"]["subrun_run_times"]
            runInformation["pulse_delay_correct_proportion"]  = data[run]["check_params"]["pulse_delay_efficiency"]

            #Run Information for the subruns
            runInformation["subrun_numbers"] = data[run]["check_params"]["subrun_numbers"]
            runInformation["avg_nhit_check_subruns"] = data[run]["check_params"]["avg_nhit_check"]
            runInformation["max_nhit_check_subruns"] = data[run]["check_params"]["max_nhit_check"]
            runInformation["peak_number_check_subruns"] = data[run]["check_params"]["peak_number_check"]
            runInformation["prompt_peak_amplitude_check_subruns"] = data[run]["check_params"]["prompt_peak_amplitude_check"]
            runInformation["prompt_peak_adc_count_check_subruns"] = data[run]["check_params"]["prompt_peak_adc_count_check"]
            runInformation["adc_peak_time_spacing_check_subruns"] = data[run]["check_params"]["adc_peak_time_spacing_check"]
            runInformation["pulse_delay_efficiency_check_subruns"] = data[run]["check_params"]["pulse_delay_efficiency_check"]
            runInformation["subrun_run_length_check"] = data[run]["check_params"]["subrun_run_length_check"]
            runInformation["correct_fibre_check_subruns"] = data[run]["check_params"]["correct_fibre_check"]
            runInformation["trigger_check_subruns"] = data[run]["check_params"]["trigger_check"]

            runInformationDict[run] = runInformation
        except KeyError:
            checkDict[run] = -1
            runInformationDict[run] = -1

    return runs, checkDict, runInformation

#SMELLIE Tools
def import_SMELLIE_runnumbers(limit=10,offset=0):
    #Returns the latest SMELLIE runs.
    conn = engine.connect()
    # select all runs which have the external source and tellie bits checked
    result = conn.execute("SELECT run FROM run_state WHERE (run_type & 4112) = 4112 ORDER BY run DESC LIMIT %s OFFSET %s", (limit,offset))
    return [row[0] for row in result.fetchall()]

def import_SMELLIEDQ_ratdb(runNumber):
    server = couchdb.Server("http://snoplus:"+app.config["COUCHDB_PASSWORD"]+"@"+app.config["COUCHDB_HOSTNAME"])
    dqDB = server["data-quality"]
    data = None
    for row in dqDB.view('_design/data-quality/_view/runs'):
        if(int(row.key) == runNumber):
            runDocId = row['id']
            try:
                data = dqDB.get(runDocId)["checks"]["DQSmellieProc"]
            except KeyError:
                app.logger.warning("Code returned KeyError searching for dqsmellie proc information in the couchDB. Run Number: %d" % runNumber)
                return runNumber, -1, -1 
    if data==None:
        return runNumber, -1, -1 
    
    checkDict = {}
    checkDict["fibre"] = data["smellieCorrectFibre"]
    checkDict["frequency"] = data["smellieFrequencyCheck"]
    checkDict["intensity"] = data["smellieIntensityCheck"]
    checkDict["number_of_events"] = data["smellieNumberOfEventsCheck"]

    #Get the runinformation from the tellie dq output
    runInformation = {}
    runInformation["smellie_number_of_events_check_subrun"] = data["check_params"]["smellieNumberOfEventsCheckSubrun"]
    runInformation["expected_smellie_events"] = data["check_params"]["number_events_expected_subrun"]
    runInformation["actual_smellie_events"] = data["check_params"]["events_passing_nhit_and_trigger"]
    
    runInformation["smellie_fibre_bool_subrun"] = data["check_params"]["smellieFibreCheckSubrun"]
    runInformation["smellie_calculated_fibre"] = data["check_params"]["fibre_calculated_subrun"]
    runInformation["smellie_actual_fibre"] = data["check_params"]["fibre_expected_subrun"]
    
    runInformation["frequency_actual_subrun"] = data["check_params"]["frequency_actual_subrun"]
    runInformation["frequency_expected_subrun"] = data["check_params"]["frequency_expected_subrun"]
    runInformation["smellie_frequency_check_subrun"] = data["check_params"]["smellieFrequencyCheckSubrun"]
   
    runInformation["smellie_laser_type"] = data["check_params"]["laser_type"]
    runInformation["smellie_laser_intensity"] = data["check_params"]["laser_intensities"]
    runInformation["smellie_laser_wavelength"] = data["check_params"]["laser_wavelengths"]
    runInformation["smellie_intensity_check_subrun"] = data["check_params"]["smellieIntensityCheckSubrun"]
    runInformation["mean_nhit_smellie_events"] = data["check_params"]["mean_nhit_smellie_trigger_subrun"]
    
    runInformation["nhit_event_no_adjacent_trigger"] = data["check_params"]["nhit_event_no_adjacent_trigger"]
    runInformation["trigger_event_no_adjacent_nhit"] = data["check_params"]["trigger_event_no_adjacent_nhit"]
    runInformation["nhit_event_next_to_trigger_event"] = data["check_params"]["nhit_event_next_to_trigger_event"]
    runInformation["events_failing_nhit_passing_trigger"] = data["check_params"]["events_failing_nhit_passing_trigger"]
    return runNumber, checkDict, runInformation
