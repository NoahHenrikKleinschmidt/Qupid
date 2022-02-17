import streamlit as st
import pandas as pd
import qpcr
import Qupid as qu
import controls as ctrl
from controls import session
import qpcr.Filters as Filters
import qpcr.Plotters as Plotters

st.set_page_config(
                        page_title="Qupid",
                        page_icon="📈",
                        layout="wide",
                        initial_sidebar_state = "collapsed",
                    )

st.title("Qupid")
st.markdown("#### Quantitative PCR Interface to Delta-Delta-Ct")

# setup layout

# =================================================================
# upload input files for normalisers and assays
# =================================================================

# setup the input upload type to the session
session("upload_type", None)

files_container = st.expander("Input Data File(s)", expanded = True) #.container()

control_col, uploader_col = files_container.columns((1,4))
files_expander = uploader_col#.expander("Input Data File(s)", expanded = True)

# ------------------------------------------------------------------------------------------
# setup control buttons to select which type of inputs to upload
# ------------------------------------------------------------------------------------------

control_col.markdown("#### Type of Input Data")

control_col.markdown("---")

multiple_files_button = control_col.button(
                                                "Upload multiple Files",
                                                help = "Upload multiple single-assay datafiles. Note, these must be regular `csv` files!",
                                        )
multi_assay_button = control_col.button(
                                                "Upload one multi-assay File",
                                                help = "Upload a single decorated multi-assay datafile. Note, this may be a multi-sheet datafile.",
                                        )

big_table_button = control_col.button(
                                                "Upload one Big Table File",
                                                help = "Upload a single decorated Big Table datafile.",
                                        )


control_col.markdown("---")

read_button = control_col.button(
                                                "Read my File(s)",
                                                help = "Hit this button **after** you have finished your upload setup.",
                                        )

# control_col.markdown(   "Please, note that is is not possible to mix data from different upload types! You can perform an analysis on data uploaded by only a single input type at a time. ")
control_col.markdown(   "If you wish to switch between input types, you may have to click the corresponding button twice or reload the app."   )
control_col.markdown(   "Check out [the Getting Started tutorial](https://github.com/NoahHenrikKleinschmidt/qpcr/blob/main/Examples/0_getting_started.ipynb) to the API  to learn more about valid input datafiles."   )

# ------------------------------------------------------------------------------------------
# Setting up input widgets for different datafile types
# ------------------------------------------------------------------------------------------

if multiple_files_button or session("upload_type") ==  "multiple files":
    
    # set the input type
    session("upload_type", "multiple files")
    
    # reset the files 
    session("assay_files", reset = True)
    session("normaliser_files", reset = True)

    # set up input controls
    ctrl.upload_multiple_files(files_expander, build = True)

if multi_assay_button or session("upload_type") ==  "multi assay":
    
    # set the input type
    session("upload_type", "multi assay")    
    
    # reset the files 
    session("assay_files", reset = True)

    # set up input controls
    ctrl.upload_single_file(files_expander, build = True)
    ctrl.setup_multi_assay_file(files_expander, build = True)

if big_table_button or session("upload_type") ==  "big table":
    
    # set the input type
    session("upload_type", "big table")   

    # reset the files 
    session("assay_files", reset = True)

    # set up input controls
    ctrl.upload_single_file(files_expander, build = True)
    ctrl.setup_bigtable_file(files_expander, build = True)

# ------------------------------------------------------------------------------------------
#  Reading the data
# ------------------------------------------------------------------------------------------

