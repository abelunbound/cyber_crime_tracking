import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import Database
from auth import AuthManager

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True
)
app.title = "Gloria's Cybercrime Management System"
server = app.server

# Initialize database and auth manager
db = Database()
auth_manager = AuthManager(db)

# Color scheme
COLORS = {
    'primary': '#2C3E50',
    'secondary': '#3498DB',
    'success': '#27AE60',
    'danger': '#E74C3C',
    'warning': '#F39C12',
    'info': '#16A085',
    'light': '#ECF0F1',
    'dark': '#34495E'
}

# Login page layout
def get_login_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-shield-alt fa-3x mb-3"),
                        html.H3("Gloria's Cybercrime Management System", className="text-center")
                    ], className="bg-primary text-white"),
                    dbc.CardBody([
                        html.Div(id='login-alert'),
                        dbc.Input(
                            id='username-input',
                            placeholder='Username',
                            type='text',
                            className='mb-3'
                        ),
                        dbc.Input(
                            id='password-input',
                            placeholder='Password',
                            type='password',
                            className='mb-3'
                        ),
                        dbc.Button(
                            'Login',
                            id='login-button',
                            color='primary',
                            className='w-100',
                            n_clicks=0
                        )
                    ])
                ], className="shadow-lg")
            ], width=4)
        ], justify='center', className='min-vh-100 align-items-center')
    ], fluid=True)

# Main dashboard layout
def get_dashboard_layout(username='Guest'):
    return dbc.Container([
        # Interval for auto-refresh
        dcc.Interval(id='interval-component', interval=60000, n_intervals=0),
        
        # Header
        dbc.Navbar([
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.I(className="fas fa-shield-alt fa-2x me-2"),
                        dbc.NavbarBrand("Gloria's Cybercrime Management System", className="ms-2")
                    ], width="auto"),
                    dbc.Col([
                        dbc.Nav([
                            dbc.NavItem(dbc.NavLink([html.I(className="fas fa-user me-2"), html.Span(username, id='username-display')], href="#")),
                            dbc.NavItem(dbc.Button("Logout", id='logout-button', color="danger", size="sm"))
                        ], className="ms-auto", navbar=True)
                    ])
                ], className="w-100", align="center")
            ], fluid=True)
        ], color="primary", dark=True, className="mb-4"),
        
        # Main content
        dbc.Row([
            # Sidebar
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Nav([
                            dbc.NavLink([html.I(className="fas fa-tachometer-alt me-2"), "Dashboard"], 
                                       id='nav-dashboard', active=True, href="#"),
                            dbc.NavLink([html.I(className="fas fa-file-alt me-2"), "Cases"], 
                                       id='nav-cases', href="#"),
                            dbc.NavLink([html.I(className="fas fa-plus-circle me-2"), "New Case"], 
                                       id='nav-new-case', href="#"),
                            dbc.NavLink([html.I(className="fas fa-search me-2"), "Search"], 
                                       id='nav-search', href="#"),
                            dbc.NavLink([html.I(className="fas fa-chart-bar me-2"), "Reports"], 
                                       id='nav-reports', href="#"),
                            dbc.NavLink([html.I(className="fas fa-users me-2"), "Users"], 
                                       id='nav-users', href="#"),
                        ], vertical=True, pills=True)
                    ])
                ])
            ], width=2),
            
            # Main content area
            dbc.Col([
                html.Div(id='page-content')
            ], width=10)
        ])
    ], fluid=True)

# Dashboard page
def get_dashboard_page():
    # Get statistics
    stats = db.get_statistics()
    
    return html.Div([
        html.H2("Dashboard Overview", className="mb-4"),
        
        # Statistics cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-file-alt fa-3x text-primary"),
                            html.H3(stats['total_cases'], className="mt-2"),
                            html.P("Total Cases", className="text-muted")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-hourglass-half fa-3x text-warning"),
                            html.H3(stats['pending_cases'], className="mt-2"),
                            html.P("Pending Cases", className="text-muted")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-check-circle fa-3x text-success"),
                            html.H3(stats['resolved_cases'], className="mt-2"),
                            html.P("Resolved Cases", className="text-muted")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-users fa-3x text-info"),
                            html.H3(stats['total_users'], className="mt-2"),
                            html.P("System Users", className="text-muted")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=3)
        ], className="mb-4"),
        
        # Charts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Cases by Type"),
                    dbc.CardBody([
                        dcc.Graph(id='cases-by-type-chart')
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Cases by Status"),
                    dbc.CardBody([
                        dcc.Graph(id='cases-by-status-chart')
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Recent cases table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Recent Cases"),
                    dbc.CardBody([
                        html.Div(id='recent-cases-table')
                    ])
                ])
            ])
        ])
    ])

