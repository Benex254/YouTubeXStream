from pytube import YouTube

yt = YouTube('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
stream = yt.streams.filter(file_extension="mp4",only_audio=True)

print(stream)
# # Change the extension to .mp4
# audio_stream = stream

# # Download the audio
# yt.streams.get_by_url(audio_stream).download()