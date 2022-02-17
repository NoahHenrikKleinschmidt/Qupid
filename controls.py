"""
This module defines functions the help set up the main app's controls depending 
on the different user inputs etc. ...
"""

import streamlit as st
import qpcr
import Qupid as qu
from copy import deepcopy 
from datetime import datetime

def add_figure(fig, container, mode):
    """
    Adds a figure to a container
    """
    if mode == "interactive":
        container.plotly_chart(fig, use_container_width = True)
    elif mode == "static":
        container.pyplot(fig, use_container_width = True)
       

def session(key, value = None, reset = False):
    """
    Adds a variable to the st.session_state or gets it.
    It returns None by default if the variable is not in session_state.
    """
    if value is not None :
        st.session_state[key] = value
    elif key in st.session_state     and value is None and not reset: 
        return st.session_state[key]
    elif key in st.session_state     and reset:
        st.session_state[key] = None
    elif key not in st.session_state:
        return None

# set up a QupidReader to help with deciding which input widgets to display
reader = qu.QupidReader()
session("ControlsReader", reader)

def vet_input_data():
    """
    Checks if complete input data is provided. For "multi-assay"
    and "big table" that means assay_files is not None, for "multiple" 
    that means both assay_files and normaliser_files must not be None.
    """
    upload_type = session("upload_type")
    
    got_assays = session("assay_files") is not None   
    
    if upload_type == "multiple files":
        
        # it's all good if both assays and normalisers are defined
        got_normalisers = session("normaliser_files") is not None
        all_good = got_assays   and   got_normalisers
    
    else: 

        # since we only have one file anyway, 
        # it's fine if this is not None
        all_good = got_assays

    # generate some error messages if it's not all good
    if not all_good:
        st.error(  "Qupid did not find input data so far! Make sure to upload something before hitting the 'Read' Button."  )
        if session("upload_type") == "multiple files":
            st.warning("Since you are running on multiple input files, make sure to have uploaded to both the Assay and Normaliser input fields!")
        st.stop()

    return all_good


# @st.cache
def upload_multiple_files(container, build = False):
    """
    Sets up two uploaders for assays and normalisers separately...
    """
    if build:
        assay_files = container.file_uploader(
                                                    "Upload Input Assays", 
                                                    type = ["csv"],
                                                    accept_multiple_files = True,
                                                    help = "Upload csv files here for all assays that shall be treated as samples-of-interest.\nPlease, upload a separate file for each assay."
                                                )

        norm_files = container.file_uploader(
                                                    "Upload Normaliser Assays", 
                                                    type = ["csv"],
                                                    accept_multiple_files = True,
                                                    help = "Upload csv files here for all assays that shall be treated as normalisers.\nPlease, upload a separate file for each assay."
                                                )
        # and save to session
        if assay_files != []:
            session("assay_files", assay_files)
        if norm_files != []:
            session("normaliser_files", norm_files)

        # set up a delimiter to read the csv files
        setup_csv_delimiter(container) 

        # set up replicate Settings
        setup_replicates_and_names(container)

def setup_replicates_and_names(container, allow_infer = True):
    """
    Set up inputs for replciates and names
    """

    infer = allow_infer
    replicates = None
    names = None

    container.markdown(   "##### Replicates and Group Names"    )

    # we have allow_infer for the big table input 
    # later where infer is not possible...
    if allow_infer:
        # set up checkbox to use inferred replicates or not...
        infer = container.checkbox(
                                        "Infer replicates",
                                        help = "Select if your replicates are identically labelled and you wish to use automatically inferred replicates.",
                                        value = True                        
                                )
    if not infer:
        replicates = container.text_input(
                                            "Specify replicates",
                                            help = "Either specify an `integer`, `tuple`, or `formula` for your replicates. Learn more about [valid replicate inputs here](https://noahhenrikkleinschmidt.github.io/qpcr/index.html#qpcr.Assay.replicates).",
                                            placeholder = "3    or     4,4,4,4,4,1    or    4:5,1 "
                                        )
        names = container.text_input(
                                            "Specify group names",
                                            help = "Specify the names of your groups of replicates, or leave blank to use default names (group0, group1, ...).",
                                            placeholder = "untreated, ..."
                                        )
    
        # if a single integer was passed convert it
        # else we can keep the string, as the full tuple is 
        # also a formula in string type...
        try: 
            replicates = int(replicates)
        except: 
            pass
        
        # set replicates to None if none are specified
        replicates = None if replicates == "" else replicates
        # set names to None if empty else get the list of names
        names = None if names == "" else [i.strip() for i in names.split(",")]

    # store to session
    session("replicates", replicates, reset = True)
    session("names", names, reset = True)