if read_button:     
    
    # check if we got data
    ctrl.vet_input_data()

    # get the input type
    input_type = session("upload_type")
    
    # set up a new QupidReader
    Qreader = qu.QupidReader()

    # reading multiple regular csv input files
    if input_type == "multiple files":
        

        # read regular csv file lists 
        assays = Qreader.read_regular_csv_files( "assay_files" )
        normalisers = Qreader.read_regular_csv_files( "normaliser_files" )


    # reading a single multi assay file
    elif input_type == "multi assay":

        # get the datafile
        file = session("assay_files")

        # setup a MultiSheetReader
        reader = qpcr.Readers.MultiReader()
        
        # setup the Qreader with the file
        Qreader.setup(file)
        

        # setup general variables used by both multisheet and singlesheet
        
        # get the column to search in for assays
        col = session("col")

        if Qreader.is_excel():

            # set up an ExcelParser
            reader._Parser = qpcr.Parsers.ExcelParser()
            qu.setup_parser_from_session(reader)

            # pass on replicate information
            qu.replicates_from_session(reader)

            # prelim read
            Qreader.read_excel()

            multi_sheet = session("multi_sheet")
            if multi_sheet:

                # get all sheet names
                sheets = Qreader.sheets()

                # now read each sheet in the data
                assays, normalisers = [], []
                for sheet in sheets:

                    # parse and extract data
                    a, n = Qreader.parse_one_excel_sheet(file, reader, col, sheet)
                    
                    # store found assays + normalisers
                    assays.extend(a)
                    normalisers.extend(n)

            # single-sheet read
            else:

                # get the sheet_name to read
                sheet_name = qu.sheet_name_from_session(Qreader)

                # parse only the one provided sheet
                assays, normalisers = Qreader.parse_one_excel_sheet(file, reader, col, sheet_name)

        else: # file is a csv file

            # setup a CsvParser
            reader._Parser = qpcr.Parsers.CsvParser()
            qu.setup_parser_from_session(reader)

            # pass on replicate information
            qu.replicates_from_session(reader)

            # prepare the csv file to be read 
            # and parse the file
            data = Qreader.read_irregular_csv()
            assays, normalisers = Qreader.parse_csv_file(data, reader, col)

    # reading a big table file
    elif input_type == "big table":

        # setting up a reader
        reader = qpcr.Readers.BigTableReader()

        # get the datafile
        file = session("assay_files")

        # setup the Qreader with the file
        Qreader.setup(file)

        # get kind of big table
        kind = session("kind")
        reader._kind = kind
        is_horizontal = kind == "horizontal"

        # check for excel file
        if Qreader.is_excel():

            # set up an ExcelParser
            reader._Parser = qpcr.Parsers.ExcelParser()
            qu.setup_parser_from_session(reader)

            # pass on replicate information
            qu.replicates_from_session(reader)

            # prelim read
            Qreader.read_excel()

            # get sheet_name to read
            sheet_name = qu.sheet_name_from_session(Qreader)

            # parse the table and make Assays
            assays, normalisers = Qreader.parse_excel_BigTable(file, reader, sheet_name, is_horizontal)


        else: # read a CSV big table file

            # setup a CsvParser
            reader._Parser = qpcr.Parsers.CsvParser()
            qu.setup_parser_from_session(reader)

            # pass on replicate information
            qu.replicates_from_session(reader)

            assays, normalisers = Qreader.prase_csv_BigTable(reader, is_horizontal)
            
            
    # store in session
    session("assays", assays)
    session("normalisers", normalisers)

if session("assays") is not None and session("normalisers") is not None:
    ctrl.found_assays_message()

    # st.write(  session("assay_files"), session("normaliser_files")  )







# files_expander = uploader_col.expander("Input Data Files", expanded = True)
# assay_files_col, norm_files_col = files_expander.columns(2)

# assay_files = assay_files_col.file_uploader(
#                                             "Upload Input Assays", 
#                                             type = ["csv", "xlsx"],
#                                             accept_multiple_files = True,
#                                             help = "Upload csv files here for all assays that shall be treated as samples-of-interest.\nPlease, upload a separate file for each assay."
#                                         )

# norm_files = norm_files_col.file_uploader(
#                                             "Upload Normaliser Assays", 
#                                             type = ["csv", "xlsx"],
#                                             accept_multiple_files = True,
#                                             help = "Upload csv files here for all assays that shall be treated as normalisers.\nPlease, upload a separate file for each assay."
#                                         )

# # check if data is supplied
# got_data = assay_files is not None or norm_files is not None


# if got_data: 
#     first_reader = qu.QupidReader()
#     assay_files = [  first_reader.read(i) for i in assay_files  ]

# # =================================================================
# # Control settings for experiment
# # =================================================================

# controls_panel = st.container()
# controls, chart = controls_panel.columns((10,20))

# # setting up controls
# replicates = controls.number_input(
#                                     "Number of Replicates per group",
#                                     min_value = 1,
#                                     value = 3,
#                                     step = 1,
#                                     help = "The number of replicates in each group of replicates. Note, this assumes there are always the same number of replicates. If this is not the case for your datasets then use the replicate settings from the `Advanced Settings`."
#                                 )

# group_names = controls.text_input(
#                                     "Names of Replicate groups",
#                                     placeholder = "control, conditionA, conditionB, ... (optional)",
#                                     help = "The names for your groups of replicates (optional). Please, specify names comma-separated. Note that the names must match the order in which the replicates appear in the dataset."
#                                 )
# # pre-process group_names into list or set to None
# group_names = None if group_names == "" else [i.strip() for i in group_names.split(",")]


