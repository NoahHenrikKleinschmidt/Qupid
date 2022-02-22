"""
This module handles the main workflows to read 
files and compute Delta-Delta-Delta-Ct
"""

import streamlit as st
import qpcr
import qpcr._auxiliary as aux
import qpcr._auxiliary.defaults as defaults
import controls as ctrl
from controls import session
import Qupid as qu

from copy import deepcopy 
import datetime

def read():
    """
    The main workflow that will read the upoaded datafile(s) 
    and store lists of qpcr.Assay objects for both assays and normalisers
    into the session.
    """
    # get the input type
    input_type = session("upload_type")

    # set up a new QupidReader
    Qreader = qu.QupidReader()

    # reading multiple regular csv input files
    if input_type == "multiple files":
        # read regular csv file lists 
        assay_files = session( "assay_files" )

        assays = []
        for assay in assay_files:
            # get the datacolumns in case there are more than two
            id_col = aux.from_kwargs( "id_col", defaults.default_id_header, st.session_state, rm = True )
            ct_col = aux.from_kwargs( "ct_col", defaults.default_ct_header, st.session_state, rm = True )
            # read the file
            assay = Qreader.SingleReader_read_regular( 
                                                        assay, 
                                                        id_label = id_col, 
                                                        ct_label = ct_col 
                                                    )
            assays.append(assay)

        # now read the normalisers the same way
        normaliser_files = session( "normaliser_files" )
        normalisers = []
        for assay in normaliser_files:
            # get the datacolumns in case there are more than two
            id_col = aux.from_kwargs( "id_col", defaults.default_id_header, st.session_state, rm = True )
            ct_col = aux.from_kwargs( "ct_col", defaults.default_ct_header, st.session_state, rm = True )
            # read the file
            assay = Qreader.SingleReader_read_regular( 
                                                        assay, 
                                                        id_label = id_col, 
                                                        ct_label = ct_col 
                                                    )
            normalisers.append(assay)
        
        # st.write(assays)
        # st.write(assays[0].id(), assays[0].get())


    # reading a single multi assay file
    elif input_type == "multi assay":
        
        # get the datafile
        file = session("assay_files")

        # setup general variables used by both multisheet and singlesheet
        # get the column to search in for assays
        col = session("col")

        # setup the Qreader to prep-read the 
        # file and check for multi-sheet-ness
        Qreader.link( file )
        if Qreader.is_excel():
            Qreader.read_excel()

        
        # check if we're supposed to read all sheets of a multi-assay file
        # if it is one at all...
        if Qreader.is_multisheet() and session("multi_sheet"):
            
            try: 
                assays, normalisers = Qreader.MultiSheetReader_read( file, col = col )
            except:
                st.error(  "No assays could be identified with the given settings!\nMake sure your file is decorated and you supply the right search parameters."   )
                st.stop()
        else:

            # read a single data_sheet
            try: 
                assays, normalisers = Qreader.MultiReader_read( file, col = col )
            except:
                st.error(  "No assays could be identified with the given settings!\nMake sure your file is decorated and you supply the right search parameters."   )
                st.stop()
        
    # reading a big table file
    elif input_type == "big table":
        
        # get the datafile
        file = session("assay_files")

        assays, normalisers = Qreader.BigTableReader_read( file )

    # store in session
    session("assays", assays)
    session("normalisers", normalisers)



