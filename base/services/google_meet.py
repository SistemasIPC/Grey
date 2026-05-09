from googleapiclient.discovery import build

from google.oauth2.credentials import Credentials

import datetime


def crear_evento_meet(
    credentials,
    titulo,
    inicio,
    fin,
    asistentes
):

    service = build(
        'calendar',
        'v3',
        credentials=credentials
    )

    evento = {

        'summary': titulo,

        'start': {
            'dateTime': inicio.isoformat(),
            'timeZone': 'America/Bogota',
        },

        'end': {
            'dateTime': fin.isoformat(),
            'timeZone': 'America/Bogota',
        },

        'attendees': [
            {'email': correo}
            for correo in asistentes
        ],

        'conferenceData': {
            'createRequest': {
                'requestId': 'meet123'
            }
        },
    }

    evento_creado = service.events().insert(

        calendarId='primary',

        body=evento,

        conferenceDataVersion=1,

        sendUpdates='all'

    ).execute()

    meet_link = evento_creado[
        'hangoutLink'
    ]

    return {
        "event_id": evento_creado["id"],
        "meet_link": meet_link
    }