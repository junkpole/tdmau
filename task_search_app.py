import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output

# --- 1. Load the Master Task Data ---
TASK_FILE = "tasks.xlsx"
DATA_FILE_ERROR = None

try:
    # Try loading with standard UTF-8 first
    try:
        df_all_tasks = pd.read_csv(TASK_FILE, header=1, encoding='utf-8')
    except UnicodeDecodeError:
        print("UTF-8 encoding failed, trying cp1251 (Windows-Cyrillic)...")
        # If that fails, try 'cp1251' which is standard for Cyrillic Excel files
        df_all_tasks = pd.read_csv(TASK_FILE, header=1, encoding='cp1251')

    # Drop any rows that are completely empty
    df_all_tasks = df_all_tasks.dropna(how='all')
    
    # Define the columns you want to be able to search
    SEARCH_COLS = [
        'Топшириқ мазмуни', 
        'Асосий ижрочи маъсуллар', 
        'Ижро ҳолати', 
        'Топшириқ берилган жой'
    ]
    # Ensure all search columns are present and are string type
    for col in SEARCH_COLS:
        if col in df_all_tasks.columns:
            df_all_tasks[col] = df_all_tasks[col].astype(str).fillna('')
        else:
            print(f"Warning: Search column '{col}' not found in file.")
            
    # Columns to display in the search results table
    DISPLAY_COLS = [
        'Банд', 
        'Топшириқ мазмуни', 
        'Ижро муддати', 
        'Асосий ижрочи маъсуллар', 
        'Ижро ҳолати', 
        'Изох'
    ]
    # Filter to only columns that actually exist in the loaded dataframe
    DISPLAY_COLS = [col for col in DISPLAY_COLS if col in df_all_tasks.columns]
    
    print("Successfully loaded task data.")
    
except FileNotFoundError:
    print(f"FATAL ERROR: Could not find the data file '{TASK_FILE}'.")
    DATA_FILE_ERROR = f"Error: The data file ({TASK_FILE}) was not found. The app cannot load."
    df_all_tasks = pd.DataFrame()
    
except Exception as e:
    print(f"An error occurred loading the data: {e}")
    DATA_FILE_ERROR = f"An error occurred loading data: {e}"
    df_all_tasks = pd.DataFrame()
    
except FileNotFoundError:
    print(f"FATAL ERROR: Could not find the data file '{TASK_FILE}'.")
    DATA_FILE_ERROR = f"Error: The data file ({TASK_FILE}) was not found. The app cannot load."
    df_all_tasks = pd.DataFrame() # Create empty dataframe to avoid more errors
    
except Exception as e:
    print(f"An error occurred loading the data: {e}")
    DATA_FILE_ERROR = f"An error occurred loading data: {e}"
    df_all_tasks = pd.DataFrame() # Create empty dataframe


# --- 2. Initialize the Dash App ---
app = dash.Dash(__name__)
server = app.server # This line is needed for services like Render
app.title = "Task Search System"

# --- 3. Define the App Layout ---
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'})(
    children=[
        html.H1("Task Management Search System", style={'textAlign': 'center', 'color': '#333'}),
        
        html.Div(
            [
                dcc.Input(
                    id='search-input',
                    placeholder="Search by task content, assignee, status, location...",
                    type='text',
                    # Disable input if data failed to load
                    disabled=DATA_FILE_ERROR is not None,
                    style={'width': '100%', 'padding': '12px', 'fontSize': '16px', 'borderRadius': '5px', 'border': '1px solid #ccc'}
                )
            ],
            style={'maxWidth': '800px', 'margin': '20px auto'}
        ),
        
        html.Hr(),
        
        dcc.Loading(
            id="loading-spinner",
            type="circle",
            children=[
                html.Div(id='results-output', style={'marginTop': '20px'})
            ]
        )
    ]
)

# --- 4. Create the Callback for Interactivity ---
@app.callback(
    Output('results-output', 'children'),
    [Input('search-input', 'value')]
)
def update_results(search_value):
    # If the data file failed to load, show the error
    if DATA_FILE_ERROR:
        return html.P(DATA_FILE_ERROR, style={'color': 'red', 'textAlign': 'center', 'fontSize': '18px'})
        
    if not search_value:
        return html.P("Please enter a search term to see matching tasks.", style={'textAlign': 'center', 'fontSize': '18px'})
        
    try:
        # Create a flexible filter mask.
        # This checks all SEARCH_COLS for the search_value.
        search_query = search_value.lower()
        mask = df_all_tasks[SEARCH_COLS].apply(
            lambda col: col.str.lower().str.contains(search_query, na=False)
        ).any(axis=1)
        
        filtered_df = df_all_tasks[mask]
        
        if filtered_df.empty:
            return html.P(f"No results found for '{search_value}'.", style={'textAlign': 'center', 'color': 'red', 'fontSize': '18px'})
        
        # Display the results in an interactive data table
        return dash_table.DataTable(
            data=filtered_df[DISPLAY_COLS].to_dict('records'),
            columns=[{"name": i, "id": i} for i in DISPLAY_COLS],
            page_size=20,  # Show 20 tasks per page
            sort_action="native",  # Allow sorting by clicking headers
            filter_action="native", # Allow column-level filtering
            style_table={'overflowX': 'auto'}, # Allow horizontal scrolling
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'whiteSpace': 'normal',
                'height': 'auto',
                'border': '1px solid #eee'
            },
            style_header={
                'backgroundColor': '#f8f8f8',
                'fontWeight': 'bold',
                'border': '1px solid #ddd'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#fcfcfc'
                }
            ]
        )
        
    except Exception as e:
        return html.P(f"An error occurred during search: {e}", style={'color': 'red'})

# --- 5. Run the App ---
if __name__ == '__main__':
    # 'host' is set to '0.0.0.0' to be accessible for deployment
    app.run_server(debug=False, host='0.0.0.0')
