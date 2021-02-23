# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 11:46:14 2020

@author: ksmeng
"""

import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_table
from dash.dependencies import Input, Output, State

import copy
import datetime
import pandas as pd
import requests, json


###################################################
# Constants
###################################################

config = dict(
    api_super_token = 'ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234',
    api_token       = 'E35EBAD0BDE751A7B0F154E4B817DF07',
    api_url         = 'https://redcap.healthinformatics.unimelb.edu.au/api/'
)

BOOL_NUMBERING = False
DATE_MIN = datetime.datetime(2021,1,1)
DATE_MAX = datetime.datetime(2021,12,31)
WIDTH_SHORT = 300
WIDTH_LONG = '100%'

# Styles for inner row
STYLE_NO_BORDER = {'display':'inline-block', 'width':'90%', 'position':'relative', 'verticalAlign':'middle',
                   'marginTop':'20px', 'marginBottom':'20px', 'padding':'10px'}
STYLE_BORDER_BLUE = {**STYLE_NO_BORDER, **{'border':'2px solid blue'}}
STYLE_BORDER_GREEN = {**STYLE_NO_BORDER, **{'border':'2px solid green'}}
STYLE_BORDER_RED = {**STYLE_NO_BORDER, **{'border':'2px solid red'}}

# Styles for outer row
STYLE_VISIBLE = {'display':True}
STYLE_HIDDEN = {'display':'none'}

# Styles for columns inside row
STYLE_ROW = {'float':'left', 'display':'inline-block'}
STYLE_ROW_LEFT = {**STYLE_ROW, **{'width':'60%', 'marginRight':'40px'}}
STYLE_ROW_CENTER = {**STYLE_ROW, **{'width':'30%'}}
STYLE_ROW_RIGHT = {**STYLE_ROW, **{'width':'90%'}}

# Styles for cells in data table
STYLE_CELL = {'width':'24%', 'fontSize':14, 'font-family':'sans-serif', 'textAlign':'left', 'whiteSpace':'normal'}
STYLE_BUTTON = {'width':'50%', 'display':'inline-block', 'textAlign':'center'}
STYLE_LAYOUT = {'fontFamily':'Arial', 'fontSize':48}

# Constants for main widget
VALUE_COMPONENT_MAIN = 'home'
DICT_OPTIONS_MAIN = {'home':'HOME'}
STYLE_ROW_LEFT_MAIN = {**STYLE_ROW, **{'width':'80%'}}
STYLE_ROW_CENTER_MAIN = {**STYLE_ROW, **{'width':'10%'}}
STYLE_ROW_RIGHT_MAIN = {**STYLE_ROW, **{'width':'90%'}}


###################################################
# Functions that interact with Redcap API
###################################################

def get_dict_answers_final(dict_answers):
    """
    Get dictionary of answers without None
    """
    dict_answers_final = copy.deepcopy(dict_answers)
    for key in dict_answers:
        if dict_answers_final[key] is None or dict_hide_branching_logic[key]:
            del dict_answers_final[key]
    return dict_answers_final


def send_record_to_redcap(patient_code):
    """
    Send data to Redcap
    """
    if patient_code is None:
        output_label = 'Error: Please enter patient code'
    else:
        record = get_dict_answers_final(dict_answers)
        record['record_id'] = patient_code
        data = json.dumps([record])
        fields = {
            'token': config['api_token'],
            'content': 'record',
            'format': 'json',
            'type': 'flat',
            'data': data,
        }
        r = requests.post(config['api_url'], data=fields)
        print('HTTP Status: ' + str(r.status_code))
        print(r.text)
        output_label = f'Record submitted (id = {patient_code})'
        output_label += f'\nFields completed = {len(record)-1}'
    return output_label


###################################################
# Functions to populate data table
###################################################
        
def get_question_from_key(field_name):
    return df_fields[df_fields['Variable / Field Name']==field_name]['Field Label'].iloc[0]


def get_choice_label_from_value(field_name, value):
    string = df_fields[df_fields['Variable / Field Name']==field_name]['Choices, Calculations, OR Slider Labels'].iloc[0]
    if type(string) is str:
        for choice in string.split('|'):
            if value == int(choice.split(',')[0].lstrip().rstrip()):
                return ','.join(choice.split(',')[1:]).lstrip().rstrip()
        return ''
    else:
        if value is not None:
            return value
        return ''


###################################################
# Functions to add HTML components
###################################################

def get_dict_options(choices):
    """
    Get dictionary of options from raw string in Redcap dictionary
    """
    if pd.isna(choices):
        return {}
    else:
        dict_choices = {}
        for choice in choices.split('|'):
            value = int(choice.split(',')[0])
            label = ','.join(choice.split(',')[1:]).lstrip().rstrip()
            dict_choices[value] = label
        return dict_choices


def get_form_initial_style(form):
    """
    Return initial style of forms
    """
    initial_style = STYLE_VISIBLE if form == 'home' else STYLE_HIDDEN
    return initial_style


def get_date_from_value(value, format_in="%Y-%m-%d", format_out="%Y-%m-%d"):
    """
    Check if value entered is a date
    Return string or False
    """
    try:
        dt = datetime.datetime.strptime(value, format_in)
        return dt.strftime(format_out)
    except:
        return False
    
   
def get_style_border_from_value(value):
    if value is None:
        return STYLE_BORDER_RED
    else:
        return STYLE_BORDER_GREEN
    
    
def get_type_component(field_name):
    """
    Return type of component based on field name
    """
    df = df_fields[df_fields['Variable / Field Name']==field_name]
    field_type = df['Field Type'].iloc[0]
    field_type_alt = df['Text Validation Type OR Show Slider Number'].iloc[0]
    if field_type == 'text':
        type_component = field_type if pd.isna(field_type_alt) else field_type_alt
    else:
        type_component = field_type
    return type_component


def add_html_left_part(label_children, label_help=None, style_left=STYLE_ROW_LEFT, style_center=STYLE_ROW_CENTER):
    html_help = '' if pd.isna(label_help) or label_help is None else html.Abbr("Info", title=label_help)
    return [html.Div(style=style_left, children=[
        dcc.Markdown(children=label_children)
    ]),
    html.Div(style=style_center, children=[
        html_help
    ])]

    
def add_html_component(type_component, id_component, label_children, label_help=None,
                       value_component=None, dict_options={},
                       value_min=None, value_max=None, value_step=1,
                       date_min=DATE_MIN, date_max=DATE_MAX, dict_marks={},
                       width_short=WIDTH_SHORT, width_long=WIDTH_LONG,
                       style_left=STYLE_ROW_LEFT, style_center=STYLE_ROW_CENTER,
                       style_right=STYLE_ROW_RIGHT, style_border=STYLE_BORDER_BLUE,
                       style_visibility=STYLE_VISIBLE):
    """
    Add HTML component, which is a row with 3 columns:
        - left: description (by default: 50% width)
        - center: help text (by default: 10% width)
        - right: widget (by default: 40% width)
    """
    
    ###################################################
    if type_component == 'dropdown':
        component = [dcc.Dropdown(id=id_component, value=value_component,
                                  options=[{'label':dict_options[i], 'value':i} for i in dict_options],
                                  style={'width':width_long}, optionHeight=80)]
        
    ###################################################
    elif type_component in ['radio', 'yesno']:
        if not dict_options: # if dictionary is empty, condition is satisfied
            dict_options = {1:'Yes', 0:'No'}
        component = [dcc.RadioItems(id=id_component, value=value_component,
                                    options=[{'label':dict_options[i], 'value':i} for i in dict_options])]
    ###################################################
    elif type_component in ['text','number']:
        component = [dcc.Input(id=id_component, value=value_component, type=type_component,
                               min=value_min, max=value_max, style={'width':width_short})]
        
    ###################################################
    elif type_component in ['date_dmy']:
        component = [dcc.DatePickerSingle(id=id_component, display_format='DD/MM/YYYY', date=None,
                                          min_date_allowed=date_min, max_date_allowed=date_max,
                                          initial_visible_month=datetime.datetime.now())]
    
    ###################################################
    elif type_component in ['slider']:
        component = [dcc.Slider(id=id_component, min=value_min, max=value_max,
                                value=value_min, step=value_step, marks=dict_marks)]
    
    ###################################################
    elif type_component in ['descriptive']:
        component = [dcc.Input(id=id_component, value=value_component, style=STYLE_HIDDEN)]
        style_border = STYLE_NO_BORDER # do not show border if row is descriptive
        
    ###################################################
    else:
        print(f'Component not added: {id_component}')
        component = []
    
    ###################################################
    children = add_html_left_part(label_children, label_help, style_left, style_center)
    children.append(html.Div(style=STYLE_ROW_RIGHT, children=component))
    return html.Div(id='row_outer_'+id_component, style=style_visibility, children=[
        html.Div(id='row_inner_'+id_component, style=style_border, children=children)
    ])


def add_html_form_home():
    """
    Add HTML components for "Home" form
    """
    children = []
    children.append(add_html_component('text', 'home_patient_code', 'Patient code'))
    children.append(add_html_component('number','home_visit_day', 'Day of visit (1-7)', value_min=1, value_max=7))
#    children.append(add_html_component('date', 'home_visit_date', 'Date of visit'))
    return html.Div(children=children)
    

def add_html_form_review():
    """
    Add HTML components for "Review" form
    """
    children = []
    children.append(html.Div(style=STYLE_NO_BORDER, children=[
        dash_table.DataTable(id='review_table', columns=[], data=None,
                             style_table={'minWidth':'100%'}, style_cell=STYLE_CELL)
    ]))
    children.append(html.Div(style=STYLE_NO_BORDER, children=[
        html.Div(id='label_submit', children='')
    ]))
    return html.Div(children=children)


def add_html_form(form, bool_numbering=BOOL_NUMBERING):
    """
    Inputs:
        - form: value of selected form (Form Name)
        - bool_numbering: show/hide question number, e.g. "1.1."
    """

    ###################################################
    # Filter dataframes based on form
    df = df_fields[df_fields['Form Name']==form]
    dff = df_forms[df_forms['Form Name']==form]
    
    ###################################################
    # Add title
    contents = [html.H3(dff['Title'].iloc[0])]
    
    ###################################################
    # Form is HOME
    if form in ['home']:
        contents.append(add_html_form_home())
        
    ###################################################
    # Form is REVIEW
    elif form in ['review']:
        contents.append(add_html_form_review())
    
    ###################################################
    # Form is an actual questionnaire
    else:
        # Loop through rows
        for i in df.index:
            
            # Create question number (if numbering is desired)
            idx_question = f"{dff['Form Index'].iloc[0]}.{list(df.index).index(i)+1}. " if bool_numbering else ''
            
            # Find type of component (be careful: text has subtypes)
            type_component = get_type_component(df['Variable / Field Name'][i])
            
            # Add section header (if corresponding column is not empty)
            if not pd.isna(df['Section Header'][i]):
                contents.append(html.H6(df['Section Header'][i]))
                
            # Add component
            contents.append(add_html_component(type_component=type_component,
                                               id_component=df['Variable / Field Name'][i],
                                               label_children=idx_question+df['Field Label'][i],
                                               label_help=df['Field Note'][i],
                                               dict_options=get_dict_options(df['Choices, Calculations, OR Slider Labels'][i]),
                                               style_visibility=get_field_style(df['Variable / Field Name'][i])))
            
    ###################################################
    return contents


###################################################
# Functions to manage global variables
###################################################

def get_dict_answers(df_fields):
    """
    This function is called once when app is started
    Return one output:
        - dict: a dictionary that summarizes the state of answers for all questions
    """
    dict_answers = {}
    for i in df_fields['Variable / Field Name'].values:
        dict_answers[i] = None
    return dict_answers


def get_variables_branching_logic(df_fields):
    """
    This function is called once when app is started
    Return two outputs:
        - list: all variables (field names) that have branching logic
        - dict: dictionary that summarizes the state of show/hide styles for all questions
    """
    list_check_branching_logic = []
    dict_hide_branching_logic = {}
    for i in range(df_fields.shape[0]):
        field_name = df_fields['Variable / Field Name'].iloc[i]
        branching_logic = df_fields['Branching Logic (Show field only if...)'].iloc[i]
        dict_hide_branching_logic[field_name] = type(branching_logic) == str # Hide field if string
        if type(branching_logic) == str:
            field_check = branching_logic.replace("[","]").split("]")[1] # get value between square brackets
            if field_check not in list_check_branching_logic:
                list_check_branching_logic.append(field_check)
    return list_check_branching_logic, dict_hide_branching_logic


def reset_global_variables():
    """
    Reset all answers to None
    """
    
    # Reset global variables
    for i in range(df_fields.shape[0]):
        field_name = df_fields['Variable / Field Name'].iloc[i]
        branching_logic = df_fields['Branching Logic (Show field only if...)'].iloc[i]
        dict_answers[field_name] = None
        dict_hide_branching_logic[field_name] = type(branching_logic) == str
        
    
    return True


def update_branching_logic(field_name_ref, value_ref):
    """
    This function is called once when app is started (to initialize callbacks for branching logic)
    Then, it is called every time that the user enters an answer (value_ref) to any question (field_name_ref)
    Inputs:
        - field_name_ref: field where value has been changed
        - value_ref: new value entered in field_name
    Output:
        - list_fields_updated: list of fields associated to branching logic (useful to initialize callbacks)
    """
    list_fields_updated = []
    if field_name_ref in list_check_branching_logic:
        for i in range(df_fields.shape[0]):
            field_name = df_fields['Variable / Field Name'].iloc[i]
            branching_logic = df_fields['Branching Logic (Show field only if...)'].iloc[i]
            if type(branching_logic) == str:
                field_name_check = branching_logic.replace("[","]").split("]")[1] # get value between square brackets
                value_check = branching_logic.replace(" ","").split("=")[1] # get value after the equal sign
                value_check = int(value_check.split("'")[1]) if "'" in value_check else int(value_check) # transform integer
                if field_name_ref == field_name_check:
                    dict_hide_branching_logic[field_name] = False if value_ref == value_check else True
                    list_fields_updated.append(field_name)
    return list_fields_updated



def get_field_style(field_name):
    """
    Return HTML style for showing/hiding the row corresponding to field_name
    """
    if dict_hide_branching_logic[field_name]:
        return STYLE_HIDDEN
    else:
        return STYLE_VISIBLE
    

########################################################
# Initialize variables to be used throughout whole user session
# These variables act as global variables
df_forms = pd.read_excel('https://raw.githubusercontent.com/kevinsmeng/delectable-demo/main/resources/list_forms_v3.xlsx')
df_fields = pd.read_excel('https://raw.githubusercontent.com/kevinsmeng/delectable-demo/main/resources/list_fields_v3.xlsx')
dict_answers = get_dict_answers(df_fields)
list_check_branching_logic, dict_hide_branching_logic = get_variables_branching_logic(df_fields)


########################################################
# Layout before defining callbacks
external_stylesheets = ['https://raw.githubusercontent.com/kevinsmeng/delectable-demo/main/assets/mycss.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.layout = html.Div(style=STYLE_LAYOUT, children=[
    # Main dropdown to select form
    html.Div(style={'width':'100%', 'display':'inline-block', 'verticalAlign':'top'},children=[
        add_html_component(type_component='dropdown', id_component='main_dropdown', label_children='**Select form...**',
                           value_component=VALUE_COMPONENT_MAIN, dict_options=DICT_OPTIONS_MAIN,
                           style_left=STYLE_ROW_LEFT_MAIN, style_center=STYLE_ROW_CENTER_MAIN,
                           style_right=STYLE_ROW_RIGHT_MAIN, style_border=STYLE_NO_BORDER)
    ]),
    # Contents of selected form
    html.Div(style={'width':'100%', 'display':'inline-block', 'verticalAlign':'top'},children=[
        html.Div(id='form_'+form, children=add_html_form(form)) for form in df_forms['Form Name'].values
    ]),
    # Previous and next buttons
    html.Div(style={'width':'100%', 'display':'inline-block', 'verticalAlign':'top', 'marginBottom':'50px'},children=[
        html.Button(id='button_previous', children='Previous', style=STYLE_BUTTON),
        html.Button(id='button_next', children='Next', style=STYLE_BUTTON),
        dcc.Store(id='back_to_top', data=[])
    ])
])


########################################################
# The loop creates multiple callbacks that are responsible for interactive processes:
# - update_answer(input_id): user answers a question -> answer is shown in the corresponding HTML component
# - update_style(input_id): user answers a question with branching logic -> additional questions are shown/hidden

def update_answer(input_id):
    """
    This function creates callback functions for answering questions
    """
    attribute = 'date' if get_type_component(input_id) == 'date_dmy' else 'value'
    @app.callback([Output(input_id, 'id'),
                   Output('row_inner_'+input_id, 'style')],
                  [Input(input_id, attribute)],
                  [State(input_id, 'id')], prevent_initial_call=True)
    def update_answer_repeated(value, field_name):
        
        # Update dictionary of answers in global variables
        if get_date_from_value(value): # returns a string (True)
            dict_answers[field_name] = get_date_from_value(value)
        else: # returns False
            dict_answers[field_name] = value
        print(f'Dictionary updated: {field_name}')
        print(f'Answer entered: {dict_answers[field_name]}')
        
        # Update dictionary in global variables
        _ = update_branching_logic(field_name, value)
            
        # First output triggers branching logic callback
        # Second output is an HTML style to change border color
        return field_name, get_style_border_from_value(value)


def update_style(input_id):
    """
    This function creates callback functions for branching logic
    """
    list_outputs = update_branching_logic(input_id, None)
    
    # Single output cannot be in a list when defining callback
    if len(list_outputs) == 1:
        @app.callback(Output('row_outer_'+list_outputs[0], 'style'),
                      [Input(input_id, 'id')], prevent_initial_call=True)
        def update_style_repeated(field_name):
            for i in df_fields['Variable / Field Name'].values:
                if i in list_outputs:
                    return get_field_style(i)
                
    # Multiple outputs in a list
    elif len(list_outputs) > 1:
        @app.callback([Output('row_outer_'+i, 'style') for i in list_outputs],
                      [Input(input_id, 'id')], prevent_initial_call=True)
        def update_style_repeated(field_name):
            list_styles = []
            for i in df_fields['Variable / Field Name'].values:
                if i in list_outputs:
                    list_styles.append(get_field_style(i))
            return list_styles
        
for i in df_fields['Variable / Field Name'].values:
    update_answer(i)
    update_style(i)


########################################################
# These callbacks are standard callbacks:
# - render_content(form, options): show selected form, show previous/next buttons
# - update_patient_code(code):
# - update_visit_day(day):
# - update_review(style): update data table contents when review form is shown
# - on_click_button_previous_next(): both Dash + JavaScript!
    
@app.callback([Output('form_'+tab, 'style') for tab in df_forms['Form Name'].values] + [Output('button_previous','style')] + [Output('button_next','style')] + [Output('button_next','children')],
              [Input('main_dropdown', 'value'),
               Input('main_dropdown', 'options')])
def render_content(form, options):
    """
    This callback is called when user clicks on any tab
    Shows questions associated with the clicked tab and hides the other questions
    """
        
    # Styles for different forms (only one form to show)
    list_styles = []
    for i in df_forms['Form Name'].values:
        list_styles.append(STYLE_VISIBLE if form==i else STYLE_HIDDEN)
    
    # Styles for previous/next buttons
    style_previous = STYLE_BUTTON
    style_next = STYLE_BUTTON
    if form is None or form == options[0]['value']:
        style_previous = STYLE_HIDDEN
    if form is None or len(options) == 1:
        style_next = STYLE_HIDDEN
    list_styles.append(style_previous)
    list_styles.append(style_next)
    
    # Children (text/label) for next button
    button_children = 'Submit' if form == options[-1]['value'] else 'Next'
    list_styles.append(button_children)
    
    return list_styles


@app.callback(Output('row_inner_home_patient_code','style'),
              [Input('home_patient_code', 'value')], prevent_initial_call=True)
def update_patient_code(code):
    if code is None:
        return STYLE_BORDER_RED
    else:
        return STYLE_BORDER_GREEN
    
    
@app.callback([Output('form_'+tab, 'children') for tab in list(df_forms['Form Name'].values)[1:]] + [Output('main_dropdown', 'options')] + [Output('row_inner_home_visit_day','style')],
              [Input('home_visit_day', 'value')], prevent_initial_call=True)
def update_visit_day(day):
    """
    This callback is called when user changes the value of "Day of visit (1-7)"
    CDAI questionnaire has to be different between days 1-6 and day 7
    Other questionnaires are only answered on day 7
    Outputs:
        - options in main dropdown
        - border color of row of "visit day"
    """
    
    # Reset global variables and form contents
    reset_global_variables()
    list_return = [add_html_form(form) for form in list(df_forms['Form Name'].values)[1:]]
    
    # Get forms for desired day and border color to tell limits
    dict_dropdown = {}
    if day is None: # No value or value outside limits (day 1-7)
        for form in df_forms['Form Name'].values:
            if form in ['home']:
                dict_dropdown[form] = form.upper()
        row_style = STYLE_BORDER_RED
    else:
        for form in df_forms['Form Name'].values:
            if day == 7: # Day 7: show all forms except "daily" forms
                if '_d' not in form:
                    dict_dropdown[form] = form.upper()
            else: # Days 1-6: show only "daily" forms + home + review
                if f'_d{day}' in form or form in ['home','review']:
                    dict_dropdown[form] = form.upper()
        row_style = STYLE_BORDER_GREEN
    list_options = [{'label':dict_dropdown[i], 'value':i} for i in dict_dropdown]
    
    # Append to the list to return
    list_return.append(list_options)
    list_return.append(row_style)
    return list_return


@app.callback([Output('review_table', 'data'),
               Output('review_table', 'columns')],
              [Input('form_review', 'style')], prevent_initial_call=True)
def update_review(style):
    """
    This callback is called when user clicks on the "review" tab
    Updates the DataTable object to display
    """
    df = pd.DataFrame(columns=['Question','Answer','Field Name','Value'])
    dict_answers_final = get_dict_answers_final(dict_answers)
    for i in range(len(dict_answers_final)):
        key = list(dict_answers_final.keys())[i]
        df.loc[i] = [get_question_from_key(key),
                     get_choice_label_from_value(key,dict_answers_final[key]),
                     key,
                     dict_answers_final[key]]
    data = df.to_dict('records')
    columns=[{"name": str(i), "id": str(i)} for i in df.columns]
    return data, columns


@app.callback([Output('main_dropdown', 'value'),
               Output('label_submit', 'children')],
              [Input('button_previous','n_clicks'),
               Input('button_next','n_clicks')],
              [State('button_next','children'),
               State('main_dropdown', 'value'),
               State('main_dropdown', 'options'),
               State('home_patient_code', 'value')], prevent_initial_call=True)
def on_click_button_previous_next(n_clicks_previous, n_clicks_next, id_next,
                                  value, options, patient_code):
    """
    Modify value of main dropdown, which in turn shows the corresponding form
    """
    
    # Determine current index of form (among available options)
    list_values = [options[i]['value'] for i in range(len(options))]
    idx_current = list_values.index(value)
    
    # Determine which Input has fired the callback
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger == 'button_previous':
        dropdown_value = list_values[idx_current-1]
        output_label = ''
    elif trigger == 'button_next':
        if id_next == 'Submit':
            output_label = send_record_to_redcap(patient_code)
            dropdown_value = value
        else:
            dropdown_value = list_values[idx_current+1]
            output_label = ''
    return dropdown_value, output_label


# This clientside callback is called when clicking on Previous or Next
# Scroll back to top (can be done only with JavaScript)
app.clientside_callback(
    """
    function(n_clicks_previous, n_clicks_next) {
    document.body.scrollTop = 0; // For Safari
    document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
    return "";
    }
    """,
    Output('back_to_top', 'data'), # Callback needs an output, so this is dummy
    Input('button_previous', 'n_clicks'), # This triggers the Javascript callback
    Input('button_next', 'n_clicks'), # This also triggers the Javascript callback
    prevent_initial_call=True
)


########################################################

if __name__ == '__main__':
    app.run_server(debug=True)
