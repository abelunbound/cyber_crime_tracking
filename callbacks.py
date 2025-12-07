from dash import Input, Output, State, dash_table, ctx
import dash_bootstrap_components as dbc
from dash import html
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def register_callbacks(app, db):
    """Register all callbacks for the application"""
    
    # Submit new case callback
    @app.callback(
        Output('case-form-alert', 'children'),
        Input('submit-case-button', 'n_clicks'),
        [State('case-title', 'value'),
         State('case-crime-type', 'value'),
         State('case-incident-date', 'value'),
         State('case-location', 'value'),
         State('case-victim-name', 'value'),
         State('case-victim-contact', 'value'),
         State('case-suspect-name', 'value'),
         State('case-suspect-details', 'value'),
         State('case-description', 'value'),
         State('case-evidence', 'value'),
         State('case-priority', 'value'),
         State('case-status', 'value'),
         State('session-store', 'data')],
        prevent_initial_call=True
    )
    def submit_case(n_clicks, title, crime_type, incident_date, location, victim_name,
                   victim_contact, suspect_name, suspect_details, description, evidence,
                   priority, status, session_data):
        if not all([title, crime_type, incident_date]):
            return dbc.Alert("Please fill in all required fields (Title, Crime Type, Incident Date)", 
                           color="warning", duration=4000)
        
        case_data = {
            'title': title,
            'crime_type': crime_type,
            'incident_date': incident_date,
            'location': location,
            'victim_name': victim_name,
            'victim_contact': victim_contact,
            'suspect_name': suspect_name,
            'suspect_details': suspect_details,
            'description': description,
            'evidence': evidence,
            'priority': priority,
            'status': status,
            'created_by': session_data.get('username', 'system') if session_data else 'system'
        }
        
        result = db.add_case(case_data)
        
        if result['success']:
            return dbc.Alert(f"Case registered successfully! Case ID: {result['case_id']}", 
                           color="success", duration=4000)
        else:
            return dbc.Alert(f"Error: {result['error']}", color="danger", duration=4000)
    
    # Cases by type chart callback
    @app.callback(
        Output('cases-by-type-chart', 'figure'),
        Input('interval-component', 'n_intervals')
    )
    def update_cases_by_type_chart(n):
        df = db.get_cases_by_type()
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No data available", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        fig = px.pie(df, values='count', names='crime_type', 
                    title='Distribution by Crime Type',
                    color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        return fig
    
    # Cases by status chart callback
    @app.callback(
        Output('cases-by-status-chart', 'figure'),
        Input('interval-component', 'n_intervals')
    )
    def update_cases_by_status_chart(n):
        df = db.get_cases_by_status()
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No data available", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        colors = {
            'Pending': '#F39C12',
            'Under Investigation': '#3498DB',
            'Resolved': '#27AE60',
            'Closed': '#95A5A6'
        }
        
        fig = px.bar(df, x='status', y='count',
                    title='Cases by Status',
                    color='status',
                    color_discrete_map=colors)
        fig.update_layout(showlegend=False, xaxis_title='Status', yaxis_title='Number of Cases')
        
        return fig
    
    # Recent cases table callback
    @app.callback(
        Output('recent-cases-table', 'children'),
        Input('interval-component', 'n_intervals')
    )
    def update_recent_cases_table(n):
        df = db.get_recent_cases(10)
        
        if df.empty:
            return html.P("No cases found", className="text-muted")
        
        # Select and rename columns for display
        display_df = df[['case_id', 'title', 'crime_type', 'status', 'priority', 'created_at']].copy()
        display_df.columns = ['Case ID', 'Title', 'Crime Type', 'Status', 'Priority', 'Created']
        
        return dash_table.DataTable(
            data=display_df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in display_df.columns],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'Arial'
            },
            style_header={
                'backgroundColor': '#2C3E50',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#F8F9FA'
                }
            ],
            page_size=10
        )
    
    # Cases list table callback
    @app.callback(
        Output('cases-list-table', 'children'),
        [Input('case-search-input', 'value'),
         Input('case-status-filter', 'value')]
    )
    def update_cases_list(search_text, status_filter):
        if status_filter == 'all':
            df = db.get_all_cases()
        else:
            df = db.get_all_cases(status_filter)
        
        # Apply search filter if provided
        if search_text:
            mask = df.apply(lambda row: row.astype(str).str.contains(search_text, case=False).any(), axis=1)
            df = df[mask]
        
        if df.empty:
            return html.P("No cases found", className="text-muted")
        
        # Select columns for display
        display_df = df[['case_id', 'title', 'crime_type', 'incident_date', 
                        'location', 'status', 'priority', 'created_at']].copy()
        display_df.columns = ['Case ID', 'Title', 'Crime Type', 'Incident Date', 
                             'Location', 'Status', 'Priority', 'Created']
        
        return dash_table.DataTable(
            data=display_df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in display_df.columns],
            filter_action="native",
            sort_action="native",
            page_action="native",
            page_size=20,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'Arial',
                'minWidth': '100px'
            },
            style_header={
                'backgroundColor': '#2C3E50',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#F8F9FA'
                },
                {
                    'if': {'filter_query': '{Status} = "Resolved"', 'column_id': 'Status'},
                    'backgroundColor': '#D4EDDA',
                    'color': '#155724'
                },
                {
                    'if': {'filter_query': '{Status} = "Pending"', 'column_id': 'Status'},
                    'backgroundColor': '#FFF3CD',
                    'color': '#856404'
                },
                {
                    'if': {'filter_query': '{Priority} = "Critical"', 'column_id': 'Priority'},
                    'backgroundColor': '#F8D7DA',
                    'color': '#721C24'
                }
            ]
        )
    
    # Search results callback
    @app.callback(
        Output('search-results', 'children'),
        Input('search-button', 'n_clicks'),
        [State('search-text', 'value'),
         State('search-crime-type', 'value'),
         State('search-date-range', 'start_date'),
         State('search-date-range', 'end_date')],
        prevent_initial_call=True
    )
    def perform_search(n_clicks, search_text, crime_type, start_date, end_date):
        df = db.search_cases(search_text or '', crime_type, start_date, end_date)
        
        if df.empty:
            return dbc.Alert("No cases found matching your search criteria", color="info")
        
        # Display results
        display_df = df[['case_id', 'title', 'crime_type', 'incident_date', 
                        'victim_name', 'status', 'priority']].copy()
        display_df.columns = ['Case ID', 'Title', 'Crime Type', 'Incident Date', 
                             'Victim', 'Status', 'Priority']
        
        return html.Div([
            html.H5(f"Found {len(df)} case(s)", className="mb-3"),
            dash_table.DataTable(
                data=display_df.to_dict('records'),
                columns=[{'name': col, 'id': col} for col in display_df.columns],
                filter_action="native",
                sort_action="native",
                page_action="native",
                page_size=15,
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontFamily': 'Arial'
                },
                style_header={
                    'backgroundColor': '#2C3E50',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#F8F9FA'
                    }
                ]
            )
        ])
    
    # Trend chart callback
    @app.callback(
        Output('trend-chart', 'figure'),
        Input('interval-component', 'n_intervals')
    )
    def update_trend_chart(n):
        # Get data for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        df = db.get_trend_data(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No data available", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        fig = px.line(df, x='date', y='count',
                     title='Case Trend (Last 30 Days)',
                     labels={'date': 'Date', 'count': 'Number of Cases'})
        fig.update_traces(mode='lines+markers')
        fig.update_layout(hovermode='x unified')
        
        return fig
    
    # Generate report callback
    @app.callback(
        Output('report-output', 'children'),
        Input('generate-report-button', 'n_clicks'),
        [State('report-type', 'value'),
         State('report-date-range', 'start_date'),
         State('report-date-range', 'end_date')],
        prevent_initial_call=True
    )
    def generate_report(n_clicks, report_type, start_date, end_date):
        if report_type == 'monthly':
            # Monthly summary
            df = db.get_trend_data(start_date, end_date)
            total = df['count'].sum() if not df.empty else 0
            
            return html.Div([
                html.H5("Monthly Summary Report"),
                html.Hr(),
                html.P(f"Total Cases: {total}"),
                html.P(f"Period: {start_date or 'All time'} to {end_date or 'Present'}"),
                dash_table.DataTable(
                    data=df.to_dict('records') if not df.empty else [],
                    columns=[{'name': 'Date', 'id': 'date'}, {'name': 'Cases', 'id': 'count'}],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'backgroundColor': '#2C3E50', 'color': 'white'}
                ) if not df.empty else html.P("No data for selected period")
            ])
        
        elif report_type == 'crime_type':
            # Crime type analysis
            df = db.get_cases_by_type()
            
            return html.Div([
                html.H5("Crime Type Analysis"),
                html.Hr(),
                dash_table.DataTable(
                    data=df.to_dict('records') if not df.empty else [],
                    columns=[{'name': 'Crime Type', 'id': 'crime_type'}, 
                            {'name': 'Count', 'id': 'count'}],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'backgroundColor': '#2C3E50', 'color': 'white'}
                ) if not df.empty else html.P("No data available")
            ])
        
        elif report_type == 'status':
            # Status overview
            df = db.get_cases_by_status()
            
            return html.Div([
                html.H5("Status Overview"),
                html.Hr(),
                dash_table.DataTable(
                    data=df.to_dict('records') if not df.empty else [],
                    columns=[{'name': 'Status', 'id': 'status'}, 
                            {'name': 'Count', 'id': 'count'}],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'backgroundColor': '#2C3E50', 'color': 'white'}
                ) if not df.empty else html.P("No data available")
            ])
        
        return html.P("Report generated")
    
    # Users table callback
    @app.callback(
        Output('users-table', 'children'),
        Input('interval-component', 'n_intervals')
    )
    def update_users_table(n):
        df = db.get_all_users()
        
        if df.empty:
            return html.P("No users found", className="text-muted")
        
        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in df.columns],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'Arial'
            },
            style_header={
                'backgroundColor': '#2C3E50',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#F8F9FA'
                }
            ],
            page_size=10
        )
    
    # Add user callback
    @app.callback(
        Output('user-form-alert', 'children'),
        Input('add-user-button', 'n_clicks'),
        [State('new-username', 'value'),
         State('new-password', 'value'),
         State('new-fullname', 'value'),
         State('new-role', 'value')],
        prevent_initial_call=True
    )
    def add_user(n_clicks, username, password, fullname, role):
        if not all([username, password, fullname]):
            return dbc.Alert("Please fill in all fields", color="warning", duration=3000)
        
        result = db.add_user(username, password, fullname, role)
        
        if result['success']:
            return dbc.Alert("User added successfully!", color="success", duration=3000)
        else:
            return dbc.Alert(f"Error: {result['error']}", color="danger", duration=3000)
    
    # Logout callback
    @app.callback(
        Output('url', 'pathname'),
        Input('logout-button', 'n_clicks'),
        State('session-store', 'data'),
        prevent_initial_call=True
    )
    def logout(n_clicks, session_data):
        if session_data:
            db.log_activity(session_data.get('username', 'unknown'), 'LOGOUT', 'User logged out')
        return '/'
