"""
This module defines functions the help set up the main app's controls depending 
on the different user inputs etc. ...
"""

import streamlit as st
import qpcr
import Qupid as qu


def session(key, value = None, reset = False):
    """
    Adds a variable to the st.session state or gets it
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