import argparse
import os
import requests
import re
import eyed3
from eyed3.id3.frames import ImageFrame

CUSTOM_HEADER = {
    'Host': 'api.spotifydown.com',
    'Referer': 'https://spotifydown.com/',
    'Origin': 'https://spotifydown.com',
}

def check_track_playlist(link):
    # if "/track/" in link:
    if re.search(r".*spotify\.com\/track\/", link):
        return "track"
    # elif "/playlist/" in link:
    elif re.search(r".*spotify\.com\/playlist\/", link):
        return "playlist"
    else:
        return None
        # print(f"{link} is not a valid Spotify track or playlist link")

def  get_track_info(link):
    track_id = link.split("/")[-1].split("?")[0]
    response = requests.get(f"https://api.spotifydown.com/download/{track_id}", headers=CUSTOM_HEADER)
    response = response.json()
    # print(response['success'])
    # print(f"Song: {response['metadata']['title']}, Artist: {response['metadata']['artists']}, Album: {response['metadata']['album']}")
    # print(response['link'])

    return response

def attach_cover_art(trackname, cover_art, outpath):
    print(outpath)
    audio_file = eyed3.load(os.path.join(outpath, f"{trackname}.mp3"))

    # https://stackoverflow.com/questions/38510694/how-to-add-album-art-to-mp3-file-using-python-3
    if (audio_file.tag is None):
        audio_file.initTag()

    audio_file.tag.images.set(ImageFrame.FRONT_COVER, cover_art.content, 'image/jpeg')
    audio_file.tag.save()

def save_audio(trackname, link, outpath):
    if os.path.exists(os.path.join(outpath, f"{trackname}.mp3")):
        print(f"{trackname} already exists in the directory. Skipping download!")
        return False
    
    filename = re.sub(r"[<>:\"/\\|?*]", "_", f"{trackname}.mp3")
    audio_response = requests.get(link)

    if audio_response.status_code == 200:
        with open(os.path.join(outpath, filename), "wb") as file:
            file.write(audio_response.content)
        return True

def resolve_path(outpath):
    if not os.path.exists(outpath):
        create_dir = input("Directory entered does not exist. Do you want to create it? (y/N): ")
        if create_dir.lower() == "y":
            os.mkdir(outpath)
        else:
            print("Exiting program")
            exit()


def get_playlist_info(link):
    playlist_id = link.split("/")[-1].split("?")[0]
    response = requests.get(f"https://api.spotifydown.com/metadata/playlist/{playlist_id}", headers=CUSTOM_HEADER)
    response = response.json()
    if response['success']:
        print(f"Playlist found, Name: {response['title']} by {response['artists']}")
    
    track_list = []
    response = requests.get(f"https://api.spotifydown.com/tracklist/playlist/{playlist_id}", headers=CUSTOM_HEADER)
    response = response.json()
    track_list.extend(response['trackList'])
    print(track_list)

    return track_list

def main():
    # Initialize parser
    parser = argparse.ArgumentParser(description="Program to download tracks from Spotify via CLI")

    # Add arguments
    parser.add_argument("-link", nargs="+", help="URL of the Spotify track")
    parser.add_argument("-outpath", nargs="?", default=os.getcwd(), help="Path to save the downloaded track")

    args = parser.parse_args()

    # print(args.link)

    resolve_path(args.outpath)

    for link in args.link:
        link_type = check_track_playlist(link)
        if link_type == "track":
            print("Track link identified")

            resp = get_track_info(link)
            trackname = resp['metadata']['title']
            # print(trackname)
            save_status = save_audio(trackname, resp['link'], args.outpath)
            # print("Save status: ", save_status)
            if save_status:
                cover_art = requests.get(resp['metadata']['cover'])
                # print("------", trackname)
                attach_cover_art(trackname, cover_art, args.outpath)

        elif link_type == "playlist":
            print("Playlist link identified")
            resp_track_list = get_playlist_info(link)
            for track in resp_track_list:
                trackname = track['title']
                resp = get_track_info(f"https://open.spotify.com/track/{track['id']}")
                save_status = save_audio(trackname, resp['link'], args.outpath)
                if save_status:
                    cover_art = requests.get(track['cover'])
                    attach_cover_art(trackname, cover_art, args.outpath)
        
        else:
            print(f"{link} is not a valid Spotify track or playlist link")
    
    print("Download complete")




    # https://open.spotify.com/track/0b4a1iklB8w8gsE38nzyEx?si=d5986255e2464129

main()