from dash import Dash, dcc, html
import dash.dependencies
from dash.dependencies import Output, Input, State
import dash_daq as daq
from dash import html
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeChangerAIO
import RPi.GPIO as GPIO
import time
import Freenove_DHT as DHT
import smtplib
import imaplib
from imapclient import IMAPClient
import easyimap as imap
import email
import sqlite3
#import paho.mqtt.client as mqtt
import random
from paho.mqtt import client as mqtt_client
from datetime import datetime
#This is to set time in specific timezone
import pytz



LED = 18
DHTPin = 17 #define the pin of DHT11 - physical pin, not GPIO pin
dht = DHT.DHT(DHTPin) #create a DHT class object
# dht.readDHT11()
GPIO.setmode(GPIO.BCM) 
Motor1 = 22 # Enable Pin
Motor2 = 27 # Input Pin
Motor3 = 19 # Input Pin   04 I think would work
GPIO.setup(Motor1,GPIO.OUT)
GPIO.setup(Motor2,GPIO.OUT)
GPIO.setup(Motor3,GPIO.OUT)

source_address = 'iotburneremail@gmail.com'
password = 'bexl uyik vidq wphh' # this is an app password to allow access
dest_address = 'theodoretsimiklis@gmail.com' ## if testing switch this with ur email

# source_address = 'iotburneremail@gmail.com'
# dest_address = 'theodoretsimiklis@gmail.com' ## if testing switch this with ur email
# password = 'bexl uyik vidq wphh' # this is an app password to allow access
imap_srv = 'imap.gmail.com'
imap_port = 993
emailSent = False
emailReceived = 0

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED, GPIO.OUT)

global current_light_intensity
current_light_intensity = "NaN"
currentLightIntensity = "NaN"
global lightIntensity

# This works as long as the arduino code is running (change broker)
broker = '192.168.169.126'
port = 1883
topicLight = "/IoTlab/status"
topicRFID = "/IoTlab/readTag"

global globalRFID
globalRFID = ""
RFID_Tag = "NaN"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

global humidityValue
humidityValue = 0

global temperatureValue
temperatureValue = 0



offcanvas = html.Div(
    [
        dbc.Offcanvas(
            html.Div(
                [                       
                    html.Div(style={'text-align': 'center'}, children=[
                        html.Img(src=app.get_asset_url('Avatar.png'), width='50%', height='50%', style={'border-radius': '50%'})
                    ]),
                    
                     html.Div(style={'text-align': 'center'}, children=[
                        html.H2('RFID Tag', style={'font-size': '24px'}),
                        dcc.Input(id='input-tag', type='text', placeholder='', disabled = True),
                    ]),
            
                    html.Div(style={'text-align': 'center'}, children=[
                        html.H2('Name', style={'font-size': '24px'}),
                        dcc.Input(id='input-name', type='text', placeholder='', disabled = True),
                    ]),

                    html.Div(style={'text-align': 'center'}, children=[
                        html.H2('TempThreshold', style={'font-size': '24px'}),
                        dcc.Input(id='input-temp', type='text', placeholder='', disabled = True),
                    ]),

                    html.Div(style={'text-align': 'center'}, children=[
                        html.H2('HumidityThreshold', style={'font-size': '24px'}),
                        dcc.Input(id='input-humid', type='text', placeholder='', disabled = True),
                    ]),

                    html.Div(style={'text-align': 'center'}, children=[
                        html.H2('LightThreshold', style={'font-size': '24px'}),
                        dcc.Input(id='input-light', type='text', placeholder='', disabled = True),
                    ]),
                    html.P(''),
                    html.Button('Submit', id='submit-button2', n_clicks=0),
                    html.P(id='submit-message2', style={'text-align': 'center'})
                    
                ], style={'text-align': 'center'}),
            id="offcanvas-backdrop",
            title="User information",
            is_open=False,
        ),
    ]
)
offcanvas2 = html.Div(
    [
        dbc.Offcanvas(
            html.Div(
                [                       
                    html.Div(style={'text-align': 'center'}, children=[
                        html.Img(src=app.get_asset_url('Avatar.png'), width='50%', height='50%', style={'border-radius': '50%'})
                    ]),
            
                    html.Div(style={'text-align': 'center'}, children=[
                        html.H2('Register'),
                        dcc.Input(id='input-box2', type='text', placeholder='Enter Name'),
                        dcc.Input(id='input-box', type='text', placeholder='RFID Tag', disabled = True),
                        html.P(''),
                        html.Button('Submit', id='submit-button', n_clicks=0),
                        html.P(id='submit-message')
                    ]),
                    
                ]),
            id="offcanvas-backdrop2",
            title="Register",
            is_open=False,
        ),
    ]
)

