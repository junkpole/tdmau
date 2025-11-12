import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State

# --- 1. Translations ---
# All UI text is now stored here
translations = {
    'uz': {
        'app_title': "Topshiriqlarni Qidirish Tizimi",
        'main_title': "Topshiriqlarni Boshqarish Tizimi",
        'placeholder': "Topshiriq mazmuni, ijrochi, holati bo'yicha qidirish...",
        'search_prompt': "Qidirish uchun so'z kiriting...",
        'no_results': "bo'yicha hech narsa topilmadi.",
        'search_error': "Qidirish vaqtida xatolik yuz berdi:",
        'footer_text': "Copyright © Termiz davlat muhandislik va agrotexnologiyalar universiteti / ",
        'footer_link': "IT bo'limi",
        'data_error_file': "Xatolik: Ma'lumotlar fayli topilmadi. Dastur yuklana olmaydi.",
        'data_error_load': "Ma'lumotlarni yuklashda xatolik yuz berdi:"
    },
    'en': {
        'app_title': "Task Search System",
        'main_title': "Task Management System",
        'placeholder': "Search by task content, assignee, status...",
        'search_prompt': "Please enter a search term...",
        'no_results': "No results found for",
        'search_error': "An error occurred during search:",
        'footer_text': "Copyright © Termiz State University of Engineering and Agrotechnologies / ",
        'footer_link': "IT Department",
        'data_error_file': "Error: The data file was not found. The app cannot load.",
        'data_error_load': "An error occurred loading data:"
    },
    'ru': {
        'app_title': "Система Управления Задачами",
        'main_title': "Система Управления Задачами",
        'placeholder': "Поиск по содержанию, исполнителю, статусу...",
        'search_prompt': "Введите слово для поиска...",
        'no_results': "Ничего не найдено по запросу",
        'search_error': "Произошла ошибка во время поиска:",
        'footer_text': "Copyright © Термезский государственный университет инженерии и агротехнологий / ",
        'footer_link': "IT-отдел",
        'data_error_file': "Ошибка: Файл данных не найден. Приложение не может загрузиться.",
        'data_error_load': "Произошла ошибка при загрузке данных:"
    }
}

# --- 2. Load the Master Task Data ---
TASK_FILE = "tasks.xlsx"
DATA_FILE_ERROR = None

try:
    # Use pd.read_excel to read .xlsx files
    # We specify header=1 (the second row) and the 'openpyxl' engine
    df_all_tasks = pd.read_excel(TASK_FILE, header=1, engine='openpyxl')

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
    DATA_FILE_ERROR = f"{translations['uz']['data_error_file']} ({TASK_FILE})"
    df_all_tasks = pd.DataFrame()
except Exception as e:
    print(f"An error occurred loading the data: {e}")
    DATA_FILE_ERROR = f"{translations['uz']['data_error_load']} {e}"
    df_all_tasks = pd.DataFrame()


# --- 3. Initialize the Dash App ---
app = dash.Dash(__name__)
server = app.server
app.title = translations['uz']['app_title'] # Default title

# --- 4. Define the App Layout ---
app.layout = html.Div(
    style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'minHeight': '100vh', 'display': 'flex', 'flexDirection': 'column'},
    children=[
        # Store for language preference
        dcc.Store(id='language-store', data='uz'), # Default language is Uzbek

        # Language Switcher
        html.Div(
            [
                dcc.RadioItems(
                    id='lang-switcher',
                    options=[
                        {'label': 'Oʻzbekcha', 'value': 'uz'},
                        {'label': 'English', 'value': 'en'},
                        {'label': 'Русский', 'value': 'ru'},
                    ],
                    value='uz', # Default value
                    labelStyle={'display': 'inline-block', 'marginRight': '15px', 'cursor': 'pointer'},
                    style={'padding': '10px'}
                )
            ],
            style={'textAlign': 'center', 'backgroundColor': '#f4f4f4', 'borderRadius': '5px', 'maxWidth': '300px', 'margin': '0 auto 20px auto'}
        ),

        # Main App Content
        html.Div(
            style={'flex': '1'},
            children=[
                html.H1(id='main-title', style={'textAlign': 'center', 'color': '#333'}),
                html.Div(
                    [
                        dcc.Input(
                            id='search-input',
                            type='text',
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
        ),
        
        # Footer
        html.Footer(id='footer', style={'textAlign': 'center', 'marginTop': '40px', 'padding': '20px', 'color': '#777', 'borderTop': '1px solid #eee'})
    ]
)


# --- 5. Callbacks ---

# Callback to update language in store
@app.callback(
    Output('language-store', 'data'),
    Input('lang-switcher', 'value')
)
def update_language(lang):
    return lang

# Callback to update all UI text based on language
@app.callback(
    [Output('main-title', 'children'),
     Output('search-input', 'placeholder'),
     Output('footer', 'children'),
     Output('app-title', 'title')], # Update browser tab title
    Input('language-store', 'data')
)
def update_ui_text(lang):
    t = translations[lang]
    footer_children = [
        html.Span(t['footer_text']),
        html.A(
            t['footer_link'],
            href="https://www.instagram.com/iamumarsatti/?hl=en",
            target="_blank",
            style={'color': '#007bff', 'textDecoration': 'none', 'fontWeight': 'bold'}
        )
    ]
    # Note: Dash does not officially support changing app.title dynamically after load.
    # This (Output('app-title', 'title')) is a small hack and may not always work,
    # but the 'main-title' and other elements will update perfectly.
    # We will update the 'app.title' as well, which sets the <title> tag.
    app.title = t['app_title'] 
    return t['main_title'], t['placeholder'], footer_children, t['app_title']

# Callback for search logic
@app.callback(
    Output('results-output', 'children'),
    Input('search-input', 'value'),
    State('language-store', 'data') # Use State so it doesn't re-trigger
)
def update_results(search_value, lang):
    t = translations[lang]

    if DATA_FILE_ERROR:
        # Use the stored error message (which is already translated)
        return html.P(DATA_FILE_ERROR, style={'color': 'red', 'textAlign': 'center', 'fontSize': '18px'})

    if not search_value:
        return html.P(t['search_prompt'], style={'textAlign': 'center', 'fontSize': '18px'})

    try:
        search_query = search_value.lower()
        mask = df_all_tasks[SEARCH_COLS].apply(
            lambda col: col.str.lower().str.contains(search_query, na=False)
        ).any(axis=1)

        filtered_df = df_all_tasks[mask]

        if filtered_df.empty:
            # Handle different word order for "no results"
            if lang == 'en':
                no_results_text = f"{t['no_results']} '{search_value}'"
            else:
                no_results_text = f"'{search_value}' {t['no_results']}"
            return html.P(no_results_text, style={'textAlign': 'center', 'color': 'red', 'fontSize': '18px'})

        return dash_table.DataTable(
            data=filtered_df[DISPLAY_COLS].to_dict('records'),
            columns=[{"name": i, "id": i} for i in DISPLAY_COLS],
            page_size=20,
            sort_action="native",
            filter_action="native",
            style_table={'overflowX': 'auto'},
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
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#fcfcfc'}
            ]
        )

    except Exception as e:
        return html.P(f"{t['search_error']} {e}", style={'color': 'red'})


# --- 6. Run the App ---
if __name__ == '__main__':
    # Use app.run, not app.run_server
    app.run(debug=False, host='0.0.0.0')