def setup_csv_delimiter(container):
    """
    Sets up settings for the csv file delimiter
    """
    # set up which delimiter to use
    options = [",", ";"]
    delimiter = container.radio(
                                    "Select a delimiter",
                                    help = "Select which delimiter your file uses. Classic csv files use a comma `,` but some use a semicolon `;`. If you're not sure about your file(s), open them in some regular text editor to check.",
                                    options = options
                            )  
    # save to session
    session("delimiter", delimiter)

# @st.cache
def upload_single_file(container, build = False):
    """
    Sets up two uploaders for a single datafile
    """
    if build:
        try: 
            container.markdown(   "Make sure that if you upload a multi-assay datafile that you have properly [decorated](https://noahhenrikkleinschmidt.github.io/qpcr/Parsers/Parsers.html#decorators) your assays!"   )
            
            assay_files = container.file_uploader(
                                                        "Upload Input File", 
                                                        type = ["csv", "xlsx"],
                                                        accept_multiple_files = False,
                                                        help = "Upload one decorated `csv` or `xlsx` file here for all assays and normalisers."
                                                    )
            # and save to session
            session("assay_files", assay_files)

        except: 
            pass
        
def setup_multi_assay_file(container, build = False):
    """
    Sets up controls for reading a multi assay file
    """
    if build:

        # set checkbox for transposed file
        setup_transpose_controls(container)
    
        # set up replicate Settings
        setup_replicates_and_names(container)

        # get input for the assay pattern
        container.markdown(   "##### Assays"    )
        patterns = list(  qpcr.Parsers.assay_patterns.keys()  )
        patterns.append("other")
        assay_pattern = container.selectbox(
                                                    "Select an assay pattern",
                                                    help = "Select a pattern (or define one yourself) by which the names of the assays names should be extracted.",
                                                    options = patterns
                                            )
        if assay_pattern == "other":
            assay_pattern = container.text_input(
                                                        "Specify assay pattern",
                                                        placeholder = "Assay: ([a-zA-Z0-9 ,\-]+)",
                                                        help = "Specify a valid `regex` attern with _one_ single capturing group that captures the assay name."
                                                    )
        # and store assay_pattern in session
        session("assay_pattern", assay_pattern)
        
        # setup the column in which 
        # to search for assays
        setup_ref_col_input(container)

        # set up data column header controls
        setup_Id_Ct_datacols(container)

        # if we got a file we check if it's an excel file and if so
        # we ask if the file is a multi-sheet or single-sheet file...

        # check if we got a file yet
        if session("assay_files") is not None: 
            
                # set up a reader to check if 
                # we got a multisheet excel file
                reader.setup(  session("assay_files")  )


                # check if it's a csv file and if so set up the delimiter
                if reader.is_csv():
                    container.markdown(   "Qupid has identified your datafile is a `csv` file."   )
                    setup_csv_delimiter(container)


                # check if it's an excel file and 
                # then check for multi-sheet...
                if reader.is_excel():
                    
                    # read the file and check 
                    # for multisheet
                    reader.read_excel()
                    
                    if reader.is_multisheet():
                    
                    
                        container.markdown(   "##### Data Sheets"    )

                        container.markdown(  "Qupid has identified multiple sheets within your datafile!"  )

                        # checkbox for multi-sheet files
                        is_multisheet = container.checkbox(
                                                                    "Read all sheets from my file",
                                                                    "Select this if your file contains multiple sheets from which you wish to read data"                                    
                                                            )        
                        # save to session
                        session("multi_sheet", is_multisheet)

                        # if not multi-sheet then check if there are multiple sheets 
                        if not is_multisheet:

                            sheet_name = container.selectbox(
                                                                    "Select a sheet to read",
                                                                    help = "Your datafile contains multiple sheets, select which one to read, or select the multiple sheets checkbox above to read all of them.",
                                                                    options = reader.sheets(),

                                                                )
                            # save to session
                            session("sheet_name", sheet_name)