@app.callback(
    Output('submit-message2', 'children'),
    Input('submit-button2', 'n_clicks'),
    State('input-tag', 'value'),
    State('input-temp', 'value'),
    State('input-humid', 'value'),
    State('input-light', 'value')
)
def insert_values_into_database(n_clicks, tag_id, temp, humid, light):
    if n_clicks > 0:
        # Connect to the database
        conn = sqlite3.connect('smarthome.db')
        c = conn.cursor()

        # Insert the values into the database
        c.execute("UPDATE users SET TempThreshold = ?, HumidityThreshold = ?, LightThreshold = ? WHERE tag_id = ?", (temp, humid, light, tag_id))

        conn.commit()

        # Close the database connection
        conn.close()

        # Return a success message
        return "Values successfully inserted into the database."

    # If the button has not been clicked, return an empty string
    return ""
@app.callback(
    Output('submit-message', 'children'),
    Output('input-box', 'value'),
    Input('submit-button', 'n_clicks'),
    Input('interval-component', 'n_intervals'),
    State('input-box2', 'value'),
    State('input-box', 'value')
)
def update_output(n_clicks_submit, n_intervals, name, rfid_value):
    ctx = dash.callback_context

    if not ctx.triggered:
        return '', ''

    # Get the ID of the input that triggered the callback
    input_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Check which input triggered the callback
    if input_id == 'submit-button':
        # Check if the submit button has been clicked
        if n_clicks_submit > 0:
            # Simulate reading the RFID tag

            # Connect to the SQLite database
            conn = sqlite3.connect('smarthome.db')
            c = conn.cursor()
            if globalRFID and name:
                # Insert the values into the database
                c.execute("SELECT COUNT(*) FROM users WHERE tag_id=?", (globalRFID,))
                record_count = c.fetchone()[0]

                if record_count == 0 and name:
                # Close the database connection
                    c.execute("INSERT INTO users (name, tag_id) VALUES (?, ?)", (name, globalRFID))
                    conn.commit()
                
                    # Close the database connection
                    conn.close()

                    # Return the RFID tag value and the submit message
                    return "User inserted in the database", globalRFID
                
                else:
                    # Close the database connection
                    conn.close()

                    # Return an error message if the ID already exists
                    return ("RFID tag '{0}' already exists in the database. Please enter a different tag ID.".format(rfid_value), "")

    elif input_id == 'interval-component':
        # Update the RFID tag value from the global variable
        return '', globalRFID

    return '', ''


@app.callback(
    Output("offcanvas-backdrop", "is_open"),
    Input("open-offcanvas-backdrop", "n_clicks"),
    State("offcanvas-backdrop", "is_open"))

@app.callback(
    Output("offcanvas-backdrop2", "is_open"),
    Input("open-offcanvas-backdrop2", "n_clicks"),
    State("offcanvas-backdrop2", "is_open"))

def toggle_offcanvas(n_clicks, is_open):
    if n_clicks is not None:
        return not is_open
    return is_open





navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("User Account", href="#", id="open-offcanvas-backdrop", style={"border": "1px solid black", "marginLeft": "10px"})),
        dbc.NavItem(dbc.NavLink("Register", href="#", id="open-offcanvas-backdrop2", style={"border": "1px solid black", "marginLeft": "20px"})),
        dbc.NavItem(dbc.NavLink(offcanvas)),
        dbc.NavItem(dbc.NavLink(offcanvas2))
    ],
    brand="Home",
    brand_href="#",
    color="dark",
    dark=True,
    sticky="top"
)

