from Downloader import YTVideoDownloader


def main():
    dict = YTVideoDownloader().download(

        # https://www.youtube.com/watch?v=eKIr_g0q5Uc
        # https://www.youtube.com/watch?v=3NpjfRKOblg&list=OLAK5uy_nh1X4KzCgR37rgmHGTDx8u_R95S0vX4jA
        #  show_album_cover_on_mp3=True,
        #  album_cover_image="H:\\Downloads\\Video\\Thumbnails\\A Hat In Time - Seal The Deal.png"

        "https://www.youtube.com/watch?v=3NpjfRKOblg&list=OLAK5uy_nh1X4KzCgR37rgmHGTDx8u_R95S0vX4jA",
        "H:\\Downloads\\Video\\Mp4", "MP4")

    print(dict)


if __name__ == "__main__":
    main()