# # ----------------------------------------------------------------
# # Generic settings like Filter type and Plotter...
# # ----------------------------------------------------------------


# filter_type = controls.radio(
#                                 "Select Filter", 
#                                 ["Range", "IQR", "None"], 
#                                 help = "Select which filter to apply before Delta-Delta-Ct computation. By default a Range Filter of +/- 1 around the group median is applied. Alternatively, an IQR filter of 1.5 x IQR around the median can be selected. If None is selected, no filtering will be done."
#                             )
# # pre-process filter_type
# filter_type = None if filter_type == "None" else filter_type

# chart_mode = controls.radio(
#                                 "Select Plotting Mode", 
#                                 ["interactive", "static"], 
#                                 help = "Select which type of plot to display. Either an interactive plot, or a static figure."

#                             )


# # ----------------------------------------------------------------
# # Advances settings like Anchor...
# # ----------------------------------------------------------------

# more_controls_expander = controls.expander("Advanced Settings")

# # anchor settings
# anchor = more_controls_expander.selectbox(
#                                             "Select anchor", 
#                                             ["first", "grouped", "specified"],
#                                             help = "The anchor is the intra-dataset reference for the first Delta-Ct. Using 'first' will choose the very first data entry, 'grouped' will use the first entry of each replicate group. Using 'specified' you may pass an externally computed numeric value."
                                            
#                                         )

# # preprocess anchor input (and allow specific entry)
# if anchor == "specified":
#     new_anchor = more_controls_expander.number_input("Specify an anchor value")
#     anchor = new_anchor

# # advanced replicate settings
# advanced_replicates = more_controls_expander.selectbox(
#                                                         "Advanced replicates", 
#                                                         ["simple", "tuple", "formula"],
#                                                         help = "Set the number of replicates of your replicate groups. If all groups have the same number of replicates (e.g. all are triplicates) you may use the default settings `simple` which can be specified using the number input above. If replicate groups are unequal in size, you can either specify a `tuple` of sizes for each group individually (for instance `3,3,3,3,1` for four triplicates and one unicate), or use a text `formula` to specify a recipe for such a tuple (in the example before `'3:4,1'` would specify the recipe for `3,3,3,3,1`). Generally, a `formula` works by `n:m` where `n` is the number of replicates in a group and `m` is the number of times to repeat this pattern. Check out the [qpcr documentation](https://noahhenrikkleinschmidt.github.io/qpcr/index.html#qpcr.Assay.replicates) for more information."
#                                                     )
# # by default we use the simple number input above,
# # if something different is selected, then we add another input widget
# if advanced_replicates != "simple":
#     placeholder = "3,3,3,1" if advanced_replicates == "tuple" else "3:3,1"
#     replicates = more_controls_expander.text_input(
#                                                     "Number of Replicates per group",
#                                                     placeholder = placeholder,
#                                                     help = "The number of replicates per group. Specify here either a `tuple` of individual values or a `formula`. See the help string of the `Advanced replicates` selectbox above for more details."
#                                                 )

#     # if a tuple is provided, we'll pre-process the string to get the numeric tuple values
#     # if a formula is used we can keep the string formula and don't have to pre-process that any further...
#     if advanced_replicates == "tuple" and replicates != "":
#         replicates = tuple([int(i.strip()) for i in replicates.split(",")])


# # filtering inclusion range
# if filter_type is not None:
#     preset_range = (-1.0, 1.0) if filter_type == "Range" else (-1.5, 1.5)
#     inclusion_range = more_controls_expander.slider(
#                                                     "Filter Inclusion Range",
#                                                     min_value = -5.0, 
#                                                     max_value = 5.0, 
#                                                     value = preset_range,
#                                                     step = 0.1,
#                                                     help = "Set the upper and lower boundries for the filter inclusion range. In case of RangeFilter this will be absolute numbers around the group median. In case of IQRFilter this will be factors n x IQR around the group median."
#                                                 )

# # plotting kwargs setup
# plotting_kwargs = more_controls_expander.text_area(
#                                                     "Plotting parameters",
#                                                     placeholder = """color = 'green'\ntitle = 'my figure'\nfigsize = (8, 3)""",
#                                                     help = "You can specify various plotting arguments to fine-tune the preview figures generated. Note, that this requires some knowledge of either matplotlib's or plotly's accepted arguments for figures and subplots, because the different plotting methods accept different kinds of plotting kwargs. Refer to the documentation of the `qpcr` module for more details."   
#                                                 )
# plotting_kwargs = f"dict({plotting_kwargs})".replace("\n", "")
# plotting_kwargs = eval(plotting_kwargs)