image_src = app.get_asset_url('lightbulb_off.png')
ledBoxCard = dbc.Card(
    [
        dbc.CardHeader(html.H1(children='LED', style={'text-align': 'center'})),
        dbc.CardBody(
            [
                html.Div(
                        [
                            html.Div(
                                html.Img(id='led-image', src=image_src, style={'width': '50%', 'height': '50%'}),
                                className='text-center'
                            ),
                        ],
                        className='ledBox'
                    ),
                html.Div(
                    [
                        dbc.Input(
                            size="lg",
                            id='light-intensity-value',
                            className="mb-3",
                            value="The light intensity is " + str(currentLightIntensity),
                            readonly=True,
                            style={
                                'text-align': 'center',
                                'margin-top': '2%',
                                'margin-right': '5%',
                                'margin-left': '5%'
                            }
                        )
                    ],
                    className="md=12"
                )
            ]
        )
    ],
    className='grid-item',
    id='led-box'
)

humidTempCard = dbc.Card(
    [
        dbc.CardHeader(html.H1(children='Humidity and Temperature', style={'text-align': 'center'})),
        dbc.CardBody(
            [
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        id='humidity',
                                        children=[
                                            daq.Gauge(
                                                color={"gradient":True,"ranges":{"yellow":[0,30],"green":[30,50],"red":[50,100]}},
                                                id='humidity-gauge',
                                                label='Current Humidity',
                                                showCurrentValue=True,
                                                units="Percentage",
                                                value = humidityValue,
                                                max=100,
                                                min=0
                                            )
                                        ]
                                    ),
                                    md=6
                                ),
                                dbc.Col(
                                    html.Div(
                                        id='temperature',
                                        children=[
                                            daq.Thermometer(
                                                id='temperature-thermometer',
                                                label='Current temperature',
                                                value = temperatureValue,
                                                showCurrentValue=True,
                                                min=0,
                                                max=100
                                            )
                                        ] 
                                    ),
                                    md=6
                                )
                            ]
                        )
                    ],
                    className='humidTempBox'
                )
            ]
        )
    ],
    className='grid-item',
    id='humid-temp-box'
)

fanControlCard = dbc.Card(
    [
        dbc.CardHeader(html.H1(children='Fan Control', style={'text-align': 'center'})),
        dbc.CardBody(
            [
                html.Div(
                    children=[
                        html.Img(src=app.get_asset_url('fan1.png'), width='25%', height='25%')
                    ],
                    style={'text-align': 'center'}
                ),
                daq.ToggleSwitch(
                    size=100,
                    id='fan-toggle',
                    value=False,
                    label='Fan Status',
                    labelPosition='bottom',
                    color='#0C6E87',
                    style={
                        'margin-top': '3%',
                        'margin-left': '10%'
                    },
                    disabled=True
                )
            ]
        )
    ],
    className='grid-item',
    id='fan-box'
)

app.layout = html.Div(
    id="theme-div", 
    children=[ 
        navbar,
        html.H1(children='Welcome To Your SmartGrid', style={'text-align': 'center', 'margin-top': '3%'}),
        html.Div(
            className='grid-container', 
            style={'margin': '5% 7% 5% 7%'}, 
            children=[    
                dbc.Row([        
                    dbc.Col(ledBoxCard, md=4),        
                    dbc.Col(humidTempCard, md=4),
                    dbc.Col(fanControlCard, md=4),
                ], justify='center', align='center')
            ]
        ),
        dcc.Interval(id='interval-component', interval=5000, n_intervals=0)

])





