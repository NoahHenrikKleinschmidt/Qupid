import streamlit as st
import pandas as pd
import qpcr
import Qupid as qu

import controls as ctrl
from controls import session
import qpcr.Filters as Filters
import qpcr.Plotters as Plotters
import core 
from copy import deepcopy

st.set_page_config(
                        page_title="Qupid",
                        page_icon="📈",
                        layout="wide",
                        initial_sidebar_state = "collapsed",
                    )

color = "rgb(255, 82, 88)"

st.markdown("""# Qupid""")
st.markdown(f"""###  <font style="color:{color}">Qu</font>antitative <font style="color:{color}">P</font>CR <font style="color:{color}">I</font>nterface to <font style="color:{color}">D</font>elta-Delta-Ct""", unsafe_allow_html=True)
st.markdown("---")

# =================================================================
# upload input files for normalisers and assays
# =================================================================

# st.markdown("#### Input Data")

# setup the input upload type to the session
session("upload_type", None)

files_container = st.container()# ("Input Data File(s)", expanded = True) #.container()

control_col, uploader_col = files_container.columns((1,4))
files_expander = uploader_col#.expander("Input Data File(s)", expanded = True)

# ------------------------------------------------------------------------------------------
# setup control buttons to select which type of inputs to upload
# ------------------------------------------------------------------------------------------

control_col.markdown("#### Type of Input Data")

control_col.markdown("---")