def setup_ref_col_input(container):
    """
    Sets up a number input for the column to use while searching for 
    assays of irregular files based on decorators...
    """
    # set which column to search in 
    col = container.number_input(
                                    "Assay column",
                                    help = "Select which column your assay headers are stored in. Note, this will be interpreted as row for transposed files. Note, the first column/row always has index `0`.",
                                    min_value = 0,                       
                            )
    session("col", col)



def setup_Id_Ct_datacols(container):
    """
    Sets up controls for the id and Ct column  headers
    """

    container.markdown(   "##### Data Columns  "   )
    id_col = container.text_input(
                                    "Id column",
                                    help = "Enter the name of the column in which replicate identifiers are stored",
                                    value = "Name",
                                )
    ct_col = container.text_input(
                                    "Ct column",
                                    help = "Enter the name of the column in which Ct values are stored",
                                    value = "Ct",
                                )

    session("id_col", id_col)
    session("ct_col", ct_col)

def setup_Assay_datacols(container):
    """
    Sets up controls for the assay column headers (used by the big tables)
    """
    # container.markdown(   "##### Data Columns  "   )
    assay_col = container.text_input(
                                    "Assay column",
                                    help = "Enter the name of the column in which assay identifiers are stored",
                                    value = "Assay",
                                )
    session("assay_col", assay_col)



def setup_transpose_controls(container):
    """
    Sets up a checkbox to select if an irregular file is transposed or not
    """
    transposed = container.checkbox(
                                        "Read transposed",
                                        help = "Select this if your assays are not above one another but next to one another."
                                )
    session("transpose", transposed)

def setup_bigtable_file(container, build = False):
    """
    Sets up controls for reading a big table file
    """
    
    if build:

        # specify which kind of big table is present
        options = ["vertical", "horizontal"]
        kind = container.selectbox(
                                        "Kind of Big Table",
                                        help = "Select which kind of Big Table you have. You can [learn more about big tables here](https://noahhenrikkleinschmidt.github.io/qpcr/Readers/Readers.html#qpcr.Readers.Readers.BigTableReader).",
                                        options = options,                        
                                )
        # save to session
        session("kind", kind)

        # set up replicate Settings
        allow_infer = False if kind == "horizontal" else True
        setup_replicates_and_names(container, allow_infer = allow_infer)

        # setup data column controls
        if kind == "vertical":
            setup_Id_Ct_datacols(container)
            setup_Assay_datacols(container)
        else:
            container.markdown(   "##### Data Columns  "   )
            setup_Assay_datacols(container)

        # if we got a file we check if it's an excel file and if so
        # we ask if the file is a multi-sheet or single-sheet file...

        # check if we got a file yet
        if session("assay_files") is not None: 
            
                # set up a reader to check if 
                # we got a multisheet excel file
                reader.setup(  session("assay_files")  )

                # check if it's a csv file and if so set up the delimiter
                if reader.is_csv():
                    container.markdown(   "Qupid has identified your datafile is a `csv` file."   )
                    setup_csv_delimiter(container)


                # first check if it's an excel file
                if reader.is_excel():
                    
                    # read the file and check 
                    # for multisheet
                    reader.read_excel()
                    session(  "sheet_name", reader.sheets()[0]  )
                    if reader.is_multisheet():
                        
                        container.markdown(   "##### Data Sheets"    )
                        container.markdown(  "Qupid has identified multiple sheets within your datafile!"  )

                        # setup controls to select which sheet to read
                        container.markdown(  "When using a Big Table file, only a single sheet can be read! Please, select which sheet to read."  )
                        sheet_name = container.selectbox(
                                                            "Select a sheet to read",
                                                            help = "Your datafile contains multiple sheets, select which one to read, or select the multiple sheets checkbox above to read all of them.",
                                                            options = reader.sheets(),

                                                    )
                        # save to session
                        session("sheet_name", sheet_name)




def setup_filter_type(container):
    """
    Sets up a radio button to select which filter to use
    """
    options = ["Range", "IQR", "None"]
    filter_type = container.radio(
                                    "Select Filter", 
                                    options = options, 
                                    help = "Select which filter to apply before Delta-Delta-Ct computation. By default a Range Filter of +/- 1 around the group median is applied. Alternatively, an IQR filter of 1.5 x IQR around the median can be selected. If None is selected, no filtering will be done."
                                )
    # pre-process filter_type
    filter_type = None if filter_type == "None" else filter_type
    session("filter_type", filter_type, reset = True)