# # =================================================================
# # Run our analysis
# # =================================================================

# run_button = controls.button(
#                                 "Run Analysis",
#                             )

# def add_figure(fig, container, mode):
#     """
#     Adds a figure to a container...
#     """
#     if mode == "interactive":
#         container.plotly_chart(fig, use_container_width = True)
#     elif mode == "static":
#         container.pyplot(fig, use_container_width = True)
        

# if run_button and got_data:
    
#     # setup pipeline
#     pipeline = _Qupid_Blueprint()
#     pipeline.replicates(replicates)
#     pipeline.names(group_names)

#     # setup custom Analyser and Normaliser...
#     # actually, the Normaliser is a default one, 
#     # but it would not work unless specifically added as well... 
#     # (very curious)
#     analyser = qpcr.Analyser()
#     analyser.anchor(anchor)
#     pipeline.Analyser(analyser)
#     pipeline.Normaliser(qpcr.Normaliser())


#     # setup filter
#     if filter_type is not None:
#         if filter_type == "Range":
#             _filter = Filters.RangeFilter()
#         elif filter_type == "IQR":
#             _filter = Filters.IQRFilter()
        
#         lower, upper = inclusion_range
#         lower = abs(lower) # because filter range is designed for positive values 
#         _filter.set_lim(upper = upper, lower = lower)
#         _filter.plotmode(chart_mode)
#         pipeline.add_filters(_filter)
    
#     # setup plotter
#     _plotter = Plotters.PreviewResults(chart_mode)
#     _plotter.params(**plotting_kwargs)
#     _plotter.params(show = False)
#     pipeline.add_plotters(_plotter)

#     # link the data
#     pipeline.add_assays(assay_files)
#     pipeline.add_normalisers(norm_files)

#     # run pipeline
#     with st.spinner("Running analysis..."):
#         pipeline.run()

#     figures = pipeline.Figures()

#     # ----------------------------------------------------------------
#     # Get the Results to be nicely displayed...
#     # ----------------------------------------------------------------
    
#     # make new expanders for the figures

#     if filter_type is not None: 
#         filter_fig_expander = chart.expander("Filter Overview")
#         pre_filter, post_filter = figures[:2]
#         add_figure(pre_filter, filter_fig_expander, chart_mode)
#         add_figure(post_filter, filter_fig_expander, chart_mode)

#     preview_expander = chart.expander("Preview Results", expanded = True)
#     preview = figures[-1]
#     add_figure(preview, preview_expander, chart_mode)

#     # generate download buttons

#     rep_results = pipeline.get(kind = "df")
#     stats_results = pipeline.get()

#     chart.download_button(
#                             "Download Raw Results",
#                             rep_results.to_csv(index = False),
#                             mime = "text/csv",
#                             help = "Download the analysed results retaining all replicates."
#                         )
    
#     chart.download_button(
#                             "Download Summarized Results",
#                             stats_results.to_csv(index = False),
#                             mime = "text/csv",
#                             help = "Download the analysed results summarized to mean and stdev of each replicate group."
#                         )

# # =================================================================
# # Footer Section
# # =================================================================

# footer = st.container()
# footer.markdown("---")
# foot_left, foot_middle, foot_right = footer.columns(3)
# foot_left.markdown("""
# Qupid is built around the [`qpcr` python module](https://github.com/NoahHenrikKleinschmidt/qpcr) which provides a set of powerful and easy-to-use tools to perform Delta-Delta-Ct analysis on small and large-scale datasets.
# If you wish to automate your qPCR data analysis even more or Qupid isn't quite suited to your needs, you may want to check out what the main `qpcr` module can do for you.
# """)

# foot_middle.markdown("""
# Love using Qupid :cupid:?\n 
# Then, consider citing it in your work :hibiscus:. Find the citation [here](https://github.com/NoahHenrikKleinschmidt/qpcr-Analyser/blob/main/CITATION.cff). \n
# Good luck with your research :four_leaf_clover:

# """)

# foot_right.markdown("""
# Have you discovered a bug? \n
# Oh, shoot, sorry about that... Please, post an [issue on github](https://github.com/NoahHenrikKleinschmidt/qpcr-Analyser/issues) about it. \n
# Thanks :blossom:

# """)