def send_email(subject, body):
    smtp_srv = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = source_address
    smtp_pass = password

    msg = 'Subject: {}\n\n{}'.format(subject, body)
    server = smtplib.SMTP(smtp_srv, smtp_port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(smtp_user, smtp_pass)
    server.sendmail(smtp_user, dest_address, msg)
    server.quit()
    
def receive_email():
    mail = imaplib.IMAP4_SSL(imap_srv)
    mail.login(source_address, password)
    mail.select('inbox')
    status, data = mail.search(None, 
        'UNSEEN', 
        'HEADER SUBJECT "Temperature is High"',
        'HEADER FROM "' + dest_address +  '"')

    mail_ids = []
    for block in data:
        mail_ids += block.split()

    for i in mail_ids:
        status, data = mail.fetch(i, '(RFC822)')
        for response_part in data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])
                mail_from = message['from']
                mail_subject = message['subject']
                if message.is_multipart():
                    mail_content = ''
                    for part in message.get_payload():
                        if part.get_content_type() == 'text/plain':
                            mail_content += part.get_payload()
                else:
                    mail_content = message.get_payload().lower()
                print(mail_content)
                if 'yes' in mail_content:
                    return True
    return False

led_state = False

@app.callback(
    Output('led-image', 'src'),
    Input('interval-component', 'n_intervals')
)
def update_outputLight(n):
    global led_state
    if led_state:
        GPIO.output(LED, GPIO.HIGH)
        image_src = app.get_asset_url('lightbulb_on.png')
    else:
        GPIO.output(LED, GPIO.LOW)
        image_src = app.get_asset_url('lightbulb_off.png')
    return image_src


fan_state = False

@app.callback(Output('humidity-gauge', 'value'),
              Output('temperature-thermometer', 'value'),
              Input('interval-component', 'n_intervals'))
def read_DHT11_Data(n):
    global humidityValue
    global temperatureValue
    global emailSent
    global globalRFID
    global fan_state
    temperature_threshold = get_temp_threshold(globalRFID)  # retrieve temperature threshold from database
    dht.readDHT11()
    temperatureValue = dht.temperature
    humidityValue = dht.humidity
    if temperatureValue > temperature_threshold and not emailSent:
        send_email("Temperature is High", "Would you like to start the fan?")
        emailSent = True
    elif receive_email():
        fan_state = True
        time.sleep(10)
        fan_state = False
    elif temperatureValue < temperature_threshold:
        print("Temperature below threshold")
        emailSent = False
    print(f"Temperature: {temperatureValue}, Humidity: {humidityValue}")
    return  humidityValue, temperatureValue

    



@app.callback(Output('fan-toggle', 'value'),
              Input('interval-component', 'n_intervals')
)
def toggle_fan(n):
    global fan_state
    if fan_state:
        value = True
        GPIO.output(Motor1, GPIO.HIGH)
    else:
         GPIO.output(Motor1, GPIO.LOW)
         value = False
            
    return value

def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


