import yt_dlp

def get_playlist_info(playlist_url):
    youtube_dlp_options = {
        'extract_flat': True,
        'skip_unavailable_fragments': True,
        'quiet': True,
        'dump_single_json': True,
    }

    with yt_dlp.YoutubeDL(youtube_dlp_options) as yt_downloader:
        data = yt_downloader.extract_info(playlist_url, download=False)
        entries = data.get('entries', [])
        titles = sanitize_titles([entry['title'] for entry in entries if 'title' in entry and 'url' in entry])
        urls = [entry['url'] for entry in entries if 'title' in entry and 'url' in entry]
    return titles, urls

def sanitize_titles(titles):
    prohibited_chars = [':', '/', '\\', '//']
    sanitized_titles = []
    for title in titles:
        sanitized_title = ''.join(['_' if char in prohibited_chars else char for char in title])
        sanitized_titles.append(sanitized_title)
    return sanitized_titles
      
if __name__ == "__main__":
    playlist_url = input("Give the playlist URL: ")
    titles, urls = get_playlist_info(playlist_url)
        
    with open("titles.txt", "w", encoding="utf-8") as file:
        for title in titles:
            file.write(title + "\n")
        
    with open("links.txt", "w", encoding="utf-8") as file:
        for url in urls:
            file.write(url + "\n")