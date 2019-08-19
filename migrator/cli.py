import pdb
import pprint
import click


from migrator.services.deezer import DeezerPlaylists
from migrator.services.spotify import SpotifyPlaylists
from migrator.services.youtube import YoutubeService


SERVICES = {
    'deezer': DeezerPlaylists,
    'spotify': SpotifyPlaylists,
    'youtube': YoutubeService
}

options = SERVICES.keys()


@click.group()
def cli():
    pass


def execute_copy(origin, destination, playlist_name):
    origin_service = origin()
    destination_service = destination()
    playlist = origin_service.get(playlist_name)
    if playlist:
        destination_service.copy(playlist)


@cli.command()
@click.option('--name', required=True)
@click.option('--to-service', type=click.Choice(options), required=True)
@click.option('--from-service', type=click.Choice(options), required=True)
def copy(from_service, to_service, name):

    if from_service == to_service:
        print("O serviço de origem não pode ser o mesmo serviço de destino")
        return

    origin_service = SERVICES.get(from_service)
    destination_service = SERVICES.get(to_service)

    execute_copy(origin_service, destination_service, name)


if __name__ == '__main__':
    cli()