@app.callback(
    Output('input-light', 'value'),
    Output('input-light', 'disabled'),
    Input('interval-component', 'n_intervals')
)
def update_light_intensity(n_intervals):
    conn = sqlite3.connect('smarthome.db')
    cursor = conn.cursor()

    # Get the LightThreshold value from the database for the current tag ID
    cursor.execute("SELECT LightThreshold FROM users WHERE tag_id = ?", (globalRFID,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0], False
    else:
        return " ", True


@app.callback(
    Output('input-humid', 'value'),
    Output('input-humid', 'disabled'),
    Input('interval-component', 'n_intervals')
)
def update_humidity_value(n_intervals):
    conn = sqlite3.connect('smarthome.db')
    cursor = conn.cursor()

    # Get the LightThreshold value from the database for the current tag ID
    cursor.execute("SELECT HumidityThreshold FROM users WHERE tag_id = ?", (globalRFID,))
    result = cursor.fetchone()

    conn.close()
    if result:
        return result[0], False
    else:
        return " ", True

@app.callback(
    Output('input-temp', 'value'),
    Output('input-temp', 'disabled'),
    Input('interval-component', 'n_intervals')
)
def update_temp_value(n_intervals):
    conn = sqlite3.connect('smarthome.db')
    cursor = conn.cursor()

    # Get the LightThreshold value from the database for the current tag ID
    cursor.execute("SELECT TempThreshold FROM users WHERE tag_id = ?", (globalRFID,))
    result = cursor.fetchone()

    conn.close()

    # If a value is found in the database, return it; otherwise, return the default value of 0
    if result:
        return result[0], False
    else:
        return " ", True

@app.callback(
    Output('input-name', 'value'),
    Input('interval-component', 'n_intervals')
)
def update_name(n_intervals):
    global nameFake
    conn = sqlite3.connect('smarthome.db')
    cursor = conn.cursor()

    # Get the LightThreshold value from the database for the current tag ID
    cursor.execute("SELECT name FROM users WHERE tag_id = ?", (globalRFID,))
    result = cursor.fetchone()

    conn.close()
    nameFake = result[0] if result else " "
    # If a value is found in the database, return it; otherwise, return the default value of 50
    return result[0] if result else " "

@app.callback(
    Output('input-tag', 'value'),
    Input('interval-component', 'n_intervals')
)
def update_ID(n_intervals):
    conn = sqlite3.connect('smarthome.db')
    cursor = conn.cursor()

    # Get the LightThreshold value from the database for the current tag ID
    cursor.execute("SELECT tag_id FROM users WHERE tag_id = ?", (globalRFID,))
    result = cursor.fetchone()

    conn.close()
    
    # If a value is found in the database, return it; otherwise, return the default value of 50
    return result[0] if result else " "

def check_database(tag_id):
    conn = sqlite3.connect('smarthome.db')
    cursor = conn.cursor()

    # Check if tag ID exists in the database
    cursor.execute("SELECT * FROM users WHERE tag_id = ?", (tag_id,))
    result = cursor.fetchone()
    # If tag ID exists, update the LightThreshold, TempThreshold, and HumidityThreshold values in the database
    if result is not None:
        
        # Fetch all columns from the updated row
        cursor.execute("SELECT * FROM users WHERE tag_id = ?", (tag_id,))
        row = cursor.fetchone()
        

        current_time = time.strftime('%H:%M:%S')
        send_email("User was Logged In" , "User: " + nameFake +" logged in at: " + current_time)

        # Return the LightThreshold, TempThreshold, and HumidityThreshold values
        return row[2], row[3], row[4]

    conn.close()

    # Return None if tag ID does not exist in the database
    return None




def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        global led_state, current_light_intensity, globalRFID
        if msg.topic == topicLight:
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            lightmsg = ""
            lightIntensity = 0
            lightmsg = int(msg.payload.decode())
            current_light_intensity = lightmsg
            light_threshold = get_light_threshold(globalRFID)
            if int(msg.payload.decode()) <= light_threshold:
                led_state = True
                time = datetime.now(pytz.timezone('America/New_York'))
                currtime = time.strftime("%H:%M")
                send_email("Light", "The Light is ON at " + currtime + ".")
                emailSent = True
            else:
                led_state = False
                emailSent = False
        elif msg.topic == topicRFID:
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            globalRFID = msg.payload.decode()
            check_database(globalRFID)

    client.subscribe(topicLight)
    client.subscribe(topicRFID)
    client.on_message = on_message
    return current_light_intensity


def get_light_threshold(tag_id):
    conn = sqlite3.connect('smarthome.db')
    cursor = conn.cursor()

    cursor.execute("SELECT LightThreshold FROM users WHERE tag_id = ?", (tag_id,))
    result = cursor.fetchone()

    conn.close()

    if result and result[0] is not None:
        return int(result[0])
    else:
        return 70

    
    
def get_temp_threshold(tag_id):
    conn = sqlite3.connect('smarthome.db')
    cursor = conn.cursor()

    cursor.execute("SELECT TempThreshold FROM users WHERE tag_id = ?", (tag_id,))
    result = cursor.fetchone()

    conn.close()

    if result and result[0] is not None:
        return int(result[0])
    else:
        return 70


@app.callback(Output('light-intensity-value', 'value'),
              Input('interval-component', 'n_intervals'))
def update_light_intensity(n):
    return 'The current light intensity is:' + str(current_light_intensity)

def main():

    client = connect_mqtt()
    subscribe(client)
    
    client.loop_start()
    app.run_server(debug=True, host='localhost', port=8080)

main()