"""
This module handles the main workflows to read 
files and compute Delta-Delta-Delta-Ct
"""

import streamlit as st
import qpcr
import controls as ctrl
from controls import session
import Qupid as qu
from copy import deepcopy 


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



def run_ddCt():
    """
    Sets up and runs DeltaDeltaCt analysis and stores results to the session
    """

    # get the assays
    assays = session("assays")
    normalisers = session("normalisers")

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


def show_filter_fig(container):
    """
    Generates a new expander for the pre- and post- filtering summary boxplots
    """
    
    filter_type = session("filter_type")
    figures = session("figures")
    chart_mode = session("chart_mode")

    if filter_type is not None: 
        filter_fig_expander = container.expander("Filter Overview")
        pre_filter, post_filter = figures[:2]
        ctrl.add_figure(pre_filter, filter_fig_expander, chart_mode)
        ctrl.add_figure(post_filter, filter_fig_expander, chart_mode)


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
    stats_expander.write(  session("results_stats")   )