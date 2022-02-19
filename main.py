import streamlit as st
import pandas as pd
import qpcr
import qpcr._AddOns.Qupid as qu
# import Qupid2 as qu

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

st.markdown("#### Input Data")

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
    controls, chart_col = controls_panel.columns((1,2))

    controls.markdown(    "#### Analysis Setup"    )

# ----------------------------------------------------------------
# Generic settings like Filter type and Plotter...
# ----------------------------------------------------------------

    # setup filter type selection
    ctrl.setup_filter_type(controls)

    # setup chart mode (interactive vs static)
    ctrl.setup_chart_mode(controls)


# # ----------------------------------------------------------------
# # Advances settings like Anchor...
# # ----------------------------------------------------------------

    # setup expander for advanced settings
    more_controls_expander = controls.expander("Advanced Settings")

    # anchor settings
    more_controls_expander.markdown(    "###### Anchor Settings"    )
    ctrl.setup_anchor_settings(more_controls_expander)

    # filtering inclusion range
    if session("filter_type") is not None:
        more_controls_expander.markdown(    "###### Filter Settings"    )
        ctrl.setup_filter_inclusion_range(more_controls_expander)

    # plotting kwargs setup
    more_controls_expander.markdown(    "###### Plotter Settings"    )
    ctrl.setup_plotting_kwargs(more_controls_expander)
    ctrl.setup_drop_groups_selection(more_controls_expander)
    ctrl.setup_drop_rel(more_controls_expander)

# =================================================================
# Run our analysis
# =================================================================

    controls.markdown("---")

    run_analysis = controls.button(
                                    "Compute Delta-Delta-Ct",
                                    help = "Computes Delta-Delta-Ct for all uploaded assays against an averaged version of all normalisers."
                                )

    run_plotting = controls.button(
                                    "Generate Figure",
                                    help = "Visualises the results. Note, this only affects the `Preview` figure (not the Filter figure!) is intended in case you wish to adapt the plotting parameters only and wish to save time by not re-running the entire analysis."
                                )

    run_all = controls.button(
                                    "Run Both",
                                    help = "Computes Delta-Delta-Ct and generates a Preview Figure"
                                ) 


    # setup a session variable to check
    # if an analysis was run and therefore if 
    # it should be allowed to export a session log
    if run_all:
        run_analysis = True
        run_plotting = True

    # compute delta-delta-ct and store a session 
    # variable stating that results should now be present.
    if run_analysis:
        core.run_ddCt()
        session("analysis_was_run", True)
    
    analysis_was_run = True if session("analysis_was_run") is not None else False

    # if we got results try to make a 
    # filter summary, (it will check if filters were used at all..)
    if analysis_was_run:
        core.show_filter_fig(chart_col)

    # make a preview figure
    if run_plotting:
        core.make_preview(chart_col)


    # make some download buttons and stuff..
    if analysis_was_run: 
        core.stats_results_table(chart_col)
        ctrl.setup_results_downloads(chart_col)
        ctrl.onefile_download_all_assays(chart_col)
        ctrl.setup_session_log_download(chart_col)

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