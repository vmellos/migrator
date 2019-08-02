import itertools
import json
import os
import pdb
import webbrowser

import click
import requests

from flask import request
from rauth import OAuth2Service
import sqlalchemy.orm.exc as sq_exceptions

from migrator import app
from migrator.services.tokens import save_tokens, get_tokens
from migrator.services.interfaces import Playlist, ServiceAuth


class SpotifyAuth(ServiceAuth):
    SERVICE_CODE = 1

    def __init__(self):
        self.oauth = OAuth2Service(
            name='spotify',
            base_url='https://api.spotify.com/v1',
            client_id=os.environ['SPOTIFY_CLIENT_ID'],
            client_secret=os.environ['SPOTIFY_CLIENT_SECRET'],
            authorize_url='https://accounts.spotify.com/authorize',
            access_token_url='https://accounts.spotify.com/api/token'
        )

    def autorization_url(self):
        scopes = [
            'playlist-modify-public',
            'playlist-read-collaborative',
            'playlist-read-private',
            'playlist-modify-private'
        ]
        authorize_url = self.oauth.get_authorize_url(**{
            'response_type': 'code',
            'redirect_uri': 'http://localhost:5000/spotify/callback',
            'scope': ', '.join(scopes)
         })

        webbrowser.open(authorize_url)

        return self

    def _get_access_token(self, data):
        session = None
        try:
            session = self.oauth.get_auth_session(data=data, decoder=json.loads)
        except Exception as e:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': get_tokens(self.SERVICE_CODE).refresh_token
            }
            session = self.oauth.get_auth_session(data=data, decoder=json.loads)

        return session

    @property
    def session(self):
        session = None
        data = {
            'grant_type': 'authorization_code',
            'redirect_uri': 'http://localhost:5000/spotify/callback'
        }

        try:
            tokens = get_tokens(self.SERVICE_CODE)
            data.update({'code': tokens.code})
        except sq_exceptions.NoResultFound as e:
            self.autorization_url()

        if data.get('code'):
            session = self._get_access_token(data)
            save_tokens(self.SERVICE_CODE, session.access_token_response.json())

        return session


class SpotifyPlaylists(Playlist):
    def __init__(self):
        self.oauth = SpotifyAuth()

    def request(self, endpoint, page=0, limit=30):
        response = self.oauth.session.get(endpoint)

        if response.status_code != 200:
            raise Exception(response.text)

        return response.json()

    def copy(self, playlist):
        pass

    def get_tracks(self, tracks_url):
        click.echo('Buscando as musicas...')

        tracks = []
        response = self.request(f"v1/{'/'.join(tracks_url.split('/')[-3:])}")

        for track in response['items']:
            tracks.append({
                'name': track['track']['name'],
                'artists': list(
                    map(
                        lambda artists: artists['name'],
                        track['track']['artists']
                    )
                )
            })

        return tracks

    def get(self, name):
        click.echo('Procurando a playlist...')
        playlists = self.request('v1/me/playlists')

        for playlist in playlists['items']:
            if playlist['name'] == name:
                click.echo('Playlist encotrada!')
                tracks = self.get_tracks(playlist['tracks']['href'])

                return {'playlist': name, 'tracks': tracks}
        else:
            click.echo('Não foi possivel achar a playlist, verifique se o nome esta correto')
