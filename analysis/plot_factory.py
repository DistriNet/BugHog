from bokeh.core.validation import silence
from bokeh.core.validation.warnings import PALETTE_LENGTH_FACTORS_MISMATCH
from bokeh.embed import file_html
from bokeh.models import BasicTickFormatter, ColumnDataSource, HoverTool
from bokeh.models.glyphs import Circle
from bokeh.palettes import Iridescent23
from bokeh.plotting import figure, output_file, show
from bokeh.resources import CDN
from bokeh.transform import factor_cmap

from bci.database.mongo.mongodb import MongoDB
from bci.evaluations.logic import PlotParameters


silence(PALETTE_LENGTH_FACTORS_MISMATCH, True)

class PlotFactory:

    @staticmethod
    def show_plot(params: PlotParameters, db: MongoDB, path=None):
        plot = PlotFactory.__create_plot(params, db)
        if plot is None:
            return
        if path:
            output_file(path)
        show(plot)

    @staticmethod
    def create_html_plot_string(params: PlotParameters, db: MongoDB) -> tuple[str, int]:
        # Check for missing plot parameters
        missing_parameters = []
        if not params.mech_group:
            missing_parameters.append('selected experiment')
        if not params.target_mech_id:
            missing_parameters.append('reproduction ID')
        if not params.browser_name:
            missing_parameters.append('browser')
        if not params.database_collection:
            missing_parameters.append('database collection')

        if missing_parameters:
            return (
                f'No Gantt chart can be plotted because the following parameters are missing {", ".join(missing_parameters)}',
                0
            )

        plot, nb_of_evaluations = PlotFactory.__create_plot(params, db)
        if plot is None and nb_of_evaluations == 0:
            return '<p>No datapoints found...</p>', 0
        elif plot is None:
            return None, nb_of_evaluations
        html = file_html(plot, CDN)
        return html, nb_of_evaluations

    @staticmethod
    def __create_plot(params: PlotParameters, db: MongoDB):
        docs = db.get_documents_for_plotting(params)
        if len(docs) == 0:
            return None, 0

        data = PlotFactory.__add_outcome_info(params, docs)

        # Create a data source with task start and end times, task names, and task colors
        source = ColumnDataSource(data=data)

        # define a color map based on the 'version' column
        color_map = factor_cmap('browser_version_str', Iridescent23, list(set(source.data['browser_version_str'])))

        # Create a figure and add the task circles
        plot = figure(
            title='Gantt Chart with Points',
            x_range=(min(source.data['revision_number']), max(source.data['revision_number'])),
            y_range=['Error', 'Not reproduced', 'Reproduced'],
            height=350,
            width=700,
            tools='xwheel_zoom,reset,pan',
            active_scroll='xwheel_zoom')
        plot.add_glyph(source, Circle(x='revision_number', y='outcome', fill_color=color_map, fill_alpha=0.8, size=15))

        # Formatting
        plot.xaxis[0].formatter = BasicTickFormatter(use_scientific=False)
        hover = HoverTool(
            tooltips=[
                    ('Revision Number', '@revision_number'),
                    ('Browser Version', '@browser_version'),
                ]
        )
        plot.add_tools(hover)

        return plot, len(docs)

    @staticmethod
    def __transform_to_bokeh_compatible(docs: list) -> dict:
        new_docs = {}
        for d in docs:
            for key, value in d.items():
                if key not in new_docs:
                    new_docs[key] = []
                new_docs[key].append(value)
        return new_docs

    @staticmethod
    def __add_outcome_info(params: PlotParameters, docs: dict):
        docs_with_outcome = []
        target_mech_id = params.target_mech_id if params.target_mech_id else params.mech_group

        for doc in docs:
            requests_to_target = list(filter(lambda x: f'/report/?leak={target_mech_id}' in x['url'], doc['results']['requests']))
            requests_to_baseline = list(filter(lambda x: '/report/?leak=baseline' in x['url'], doc['results']['requests']))
            new_doc = {
                'revision_number': doc['revision_number'],
                'browser_version': int(doc['browser_version'].split('.')[0]),
                'browser_version_str': doc['browser_version'].split('.')[0]
            }
            if doc['dirty'] or len(requests_to_baseline) == 0:
                new_doc['outcome'] = 'Error'
                docs_with_outcome.append(new_doc)
            elif len(requests_to_target) > 0:
                new_doc['outcome'] = 'Reproduced'
                docs_with_outcome.append(new_doc)
            else:
                new_doc['outcome'] = 'Not reproduced'
                docs_with_outcome.append(new_doc)
        docs_with_outcome = PlotFactory.__transform_to_bokeh_compatible(docs_with_outcome)
        return docs_with_outcome
