import flickrapi
# from lxml import etree
import urllib.request
import time
import random
# import re
import os
import argparse
import sys


##############
# parse args #
##############
def check_positive(value):
    fvalue = float(value)
    if fvalue < 0:
        raise argparse.ArgumentTypeError(f"{value} is not a valid positive float value")
    return fvalue


parser = argparse.ArgumentParser()


parser.add_argument(
    "--min-wait",
    default=1,
    type=check_positive,
    help="Specifies the minimum time in seconds that is waited before downloading the next image.",
)

parser.add_argument(
    "--max-wait",
    default=2,
    type=check_positive,
    help="Specifies the maximum time in seconds that is waited before downloading the next image.",
)

parser.add_argument(
    "--user-id",
    help="Specifies the user id of the account, from which the photos will be downloaded.",
)
parser.add_argument(
    "--api-key",
    help="Specifies the API key of the account, from which the photos will be downloaded.",
)

parser.add_argument(
    "--api-secret",
    help="Specifies the API secret of the account, from which the photos will be downloaded.",
)

args = parser.parse_args()


#################
# functionality #
#################
def sleep_random_time(min_time=1, max_time=5):
    # sleep from 1s to 5s
    duration = (random.random() * (max_time - min_time)) + min_time
    print(f"sleeping for {round(duration, 3)}s")
    time.sleep(duration)


def get_attribute_from_photo(photo, attribute):
    for photo_item in photo.items():
        if photo_item[0] == attribute:
            return photo_item[1]


def create_directory_if_not_exists(dir_path):
    os.makedirs(os.path.dirname(dir_path),
                exist_ok=True)


def build_dir_path(photoset_id, photo_id, prefix="downloaded-photos"):
    return os.path.join(prefix, photoset_id, photo_id)


def build_file_path(photoset_id, photo_id, image_src, prefix="downloaded-photos"):
    return os.path.join(prefix, photoset_id, photo_id) + image_src[-4:]


def download_image_from_url(
    photoset_id,
    photoset_name,
    photo_id,
    photo_name,
    url
):
    dir_path = build_dir_path(photoset_name, photo_name)
    file_path = build_file_path(photoset_name, photo_name, url)
    if os.path.isfile(file_path):
        print(f"[INFO]: file already exists, skipping {file_path}.")
    else:
        print(f"[INFO]: downloading image from: {url}")
        create_directory_if_not_exists(dir_path)
        with open(file_path, mode="wb") as image_file:
            image_file.write(urllib.request.urlopen(url).read())


def get_photoset_infos(all_sets):
    photosets = {}
    for photoset in all_sets:
        photoset_id = photoset.get("id")
        photosets[photoset_id] = {
            "name": photoset.find("title").text,
            "photos": set()
        }
        # print(photosets)
        for photo in flickr.walk_set(photoset_id):
            # print(photo.items())
            photosets[photoset_id]["photos"].add(
                (get_attribute_from_photo(photo, "id"),
                 get_attribute_from_photo(photo, "title")))
    return photosets


def download_photos(flickr, photosets):
    num_of_photos = sum([len(photoset["photos"])
                         for (photoset_id, photoset)
                         in photosets.items()])
    print(f"[INFO]: found {num_of_photos} photos.")

    for (photoset_id, photoset) in photosets.items():
        for (photo_id, photo_name) in photoset["photos"]:
            sizes_tree = flickr.photos.getSizes(photo_id=photo_id)
            original_url = sizes_tree.xpath("//size[@label='Original']/@source")[0]
            download_image_from_url(
                photoset_id,
                photoset["name"],
                photo_id,
                photo_name,
                original_url)
            sleep_random_time(min_time=args.min_wait, max_time=args.max_wait)


if __name__ == "__main__":
    try:
        user_id = args.user_id
        api_key = args.api_key
        api_secret = args.api_secret

        flickr = flickrapi.FlickrAPI(api_key, api_secret, format="etree")
        flickr.authenticate_via_browser(perms="read")
        sets = flickr.photosets.getList(user_id=user_id)
        all_sets = sets.find("photosets").findall("photoset")

        photosets = get_photoset_infos(all_sets)

        download_photos(flickr, photosets)
    except KeyboardInterrupt as exc:
        print("[INFO]: got keyboard interrupt, exiting ...")
        sys.exit(0)