multiple_files_button = control_col.button(
                                                "Upload multiple Files",
                                                help = "Upload multiple single-assay datafiles. Note, these must be \"regular\" `csv` or `excel` files!",
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
control_col.markdown(   "Check out [the Getting Started tutorial](https://github.com/NoahHenrikKleinschmidt/qpcr/blob/main/Examples/0_getting_started.ipynb) to the API  to learn more about valid input datafiles. Also check out the [Decorator Tutorial](https://github.com/NoahHenrikKleinschmidt/qpcr/blob/main/Examples/8_decorating_datafiles.ipynb) to learn how to add decorators to your multi-assay datafiles."    )
control_col.markdown(   "----- \n Need an introduction? Then check out the [Tutorial Notebook](https://github.com/NoahHenrikKleinschmidt/Qupid/blob/main/Tutorial.ipynb) that provides an overview of the interface.")

# ------------------------------------------------------------------------------------------
# Setting up input widgets for different datafile types
# ------------------------------------------------------------------------------------------

if multiple_files_button or session("upload_type") ==  "multiple files":
    
    # set the input type
    session("upload_type", "multiple files")
    
    # reset the files 
    session("assay_files", reset = True)
    session("normaliser_files", reset = True)
    # session("assays", reset = True)
    # session("normalisers", reset = True)

    # set up input controls
    ctrl.upload_multiple_files(files_expander, build = True)

if multi_assay_button or session("upload_type") ==  "multi assay":
    
    # set the input type
    session("upload_type", "multi assay")    
    
    # reset the files 
    session("assay_files", reset = True)
    # session("assays", reset = True)
    # session("normalisers", reset = True)

    # set up input controls
    ctrl.upload_single_file(files_expander, build = True)
    ctrl.setup_multi_assay_file(files_expander, build = True)

if big_table_button or session("upload_type") ==  "big table":
    
    # set the input type
    session("upload_type", "big table")   

    # reset the files 
    session("assay_files", reset = True)
    # session("assays", reset = True)
    # session("normalisers", reset = True)

    # set up input controls
    ctrl.upload_single_file(files_expander, build = True)
    ctrl.setup_bigtable_file(files_expander, build = True)

# ------------------------------------------------------------------------------------------
#  Reading the data
# ------------------------------------------------------------------------------------------

if read_button:     
    
    # check if we got data
    ctrl.vet_input_data()

    # read the data and store to session
    core.read()

    # st.write(session("assays")[0].get())

# =================================================================
# Control settings for experiment
# =================================================================

if session("assays") is not None and session("normalisers") is not None:
    ctrl.vet_all_assays_grouped()
    ctrl.found_assays_message()

    # also store the names of the assays and normalisers to the session state for log
    session("assay_names" , [  i.id() for i in session("assays")  ]  )
    session("normaliser_names" , [  i.id() for i in session("normalisers")  ]  )
    # also store the group names 
    session("group_names" , session("assays")[0].names()  )

    # setup layout

    controls_panel = st.container()
    controls_panel.markdown(    "---"    )
    controls_panel.markdown(    "### Analysis Setup"    )
    controls_panel.markdown(    "##### Basic Setup"    )
    controls_left, controls_right, advanced = controls_panel.columns((1,1,4))


# ----------------------------------------------------------------
# Generic settings like Filter type and Plotter...
# ----------------------------------------------------------------

    # setup calibration option
    ctrl.setup_calibration_option( controls_left )

    # setup filter type selection
    ctrl.setup_filter_type(controls_left)

    # setup chart mode (interactive vs static)
    ctrl.setup_chart_mode(controls_right)


# # ----------------------------------------------------------------
# # Advances settings like Anchor...
# # ----------------------------------------------------------------

    advanced.markdown(    "##### Settings "    )

    # setup calibration settings
    if session("perform_calibration"):
        advanced.markdown(    "###### Calibration Settings"    )
        ctrl.setup_calibration_Settings( advanced )

    # anchor settings
    advanced.markdown(    "###### Anchor Settings"    )
    ctrl.setup_anchor_settings(advanced)

    # tile Settings
    advanced.markdown(    "###### Normalisation Settings"    )
    ctrl.setup_normaliser_mode(advanced)

    # filtering inclusion range
    if session("filter_type") is not None:
        advanced.markdown(    "###### Filter Settings"    )
        ctrl.setup_filter_inclusion_range(advanced)

    # plotting kwargs setup
    advanced.markdown(    "###### Plotter Settings"    )
    ctrl.setup_plotting_kwargs(advanced)
    ctrl.setup_drop_groups_selection(advanced)
    # ctrl.setup_drop_rel(advanced)

# =================================================================
# Run our analysis
# =================================================================

    controls_left.markdown("##### Run Analysis")

    show_replicates = controls_left.checkbox(
                                            "Show Replicate Box Plot",
                                            value = False,
                                            help = "Generate a Box Plot overview of all replicate groups from all assays in one figure. Note, this works with pre-filtered assays! For a view on filtering, check out the Filter Figure that is generated during Delta-Delta-Ct computation."
                                    )

    if session( "perform_calibration" ):
        show_calibration = controls_left.checkbox(
                                        "Show Calibration Line Plot",
                                        value = True,
                                        help = "If any new qPCR efficiencies were computed during calibration, visualise the regression lines in a figure."
                                    )
    else: 
        show_calibration = False

    run_plotting = controls_left.checkbox(
                                    "Generate Figure",
                                    value = True,
                                    help = "Visualise the results. Note, this only affects the `Preview` figure (not the Filter figure!). When this box is checked, you can edit the figure settings and do not need to push the `Run analysis` button again, the figures will automatically update!"
                                )

    controls_left.markdown("---")
    run_button = controls_left.button(
                                    "Run Analysis",
                                    help = "Compute Delta-Delta-Ct"
                                ) 


    # setup a session variable to check
    # if an analysis was run and therefore if 
    # it should be allowed to export a session log
    if run_button:
        # compute delta-delta-ct and store a session 
        # variable stating that results should now be present.
        core.run_ddCt()
        session("analysis_was_run", True)
        
        
    analysis_was_run = True if session("analysis_was_run") is not None else False

# =================================================================
# Present Results
# =================================================================

    results_container = st.container()

    if analysis_was_run:

        results_container.markdown( "---" )
        results_container.markdown( "### Results")

        # check if we should compute a replicate boxplot
        if show_replicates:
            core.show_ReplicateBoxPlot(results_container)
        
        # if we got results try to make a 
        # filter summary, (it will check if filters were used at all..)
        core.show_filter_fig(results_container)

        #  make a calibration overview figure for newly computed efficiencies
        if show_calibration:
            core.show_calibration_fig( results_container )

        # make a preview figure
        if run_plotting:
            core.make_preview(results_container)

        core.stats_results_table(results_container)

        # make some download buttons and stuff...
        cols = ctrl.setup_download_button_column_number()
        download_buttons = results_container.columns(cols)

        ctrl.setup_results_downloads(download_buttons[0])
        ctrl.setup_summarised_download(download_buttons[1])
        ctrl.onefile_download_all_assays(download_buttons[2])
        if ctrl.calibrated_new():
            ctrl.calibration_download_button( download_buttons[3] )
        ctrl.setup_session_log_download(download_buttons[-1])

# =================================================================
# Footer Section
# =================================================================

footer = st.container()
footer.markdown("---")
foot_left, foot_middle, foot_right = footer.columns(3)
foot_left.markdown("""
Qupid is built around the [`qpcr` python module](https://github.com/NoahHenrikKleinschmidt/qpcr) which provides a set of powerful and easy-to-use tools to perform Delta-Delta-Ct analysis on small and large-scale datasets.
If you wish to automate your qPCR data analysis even more or Qupid isn't quite suited to your needs, you may want to check out what the main `qpcr` module can do for you.
""")

foot_middle.markdown("""
Love using Qupid :cupid:?\n 
Then, cite it in your work :hibiscus:. Find the citation [here](https://github.com/NoahHenrikKleinschmidt/qpcr-Analyser/blob/main/CITATION.cff). \n
Good luck with your research :four_leaf_clover:

""")

foot_right.markdown("""
Have you discovered a bug? \n
Oh, shoot, sorry about that... Please, post an [issue on github](https://github.com/NoahHenrikKleinschmidt/qpcr-Analyser/issues) about it. \n
Thanks :blossom:

""")