def setup_chart_mode(container):
    """
    Sets up a radio button to select interactive or static figure mode
    """
    options = ["interactive", "static"]
    chart_mode = container.radio(
                                "Select Plotting Mode", 
                                options = options, 
                                help = "Select which type of plot to display. Either an interactive plot, or a static figure."

                            )
    session("chart_mode", chart_mode)



def setup_anchor_settings(container):
    """
    Sets up a selectbox (and optional number input for "specified" anchor )
    """
    # anchor settings
    options = ["first", "mean", "grouped", "specified"]
    anchor = container.selectbox(
                                    "Select anchor", 
                                    options = options,
                                    help = "The anchor is the intra-dataset reference for the first Delta-Ct. Using 'first' will choose the very first data entry, 'grouped' will use the first entry of each replicate group. Using 'specified' you may pass an externally computed numeric value."  
                            )

    # preprocess anchor input (and allow specific entry)
    if anchor == "specified":
        new_anchor = container.number_input("Specify an anchor value")
        anchor = new_anchor

    # set up ref_group in case of "mean" anchor 
    session("ref_group", reset = True)
    if anchor == "mean":
        # get the first assay to get the group names
        groups = session("assays")[0].names()
        ref_group = container.selectbox(
                                            "Select a reference group",
                                            help = "Select which of your replicate groups is your reference.",
                                            options = groups,
                                    )
        session("ref_group", ref_group)

    # save to session
    session("anchor", anchor)



def setup_filter_inclusion_range(container):
    """
    Sets up a slider for the inclusion range of the filter
    """
    filter_type = session("filter_type")
    # filtering inclusion range
    if filter_type is not None:
        preset_range = (-1.0, 1.0) if filter_type == "Range" else (-1.5, 1.5)
        inclusion_range = container.slider(
                                                        "Filter Inclusion Range",
                                                        min_value = -5.0, 
                                                        max_value = 5.0, 
                                                        value = preset_range,
                                                        step = 0.1,
                                                        help = "Set the upper and lower boundries for the filter inclusion range. In case of RangeFilter this will be absolute numbers around the group median. In case of IQRFilter this will be factors n x IQR around the group median."
                                                    )
        session("inclusion_range", inclusion_range)


def setup_plotting_kwargs(container):
    """
    Sets up a text area for plotting kwargs
    """
    # plotting kwargs setup
    plotting_kwargs = container.text_area(
                                            "Plotting parameters",
                                            placeholder = """color = 'green'\ntitle = 'my figure'\nfigsize = (8, 3)""",
                                            help = "You can specify various plotting arguments (or in short: plotting `kwargs` for 'keyword arguments')to fine-tune the preview figures generated. Note, that this requires some knowledge of either matplotlib's or plotly's accepted arguments for figures and subplots, because the different plotting methods accept different kinds of plotting kwargs. You can [learn more in the documentation](https://noahhenrikkleinschmidt.github.io/qpcr/Plotters/Plotters.html) of the `qpcr` module."   
                                        )
    # pre-process kwargs into a dict
    # crop any user-placed commas
    plotting_kwargs = [ 
                            i[:-1] if i.endswith(",") 
                            else i 
                            for i in plotting_kwargs.split("\n") 
                    ]
    # remove any empty lines the user may have entered
    plotting_kwargs = [  i for i in plotting_kwargs if i != ""  ]
    # check if there are any non-standard formatted lines
    if any(  [  "=" not in i for i in plotting_kwargs  ]   ):
        st.error("Something is off with the plotting kwargs, check again to make sure all your lines conform to `var = value` formatting.")
        st.stop()
    # link lines again by commas
    plotting_kwargs = ",".join(plotting_kwargs)

    # convert to a dict
    # maybe use something less hacky than eval() 
    # at some point, but so far it works...
    plotting_kwargs = f"dict({plotting_kwargs})"
    plotting_kwargs = eval(plotting_kwargs)
    # save to session
    session("plotting_kwargs", plotting_kwargs)

