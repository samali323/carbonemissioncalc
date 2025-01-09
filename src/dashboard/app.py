import dash
from dash import html, dcc, Output, Input
import plotly.graph_objs as go
import json
import tempfile
import os


class DashboardApp:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.setup_layout()

    def setup_layout(self):
        self.app.layout = html.Div([
            html.H1("Transport Emissions Analysis Dashboard"),

            # Emissions Overview Grid
            html.Div([
                html.H2("Emissions Overview"),
                dcc.Graph(id='emissions-overview'),
            ]),

            # Transport Comparison Grid
            html.Div([
                html.H2("Transport Mode Comparison"),
                dcc.Graph(id='transport-comparison'),
            ]),

            # Environmental Impact Grid
            html.Div([
                html.H2("Environmental Impact"),
                dcc.Graph(id='environmental-impact'),
            ]),

            # Update interval
            dcc.Interval(
                id='interval-component',
                interval=2 * 1000,  # in milliseconds
                n_intervals=0
            )
        ])

        self.setup_callbacks()

    def setup_callbacks(self):
        @self.app.callback(
            [Output('emissions-overview', 'figure'),
             Output('transport-comparison', 'figure'),
             Output('environmental-impact', 'figure')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_graphs(n):
            try:
                # Read data from temp file
                with open(os.path.join(tempfile.gettempdir(), 'dashboard_data.json'), 'r') as f:
                    data = json.load(f)

                # Create emissions overview figure
                emissions_fig = go.Figure()
                emissions_fig.add_trace(go.Indicator(
                    mode="number+delta",
                    value=data['total_emissions'],
                    title={'text': "Total Emissions (mT CO2)"}
                ))

                # Create transport comparison figure
                transport_fig = go.Figure(data=[
                    go.Bar(
                        x=['Air', 'Rail', 'Bus'],
                        y=[data['transport_comparison']['air'],
                           data['transport_comparison']['rail'],
                           data['transport_comparison']['bus']],
                        name='Emissions by Transport Mode'
                    )
                ])

                # Create environmental impact figure
                impact_data = data['environmental_impact']
                impact_fig = go.Figure(data=[
                    go.Bar(
                        x=list(impact_data.keys()),
                        y=list(impact_data.values()),
                        name='Environmental Equivalencies'
                    )
                ])

                return emissions_fig, transport_fig, impact_fig

            except Exception as e:
                print(f"Error updating dashboard: {str(e)}")
                return {}, {}, {}

    def run_server(self, debug=True, port=8050):
        self.app.run_server(debug=debug, port=port)


if __name__ == '__main__':
    dashboard = DashboardApp()
    dashboard.run_server()