def run_ddCt():
    """
    Sets up and runs DeltaDeltaCt analysis and stores results to the session
    """

    # get the assays
    assays = deepcopy( session("assays") )
    normalisers = deepcopy( session("normalisers") )

    # set up the ddCt pipeline
    pipe = qpcr.Pipes.ddCt()

    # link data
    pipe.add_assays(assays)
    pipe.add_normalisers(normalisers)


    # add filter
    filter_type = session("filter_type")
    if filter_type is not None: 
        if filter_type == "Range":
            Filter = qpcr.Filters.RangeFilter()
        elif filter_type == "IQR":
            Filter = qpcr.Filters.IQRFilter()

        # set up inclusion range
        inclusion_range = session("inclusion_range")
        lower, upper = inclusion_range
        lower = abs(lower) # because filter range is designed for positive values 
        Filter.set_lim(upper = upper, lower = lower)

        # set up plotmode
        chart_mode = session("chart_mode")
        Filter.plotmode(chart_mode)
        Filter.plot_params(show = False)
        # add filter to pipe
        pipe.add_filters(Filter)

    # setup the Analyser
    analyser = qpcr.Analyser()
    analyser.anchor(  session("anchor"), group = session("ref_group")  )
    pipe.Analyser(analyser)

    
    # we will not include the Plotters here, 
    # but have these work later

    # st.write(   [i.get() for i in assays]   )

    # run pipeline
    with st.spinner("Running analysis..."):
        pipe.run()

    # add the Filter to allow 
    # downloading the Filter report
    if filter_type is not None:
        session("Filter", Filter)

    # get and store results
    results = pipe.get(kind = "obj")

    # remove the "assay" column as it is 
    # meaninglsess in the _df setting
    if "assay" in results.get().columns:
        results.drop_cols("assay")

    session("results", results)
    results_df = results.get()
    session("results_df", results_df)
    results_stats = results.stats()
    session("results_stats", results_stats)
    figures = pipe.Figures()
    session("figures", figures)

    # and also store the assay copies that 
    # now contain the computed results
    # We primarily do this to allow repeated analyses without affecting the 
    # already loaded raw data...
    session("assays_computed", assays)


def show_filter_fig(container):
    """
    Generates a new expander for the pre- and post- filtering summary boxplots
    """
    
    filter_type = session("filter_type")
    figures = session("figures")
    chart_mode = session("chart_mode")

    if filter_type is not None: 
        filter_fig_expander = container.expander("Filter Overview")
        filter_fig = figures[0]
        ctrl.add_figure(filter_fig, filter_fig_expander, chart_mode)


def make_preview(container):
    """
    Generates a PreviewResults figure and stores it to a new expander
    """

    # get a deepcopy of the results first, because we want to be able
    # to exlude groups etc. for visualisation but not for the actual data
    results = deepcopy(  session("results")  )

    # ignore groups that were selected for ignoring
    ignore_groups = session("ignore_groups")
    if ignore_groups != []:
        results.drop_groups(ignore_groups)

    drop_rel = session("drop_rel")
    if drop_rel:
        results.drop_rel()


    # setup the plotter
    chart_mode = session("chart_mode")
    preview = qpcr.Plotters.PreviewResults(  mode = chart_mode  )
    # pass plotting kwargs
    plotting_kwargs = session("plotting_kwargs")
    preview.params(
                    show = False,
                    **plotting_kwargs,
                )
    # link the data
    preview.link(results)

    # plot
    preview_fig = preview.plot()
    
    # and add figure to an expander
    preview_expander = container.expander("Preview Results", expanded = True)
    ctrl.add_figure(preview_fig, preview_expander, chart_mode)


def stats_results_table(container):
    """
    Generates a new expander and places the results_stats dataframe in it
    for inspection.
    """
    stats_expander = container.expander(
                                            "View Summary Table",
                                            # help = "Show the summary statistics table of the delta-delta-Ct results that includes mean, stdv, and median of each group of each assay."
                                    )
    stats_expander.table(  session("results_stats")  )


def show_ReplicateBoxPlot(container):
    """
    Generates a replicate boxplot and places it in an expander.
    """
    # get the assays
    assays = deepcopy( session("assays") )
    normalisers = deepcopy( session("normalisers") )
    assays = assays + normalisers

    # setup the plotter 
    mode = session("chart_mode")
    plotter = qpcr.Plotters.ReplicateBoxPlot( mode = mode )

    # link the assays
    for a in assays: plotter.link( a )
    
    # plot and show
    fig = plotter.plot( show = False )
    expander = container.expander( "Overview of Replicates" )
    ctrl.add_figure(fig, expander, mode)
    