def setup_drop_groups_selection(container):
    """
    Sets up a selectbox to choose which groups to ignore while plotting
    It also offers a checkbox to invert the selection to allow instead to
    highlight only the groups that should be plotted...
    """
    groups = session("assays")[0].names()

    to_ignore = container.multiselect(
                                        "Select groups to ignore while plotting",
                                        help = "Select groups of replicates that should not be included in your Preview figure. This is useful when having Diluent or RT- samples that you would not want to have in your final figure.",
                                        options = groups
                                    )

    invert_selection = container.checkbox(
                                                "Invert selection",
                                                help = "Use this to invert your selection. In this case only the selected groups will be plotted."
                                        )
    if invert_selection:
        to_ignore = [ i for i in groups if i not in to_ignore ]
    session("ignore_groups",to_ignore)


def setup_drop_rel(container):
    """
    Sets up a checkbox to drop the _rel_{} part of the headers
    for plotting
    """
    drop_rel = container.checkbox(
                                    "Drop '_rel_'",
                                    help = "This will drop the `_rel_{normaliser}` part of the composite `{assay}_rel_{normaliser}` ids, and thus restore the original assay id when plotting."
                                )
    session("drop_rel", drop_rel)



def setup_session_log_download(container):
    """
    Generates a session log dictionary download button
    """
    session_log = make_session_log()
    # session_log = [(i, j) for i, j in session_log.items()]
    string = "\t{} : {},\n"

    session_log = [ string.format(i, j) for i, j in session_log.items()]
    session_log = "{\n" + "".join(session_log) + "}"
    now = datetime.now()
    filename = f"Qupid_session_log_{now}.json"
    container.download_button(
                                "Download Session Log",
                                session_log,
                                file_name = filename,
                                mime = "text/plain",
                                help = "Downloads a `json` file of metadata on the settings on which Qupid was run. This is important to ensure reproducibility of your analyses, so always download this file!"
                            )




def setup_results_downloads(container):
    """
    Sets up two download buttons, one for the results with replicates, 
    one for the summary statistics table.
    """
    rep_results = session("results_df")
    stats_results = session("results_stats")
    
    container.download_button(
                            "Download Results",
                            rep_results.to_csv(index = False),
                            mime = "text/csv",
                            help = "Download the analysed results retaining all individual replicate values."
                        )

    container.download_button(
                            "Download Summarized Results",
                            stats_results.to_csv(index = False),
                            mime = "text/csv",
                            help = "Download the analysed results summarized to mean and stdev of each replicate group."
                        )





def found_assays_message():
    """
    Generates a success message with the ids of all assays and Normalisers
    that were found
    """
    # check if we got both assays and normalisers
    if len( session("assays") ) == 0 or len( session("normalisers") ) == 0:
        st.error("No assays and/or normalisers could be identified with the given settings. Make sure you have decorated your data and provide the correct `col` argument (column or row in which to search).")
        st.stop()
    else:
        st.success(
            """
            Qupid was able to read the following datsets:
            ###### Assays: 
            {assays}
            ###### Normalisers:
            {normalisers}
            """.format( 
                        assays = [ i.id() for i in session("assays") ],
                        normalisers = [ i.id() for i in session("normalisers") ],
                    )
                )


def make_session_log():
    """
    Will remove technical stuff that is not user-relevant from the st.session_state
    
    Returns
    ---
    log : dict
        The processed session log 
    """
    # get the session_state
    # we manually copy as deepcopy did not work for the session_state
    # and so processing also affected the original dict...
    log = {i : j for i,j in st.session_state.items() }

    # specify the keys to remove
    to_remove = []

    if "ControlsReader" in log.keys():
        to_remove.append( "ControlsReader" )

    # remove results (they are not meta-data)
    if "results" in log.keys():
        to_remove.append( "results" )
    if "results_df" in log.keys():
        to_remove.append( "results_df" )
    if "results_stats" in log.keys():
        to_remove.append(  "results_stats"  )

    if "figures" in log.keys():
        to_remove.append(  "figures"  )

    # if we got a filter remove the Filtering meta data
    if "Filter" in log.keys():
        to_remove.append( "Filter" )
    if session("filter_type") is None and session("Filter") is not None:
        if "inclusion_range" in log.keys():
            to_remove.append(  "inclusion_range"  )

    # remove the keys 
    for i in to_remove: 
        log.pop(i)

    # rename the ignore groups to avoid confusion
    if "ignore_groups" in log.keys():
        log["ignore_groups_while_plotting"] = log["ignore_groups"]
        log.pop("ignore_groups")

    return log

