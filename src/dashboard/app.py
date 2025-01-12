import dash
from dash import html, dcc, Output, Input
import plotly.graph_objs as go
import json
import tempfile
import os


class DashboardApp:
    def __init__(self):
        self.app = dash.Dash(__name__)

        # Add custom CSS
        self.app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
                <style>
                    body {
                        background-color: #f0f2f5;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    }
                    .dashboard-container {
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    .card {
                        background-color: white;
                        border-radius: 12px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        padding: 20px;
                        margin-bottom: 20px;
                        transition: transform 0.2s;
                    }
                    .card:hover {
                        transform: translateY(-2px);
                    }
                    .flight-card {
                        background: linear-gradient(135deg, #60a5fa, #3b82f6);
                        color: white;
                    }
                    .emissions-card {
                        background: linear-gradient(135deg, #34d399, #059669);
                        color: white;
                    }
                    .section-header {
                        font-size: 1.2em;
                        font-weight: bold;
                        margin-bottom: 15px;
                        color: #1f2937;
                    }
                    .white-text {
                        color: white;
                    }
                    .impact-category {
                        background-color: #f3f4f6;
                        border-radius: 8px;
                        padding: 12px;
                        margin-bottom: 10px;
                    }
                    .impact-header {
                        font-weight: bold;
                        color: #4b5563;
                        margin-bottom: 8px;
                    }
                    .impact-item {
                        color: #6b7280;
                        margin: 4px 0;
                        font-size: 0.95em;
                    }
                    .table {
                        width: 100%;
                        border-collapse: collapse;
                        margin: 10px 0;
                        background-color: white;
                        border-radius: 8px;
                        overflow: hidden;
                    }
                    .table th {
                        background-color: #f3f4f6;
                        padding: 12px;
                        text-align: center;
                        font-weight: bold;
                        color: #4b5563;
                    }
                    .table td {
                        padding: 10px;
                        text-align: center;
                        border-top: 1px solid #e5e7eb;
                        color: #6b7280;
                    }
                    .table tr:hover {
                        background-color: #f9fafb;
                    }
                </style>
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        '''

        self.setup_layout()

    def create_table(self, headers, rows):
        return html.Table(
            [html.Tr([html.Th(col) for col in headers])] +
            [html.Tr([html.Td(cell) for cell in row]) for row in rows],
            className='table'
        )

    def setup_layout(self):
        self.app.layout = html.Div([
            # Header with Flight Details and Emissions
            html.Div([
                # Flight Details Card
                html.Div([
                    html.Div([
                        html.H2("Flight Details", className='section-header white-text'),
                        html.Div(id='flight-details', className='white-text')
                    ])
                ], className='card flight-card'),

                # Emissions Results Card
                html.Div([
                    html.Div([
                        html.H2("Emissions Results", className='section-header white-text'),
                        html.Div(id='emissions-results', className='white-text')
                    ])
                ], className='card emissions-card'),
            ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'}),

            # Transport Comparison Card
            html.Div([
                html.H2("Transport Mode Comparison", className='section-header'),
                html.Div(id='transport-comparison')
            ], className='card'),

            # Environmental Impact Card
            html.Div([
                html.H2("Environmental Impact Equivalencies", className='section-header'),
                html.Div(id='environmental-impact')
            ], className='card'),

            # Analysis Cards
            html.Div([
                # Carbon Price Analysis
                html.Div([
                    html.H2("Carbon Price Analysis", className='section-header'),
                    html.Div(id='carbon-price-analysis')
                ], className='card'),

                # Social Cost Analysis
                html.Div([
                    html.H2("Social Cost Analysis", className='section-header'),
                    html.Div(id='social-cost-analysis')
                ], className='card'),
            ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'}),

            dcc.Interval(
                id='interval-component',
                interval=2000,
                n_intervals=0
            )
        ], className='dashboard-container')

    def setup_callbacks(self):
        @self.app.callback(
            [Output('flight-details', 'children'),
             Output('emissions-results', 'children'),
             Output('environmental-impact', 'children'),
             Output('transport-comparison', 'children'),
             Output('carbon-price-analysis', 'children'),
             Output('social-cost-analysis', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            try:
                with open(os.path.join(tempfile.gettempdir(), 'dashboard_data.json'), 'r') as f:
                    data = json.load(f)

                # Flight Details - More compact
                flight_details = html.Div([
                    html.Div([
                        html.Span("🏠 ", style={'marginRight': '8px'}),
                        f"{data['home_team']} vs ",
                        html.Span("🏃 ", style={'marginRight': '8px', 'marginLeft': '8px'}),
                        data['away_team']
                    ]),
                    html.Div([
                        html.Span("📏 ", style={'marginRight': '8px'}),
                        f"{data['distance_km']:.1f} km | ",
                        html.Span("✈️ ", style={'marginRight': '8px', 'marginLeft': '8px'}),
                        f"{data['flight_type']} | ",
                        html.Span("🔄 ", style={'marginRight': '8px', 'marginLeft': '8px'}),
                        'Round Trip' if data['is_round_trip'] else 'One Way'
                    ])
                ])

                # Emissions Results
                emissions_results = html.Div([
                    html.Div([
                        html.Span("📊 ", style={'marginRight': '8px'}),
                        f"Total CO2: {data['total_emissions']:.2f} metric tons"
                    ]),
                    html.Div([
                        html.Span("👤 ", style={'marginRight': '8px'}),
                        f"Per Passenger: {data['per_passenger']:.2f} metric tons"
                    ])
                ])

                # Environmental Impact - Cleaner formatting
                IMPACT_LABELS = {
                    # Transportation
                    'gasoline_vehicles_year': 'Gasoline vehicles driven for one year',
                    'electric_vehicles_year': 'Electric vehicles driven for one year',
                    'gasoline_vehicle_miles': 'Miles driven by gasoline vehicle',
                    # Energy
                    'homes_energy_year': "Homes' energy use for one year",
                    'homes_electricity_year': "Homes' electricity use for one year",
                    'smartphones_charged': 'Smartphones charged',
                    # Natural
                    'tree_seedlings_10years': 'Tree seedlings grown for 10 years',
                    'forest_acres_year': 'Acres of U.S. forests in one year',
                    'forest_preserved_acres': 'Acres of U.S. forests preserved',
                    # Waste
                    'waste_tons_recycled': 'Tons of waste recycled',
                    'garbage_trucks_recycled': 'Garbage trucks of waste recycled',
                    'trash_bags_recycled': 'Trash bags of waste recycled',
                    # Fuel
                    'gasoline_gallons': 'Gallons of gasoline',
                    'diesel_gallons': 'Gallons of diesel',
                    'propane_cylinders': 'Propane cylinders for BBQ',
                    'oil_barrels': 'Barrels of oil'
                }

                impact_data = data['environmental_impact']
                environmental_impact = html.Div([
                    # Transportation Impact
                    html.Div([
                        html.Div("🚗 Transportation Impact", className='impact-header'),
                        *[html.Div(f"{value:.2f} {IMPACT_LABELS.get(desc, desc)}", className='impact-item')
                          for desc, value in impact_data.items()
                          if 'vehicle' in desc or 'mile' in desc]
                    ], className='impact-category'),

                    # Energy Usage
                    html.Div([
                        html.Div("⚡ Energy Usage", className='impact-header'),
                        *[html.Div(f"{value:.2f} {IMPACT_LABELS.get(desc, desc)}", className='impact-item')
                          for desc, value in impact_data.items()
                          if 'energy' in desc or 'electricity' in desc]
                    ], className='impact-category'),

                    # Environmental Offset
                    html.Div([
                        html.Div("🌳 Environmental Offset", className='impact-header'),
                        *[html.Div(f"{value:.2f} {IMPACT_LABELS.get(desc, desc)}", className='impact-item')
                          for desc, value in impact_data.items()
                          if 'tree' in desc or 'forest' in desc]
                    ], className='impact-category'),

                    # Waste & Resources
                    html.Div([
                        html.Div("♻️ Waste & Resources", className='impact-header'),
                        *[html.Div(f"{value:.2f} {IMPACT_LABELS.get(desc, desc)}", className='impact-item')
                          for desc, value in impact_data.items()
                          if 'waste' in desc or 'recycled' in desc]
                    ], className='impact-category'),

                    # Fuel Equivalents
                    html.Div([
                        html.Div("⛽ Fuel Equivalents", className='impact-header'),
                        *[html.Div(f"{value:.2f} {IMPACT_LABELS.get(desc, desc)}", className='impact-item')
                          for desc, value in impact_data.items()
                          if 'gasoline' in desc or 'diesel' in desc or 'oil' in desc]
                    ], className='impact-category')
                ])

                # Transport Mode Comparison
                transport_headers = ['Mode', 'Distance (km)', 'CO2 (t)', 'CO2 Saved (t)']
                transport_data = [
                    ['Air', f"{data['distance_km']:.1f}",
                     f"{data['transport_comparison']['air']:.2f}", ''],
                    ['Rail', f"{data['distance_km'] * 1.2:.1f}",
                     f"{data['transport_comparison']['rail']:.2f}",
                     f"{data['transport_comparison']['air'] - data['transport_comparison']['rail']:.2f}"],
                    ['Bus', f"{data['distance_km'] * 1.3:.1f}",
                     f"{data['transport_comparison']['bus']:.2f}",
                     f"{data['transport_comparison']['air'] - data['transport_comparison']['bus']:.2f}"]
                ]
                transport_comparison = self.create_table(transport_headers, transport_data)

                # Carbon Price Analysis
                carbon_price = html.Div([
                    html.P(f"Carbon Price: €45.00/tCO2"),
                    self.create_table(
                        ['Mode', 'Cost'],
                        [['Air', f"€ {data['transport_comparison']['air'] * 45:.2f}"],
                         ['Rail', f"€ {data['transport_comparison']['rail'] * 45:.2f}"],
                         ['Bus', f"€ {data['transport_comparison']['bus'] * 45:.2f}"]]
                    )
                ])

                # Social Cost Analysis
                social_cost_headers = ['Mode', 'Cost Type', 'Low', 'Median', 'Mean', 'High']
                social_cost_data = []
                for mode in ['Air', 'Rail', 'Bus']:
                    emissions = data['transport_comparison'][mode.lower()]
                    social_cost_data.extend([
                        [mode, 'Synthetic',
                         f"€ {emissions * 97:.0f}",
                         f"€ {emissions * 185:.0f}",
                         f"€ {emissions * 283:.0f}",
                         f"€ {emissions * 369:.0f}"],
                        ['', 'EPA', '', f"€ {emissions * 157:.0f}", '', ''],
                        ['', 'IWG', '', f"€ {emissions * 52:.0f}", '', '']
                    ])
                social_cost = self.create_table(social_cost_headers, social_cost_data)

                return (flight_details, emissions_results, environmental_impact,
                        transport_comparison, carbon_price, social_cost)

            except Exception as e:
                print(f"Error updating dashboard: {str(e)}")
                return ["Error loading data"] * 6

    def run_server(self, debug=True, port=8050):
        self.setup_callbacks()
        self.app.run_server(debug=debug, port=port)


if __name__ == '__main__':
    dashboard = DashboardApp()
    dashboard.run_server()