# Cases list page
def get_cases_page():
    return html.Div([
        html.H2("All Cases", className="mb-4"),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Input(
                            id='case-search-input',
                            placeholder='Search cases...',
                            type='text',
                            className='mb-3'
                        )
                    ], width=8),
                    dbc.Col([
                        dbc.Select(
                            id='case-status-filter',
                            options=[
                                {'label': 'All Status', 'value': 'all'},
                                {'label': 'Pending', 'value': 'Pending'},
                                {'label': 'Under Investigation', 'value': 'Under Investigation'},
                                {'label': 'Resolved', 'value': 'Resolved'},
                                {'label': 'Closed', 'value': 'Closed'}
                            ],
                            value='all',
                            className='mb-3'
                        )
                    ], width=4)
                ]),
                html.Div(id='cases-list-table')
            ])
        ])
    ])

# New case page
def get_new_case_page():
    return html.Div([
        html.H2("Register New Case", className="mb-4"),
        dbc.Card([
            dbc.CardBody([
                html.Div(id='case-form-alert'),
                dbc.Form([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Case Title"),
                            dbc.Input(id='case-title', type='text', placeholder='Enter case title')
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Crime Type"),
                            dbc.Select(
                                id='case-crime-type',
                                options=[
                                    {'label': 'Hacking', 'value': 'Hacking'},
                                    {'label': 'Phishing', 'value': 'Phishing'},
                                    {'label': 'Identity Theft', 'value': 'Identity Theft'},
                                    {'label': 'Online Fraud', 'value': 'Online Fraud'},
                                    {'label': 'Malware', 'value': 'Malware'},
                                    {'label': 'Ransomware', 'value': 'Ransomware'},
                                    {'label': 'Cyberstalking', 'value': 'Cyberstalking'},
                                    {'label': 'Data Breach', 'value': 'Data Breach'},
                                    {'label': 'Other', 'value': 'Other'}
                                ]
                            )
                        ], width=6)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Incident Date"),
                            dbc.Input(id='case-incident-date', type='date')
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Location"),
                            dbc.Input(id='case-location', type='text', placeholder='Enter location')
                        ], width=6)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Victim Name"),
                            dbc.Input(id='case-victim-name', type='text', placeholder='Enter victim name')
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Victim Contact"),
                            dbc.Input(id='case-victim-contact', type='text', placeholder='Enter contact information')
                        ], width=6)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Suspect Name (if known)"),
                            dbc.Input(id='case-suspect-name', type='text', placeholder='Enter suspect name')
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Suspect Details"),
                            dbc.Input(id='case-suspect-details', type='text', placeholder='Enter any known details')
                        ], width=6)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Description"),
                            dbc.Textarea(id='case-description', placeholder='Enter detailed description of the incident', 
                                       style={'height': '150px'})
                        ])
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Evidence/Notes"),
                            dbc.Textarea(id='case-evidence', placeholder='Enter evidence details, digital fingerprints, etc.', 
                                       style={'height': '100px'})
                        ])
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Priority Level"),
                            dbc.Select(
                                id='case-priority',
                                options=[
                                    {'label': 'Low', 'value': 'Low'},
                                    {'label': 'Medium', 'value': 'Medium'},
                                    {'label': 'High', 'value': 'High'},
                                    {'label': 'Critical', 'value': 'Critical'}
                                ],
                                value='Medium'
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Status"),
                            dbc.Select(
                                id='case-status',
                                options=[
                                    {'label': 'Pending', 'value': 'Pending'},
                                    {'label': 'Under Investigation', 'value': 'Under Investigation'},
                                    {'label': 'Resolved', 'value': 'Resolved'},
                                    {'label': 'Closed', 'value': 'Closed'}
                                ],
                                value='Pending'
                            )
                        ], width=6)
                    ], className="mb-3"),
                    
                    dbc.Button("Submit Case", id='submit-case-button', color='primary', className='mt-3')
                ])
            ])
        ])
    ])

# Search page
def get_search_page():
    return html.Div([
        html.H2("Search Cases", className="mb-4"),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Search by Case ID or Title"),
                        dbc.Input(id='search-text', type='text', placeholder='Enter search term')
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Crime Type"),
                        dbc.Select(
                            id='search-crime-type',
                            options=[
                                {'label': 'All Types', 'value': 'all'},
                                {'label': 'Hacking', 'value': 'Hacking'},
                                {'label': 'Phishing', 'value': 'Phishing'},
                                {'label': 'Identity Theft', 'value': 'Identity Theft'},
                                {'label': 'Online Fraud', 'value': 'Online Fraud'},
                                {'label': 'Malware', 'value': 'Malware'},
                                {'label': 'Other', 'value': 'Other'}
                            ],
                            value='all'
                        )
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Date Range"),
                        dcc.DatePickerRange(
                            id='search-date-range',
                            start_date_placeholder_text="Start Date",
                            end_date_placeholder_text="End Date"
                        )
                    ], width=4)
                ], className="mb-3"),
                
                dbc.Button("Search", id='search-button', color='primary', className='mb-3'),
                
                html.Hr(),
                
                html.Div(id='search-results')
            ])
        ])
    ])

# Reports page
def get_reports_page():
    return html.Div([
        html.H2("Reports & Analytics", className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Generate Report"),
                    dbc.CardBody([
                        dbc.Label("Report Type"),
                        dbc.Select(
                            id='report-type',
                            options=[
                                {'label': 'Monthly Summary', 'value': 'monthly'},
                                {'label': 'Crime Type Analysis', 'value': 'crime_type'},
                                {'label': 'Status Overview', 'value': 'status'},
                                {'label': 'Custom Report', 'value': 'custom'}
                            ],
                            value='monthly'
                        ),
                        dbc.Label("Date Range", className="mt-3"),
                        dcc.DatePickerRange(
                            id='report-date-range',
                            start_date_placeholder_text="Start Date",
                            end_date_placeholder_text="End Date"
                        ),
                        dbc.Button("Generate Report", id='generate-report-button', 
                                 color='primary', className='mt-3 w-100')
                    ])
                ])
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Report Output"),
                    dbc.CardBody([
                        html.Div(id='report-output')
                    ])
                ])
            ], width=8)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Trend Analysis"),
                    dbc.CardBody([
                        dcc.Graph(id='trend-chart')
                    ])
                ])
            ])
        ])
    ])

# Users page (admin only)
def get_users_page():
    return html.Div([
        html.H2("User Management", className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Add New User"),
                    dbc.CardBody([
                        html.Div(id='user-form-alert'),
                        dbc.Label("Username"),
                        dbc.Input(id='new-username', type='text', placeholder='Enter username', className='mb-2'),
                        dbc.Label("Password"),
                        dbc.Input(id='new-password', type='password', placeholder='Enter password', className='mb-2'),
                        dbc.Label("Full Name"),
                        dbc.Input(id='new-fullname', type='text', placeholder='Enter full name', className='mb-2'),
                        dbc.Label("Role"),
                        dbc.Select(
                            id='new-role',
                            options=[
                                {'label': 'Admin', 'value': 'Admin'},
                                {'label': 'Investigator', 'value': 'Investigator'},
                                {'label': 'Analyst', 'value': 'Analyst'},
                                {'label': 'Viewer', 'value': 'Viewer'}
                            ],
                            value='Viewer',
                            className='mb-3'
                        ),
                        dbc.Button("Add User", id='add-user-button', color='primary', className='w-100')
                    ])
                ])
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("All Users"),
                    dbc.CardBody([
                        html.Div(id='users-table')
                    ])
                ])
            ], width=8)
        ])
    ])

# App layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-layout'),
    dcc.Store(id='session-store', storage_type='session')
])

# Import callbacks module
from callbacks import register_callbacks

# Core authentication and navigation callbacks
@app.callback(
    Output('page-layout', 'children'),
    [Input('url', 'pathname'),
     Input('session-store', 'data')]
)
def display_page(pathname, session_data):
    if session_data and session_data.get('logged_in'):
        username = session_data.get('username', 'Guest')
        return get_dashboard_layout(username)
    return get_login_layout()

@app.callback(
    [Output('session-store', 'data'),
     Output('login-alert', 'children')],
    Input('login-button', 'n_clicks'),
    [State('username-input', 'value'),
     State('password-input', 'value')],
    prevent_initial_call=True
)
def login(n_clicks, username, password):
    if n_clicks and username and password:
        user = auth_manager.authenticate(username, password)
        if user:
            return {'logged_in': True, 'username': user['username'], 'role': user['role']}, None
        return None, dbc.Alert("Invalid credentials", color="danger", duration=3000)
    return None, None

@app.callback(
    Output('page-content', 'children'),
    [Input('nav-dashboard', 'n_clicks'),
     Input('nav-cases', 'n_clicks'),
     Input('nav-new-case', 'n_clicks'),
     Input('nav-search', 'n_clicks'),
     Input('nav-reports', 'n_clicks'),
     Input('nav-users', 'n_clicks')],
    prevent_initial_call=True
)
def navigate(dash_clicks, cases_clicks, new_clicks, search_clicks, reports_clicks, users_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return get_dashboard_page()
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'nav-dashboard':
        return get_dashboard_page()
    elif button_id == 'nav-cases':
        return get_cases_page()
    elif button_id == 'nav-new-case':
        return get_new_case_page()
    elif button_id == 'nav-search':
        return get_search_page()
    elif button_id == 'nav-reports':
        return get_reports_page()
    elif button_id == 'nav-users':
        return get_users_page()
    
    return get_dashboard_page()

# Register all other callbacks
register_callbacks(app, db)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
else:
    server = app.server # for GCP
